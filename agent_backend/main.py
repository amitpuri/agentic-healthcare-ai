"""
Real AI Agent Backend Service
FastAPI backend that integrates AutoGen and CrewAI agents with LLM communication tracking
"""

from fastapi import FastAPI, Header, HTTPException, Depends, BackgroundTasks, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
import uuid
import httpx
from langchain_core.callbacks.base import BaseCallbackHandler

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'autogen_fhir_agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crewai_fhir_agent'))

from llm_communication_tracker import (
    LLMCommunicationTracker,
    AutoGenLLMWrapper,
    AgentFramework,
    LLMProvider
)
from fhir_client import FHIRClient, FHIRConfig
from service_auth import UNAUTHORIZED_DETAIL, UNAUTHORIZED_HEADERS, token_is_valid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def require_service_token(authorization: str = Header(None)):
    """Authenticate the caller against the shared internal service token."""
    if not token_is_valid(authorization):
        raise HTTPException(
            status_code=401,
            detail=UNAUTHORIZED_DETAIL,
            headers=UNAUTHORIZED_HEADERS,
        )


app = FastAPI(title="Real AI Agent Backend", version="1.0.0")
api_router = APIRouter(prefix="/api", dependencies=[Depends(require_service_token)])

RETRY_AFTER_SECONDS = 300


class LLMUpstreamUnavailable(Exception):
    """The upstream LLM provider refused the call with a 429 (no quota, or rate limited)."""

    def __init__(self, error_code: str, provider_message: str):
        super().__init__(provider_message)
        self.error_code = error_code
        self.provider_message = provider_message


def raise_if_upstream_unavailable(exc: Exception):
    """Re-raise a 429 from the LLM provider as an availability error.

    Quota exhaustion and rate limiting are availability conditions, not server
    faults: callers need a 503 they can back off on, not an opaque 500. Classification
    reuses the tracker's parser so the HTTP status always agrees with the error_breakdown
    reported by /api/communications/stats.
    """
    _, error_type, error_code = tracker.parse_openai_error(exc)
    if error_code != 429:
        return
    raise LLMUpstreamUnavailable(
        "llm_quota_exhausted" if error_type == "quota_exceeded" else "llm_rate_limited",
        str(exc),
    ) from exc


@app.exception_handler(LLMUpstreamUnavailable)
async def llm_upstream_unavailable_handler(request: Request, exc: LLMUpstreamUnavailable):
    logger.error(f"LLM upstream unavailable ({exc.error_code}): {exc.provider_message}")
    return JSONResponse(
        status_code=503,
        headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
        content={
            "error": exc.error_code,
            "message": (
                "The shared LLM provider rejected the request, so no agent assessment "
                "could be run. No clinical conclusion was produced."
            ),
            "provider_message": exc.provider_message,
            "retry_after": RETRY_AFTER_SECONDS,
            "service": "agent-backend",
        },
    )

# Add a logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code}")
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global tracker instance
tracker = LLMCommunicationTracker(webhook_url=os.getenv("WEBHOOK_URL"))

# Agent wrappers
autogen_wrapper = AutoGenLLMWrapper(tracker)

# Active scenarios storage
active_scenarios: Dict[str, Dict] = {}


def get_fhir_config() -> FHIRConfig:
    """FastAPI dependency to get FHIR configuration"""
    return FHIRConfig(
        base_url=os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir"),
        client_id=os.getenv("FHIR_CLIENT_ID", "default-client-id"),
        client_secret=os.getenv("FHIR_CLIENT_SECRET"),
    )


class AgentConfig(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.1
    track_communications: bool = True


class ScenarioConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    patient_id: str = Field(..., alias='patientId')
    patient_name: str = Field(..., alias='patientName')
    chief_complaint: Optional[str] = Field(None, alias='chiefComplaint')
    urgency_level: str = Field("routine", alias='urgencyLevel')
    additional_context: Optional[str] = Field(None, alias='additionalContext')


class AgentExecutionConfig(BaseModel):
    model: str
    temperature: float
    track_communications: bool


class TaskExecutionRequest(BaseModel):
    agent_id: str
    agent_name: str
    task: str
    patient_id: Optional[str] = None
    context: Optional[str] = None
    config: Dict[str, Any]


class ScenarioExecutionRequest(BaseModel):
    patient_id: str
    scenario_config: ScenarioConfig
    agent_config: AgentExecutionConfig


@app.get("/")
async def root():
    return {"message": "Real AI Agent Backend Service", "status": "active"}


# Unauthenticated: the container healthcheck probes this and it exposes no PHI.
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "tracker_active": len(tracker.active_sessions),
        "total_communications": len(tracker.communications),
        "frameworks_available": ["autogen", "crewai"]
    }


@api_router.get("/communications")
async def get_communications():
    """Get all LLM communications"""
    communications = []
    for comm in tracker.communications.values():
        comm_dict = {
            "id": comm.id,
            "agentId": comm.agent_id,
            "agentName": comm.agent_name,
            "framework": comm.framework.value,
            "provider": comm.provider.value,
            "model": comm.model,
            "sessionStart": comm.session_start.isoformat(),
            "sessionEnd": comm.session_end.isoformat() if comm.session_end else None,
            "patientId": comm.patient_id,
            "scenarioType": comm.scenario_type,
            "totalInputTokens": comm.total_input_tokens,
            "totalOutputTokens": comm.total_output_tokens,
            "totalTokens": comm.total_tokens,
            "costEstimate": comm.cost_estimate,
            "responseTimeMs": comm.response_time_ms,
            "finalResponse": comm.final_response,
            "confidenceScore": comm.confidence_score,
            "functionCallsMade": comm.function_calls_made,
            "toolsUsed": comm.tools_used,
            "errorMessage": comm.error_message,
            "messages": [
                {
                    "id": msg.id,
                    "timestamp": msg.timestamp.isoformat(),
                    "role": msg.role,
                    "content": msg.content,
                    "tokens": msg.tokens,
                    "functionCall": msg.function_call,
                    "toolCalls": msg.tool_calls
                }
                for msg in comm.messages
            ]
        }
        communications.append(comm_dict)
    
    return communications


@api_router.get("/communications/stats")
async def get_communication_stats():
    """Get communication statistics"""
    return tracker.get_communication_stats()


@api_router.get("/communications/{comm_id}")
async def get_communication(comm_id: str):
    """Get a specific communication by ID"""
    comm = tracker.get_communication(comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    
    return {
        "id": comm.id,
        "agentName": comm.agent_name,
        "framework": comm.framework.value,
        "model": comm.model,
        "sessionStart": comm.session_start.isoformat(),
        "sessionEnd": comm.session_end.isoformat() if comm.session_end else None,
        "totalTokens": comm.total_tokens,
        "costEstimate": comm.cost_estimate,
        "responseTimeMs": comm.response_time_ms,
        "finalResponse": comm.final_response,
        "messages": [
            {
                "id": msg.id,
                "timestamp": msg.timestamp.isoformat(),
                "role": msg.role,
                "content": msg.content,
                "tokens": msg.tokens
            }
            for msg in comm.messages
        ]
    }


@api_router.post("/autogen/comprehensive")
async def execute_autogen_comprehensive(request: ScenarioExecutionRequest):
    return await execute_autogen_scenario(request, "comprehensive_assessment")


@api_router.post("/autogen/emergency")
async def execute_autogen_emergency(request: ScenarioExecutionRequest):
    return await execute_autogen_scenario(request, "emergency_assessment")


@api_router.post("/autogen/medication_review")
async def execute_autogen_medication_review(request: ScenarioExecutionRequest):
    return await execute_autogen_scenario(request, "medication_reconciliation")


@api_router.post("/crewai/comprehensive")
async def execute_crewai_comprehensive(request: ScenarioExecutionRequest):
    return await execute_crewai_scenario(request, "comprehensive_assessment")


@api_router.post("/crewai/emergency")
async def execute_crewai_emergency(request: ScenarioExecutionRequest):
    return await execute_crewai_scenario(request, "emergency_triage")


@api_router.post("/crewai/medication_review")
async def execute_crewai_medication_review(request: ScenarioExecutionRequest):
    return await execute_crewai_scenario(request, "medication_review")


async def execute_autogen_scenario(
    request: ScenarioExecutionRequest,
    scenario_type: str,
):
    """Generic executor for AutoGen scenarios"""
    scenario_id = str(uuid.uuid4())
    start_time = datetime.now()
    fhir_config = get_fhir_config()
    logger.info(f"Executing AutoGen scenario '{scenario_type}' with ID: {scenario_id}")

    active_scenarios[scenario_id] = {
        "status": "running",
        "start_time": start_time.isoformat(),
        "framework": "autogen",
        "scenario_type": scenario_type,
        "patient_id": request.patient_id
    }

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    try:
        from autogen_fhir_agent.agents import HealthcareAutogenSystem

        # Create AutoGen system
        autogen_system = HealthcareAutogenSystem(api_key, fhir_config)
        
        # Get relevant agents and wrap them
        relevant_agents = autogen_system.get_agents_for_scenario(scenario_type)
        if not relevant_agents:
            raise HTTPException(status_code=400, detail=f"No agents configured for scenario: {scenario_type}")

        for agent_name, agent in relevant_agents.items():
            agent_id = f"{scenario_id}-{agent_name}"
            # Start tracking session for each agent
            tracker.start_communication(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_specialty="general",  # Placeholder, can be improved
                framework=AgentFramework.AUTOGEN,
                provider=LLMProvider.OPENAI,
                model=request.agent_config.model,
                patient_id=request.patient_id,
                scenario_type=scenario_type,
            )
            autogen_wrapper.wrap_agent(
                agent, 
                agent_id=agent_id,
                agent_name=agent_name, 
                specialty="general"  # Placeholder
            )

        task_description = (
            f"Execute the {scenario_type} for patient {request.patient_id}. "
            f"Chief complaint: {request.scenario_config.chief_complaint}. "
            f"Urgency: {request.scenario_config.urgency_level}. "
            f"Context: {request.scenario_config.additional_context}"
        )

        result = await autogen_system.execute_scenario(
            scenario_type=scenario_type,
            patient_id=request.patient_id,
            task_description=task_description
        )
        
        active_scenarios[scenario_id]["status"] = "completed"
        active_scenarios[scenario_id]["end_time"] = datetime.now().isoformat()
        active_scenarios[scenario_id]["result"] = result

        # End tracking sessions for all involved agents
        for agent_name in relevant_agents.keys():
            agent_id = f"{scenario_id}-{agent_name}"
            comm_id = tracker.active_sessions.get(agent_id)
            if comm_id:
                tracker.complete_communication(
                    comm_id, 
                    final_response=str(result),
                    response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                )

        return {"scenario_id": scenario_id, "status": "completed", "result": result}

    except ImportError:
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = "AutoGen module not available"
        raise HTTPException(status_code=500, detail="AutoGen module not available.")
    except HTTPException:
        active_scenarios[scenario_id]["status"] = "failed"
        raise
    except Exception as e:
        logger.error(f"Scenario execution failed: {e}")
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = str(e)
        # End tracking sessions with error
        if 'relevant_agents' in locals():
            for agent_name in relevant_agents.keys():
                agent_id = f"{scenario_id}-{agent_name}"
                comm_id = tracker.active_sessions.get(agent_id)
                if comm_id:
                    tracker.complete_communication(
                        comm_id,
                        final_response="",
                        response_time_ms=0,
                        error_message=str(e)
                    )
        raise_if_upstream_unavailable(e)
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {e}")


class CrewAITrackingCallback(BaseCallbackHandler):
    """Records the crew's LLM turns into the shared tracker.

    CrewAILLMWrapper patches ``llm._call``, which the pydantic ``ChatOpenAI`` chat model
    used here neither exposes nor allows assigning, so tracking goes through LangChain's
    callback interface instead.
    """

    def __init__(self, agent_id: str, agent_name: str, specialty: str, model: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.specialty = specialty
        self.model = model
        self._runs: Dict[str, Any] = {}
        # CrewAI swallows LLM exceptions inside its executor loop and still returns a
        # result string, so the endpoint has to inspect these to notice a dead provider.
        self.succeeded = 0
        self.upstream_error: Optional[LLMUpstreamUnavailable] = None

    def _start(self, run_id, prompt: str):
        comm_id = tracker.start_communication(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_specialty=self.specialty,
            framework=AgentFramework.CREWAI,
            provider=LLMProvider.OPENAI,
            model=self.model,
        )
        self._runs[str(run_id)] = (comm_id, time.time())
        tracker.add_message(comm_id=comm_id, role="user", content=prompt)

    def on_chat_model_start(self, serialized, messages, *, run_id=None, **kwargs):
        prompt = "\n".join(
            str(getattr(m, "content", m)) for batch in messages for m in batch
        )
        self._start(run_id, prompt)

    def on_llm_start(self, serialized, prompts, *, run_id=None, **kwargs):
        self._start(run_id, "\n".join(prompts))

    def on_llm_end(self, response, *, run_id=None, **kwargs):
        run = self._runs.pop(str(run_id), None)
        if not run:
            return
        comm_id, started = run
        text = "".join(
            gen.text for batch in response.generations for gen in batch
        )
        tracker.add_message(comm_id=comm_id, role="assistant", content=text)
        tracker.complete_communication(
            comm_id=comm_id,
            final_response=text,
            response_time_ms=int((time.time() - started) * 1000),
        )
        self.succeeded += 1

    def on_llm_error(self, error, *, run_id=None, **kwargs):
        run = self._runs.pop(str(run_id), None)
        if not run:
            return
        comm_id, started = run
        error_message, error_type, error_code = tracker.parse_openai_error(error)
        tracker.complete_communication(
            comm_id=comm_id,
            final_response="",
            response_time_ms=int((time.time() - started) * 1000),
            error_message=error_message,
            error_type=error_type,
            error_code=error_code,
        )
        if error_code == 429:
            self.upstream_error = LLMUpstreamUnavailable(
                "llm_quota_exhausted" if error_type == "quota_exceeded" else "llm_rate_limited",
                error_message,
            )


def build_crewai_crew(manager, scenario_type: str, request: ScenarioExecutionRequest):
    """Map an agent-backend scenario type onto HealthcareAgentManager's crew factories."""
    if scenario_type == "comprehensive_assessment":
        return manager.create_patient_assessment_crew(request.patient_id)
    if scenario_type == "emergency_triage":
        return manager.create_emergency_assessment_crew(
            request.patient_id,
            request.scenario_config.chief_complaint or "Emergency assessment",
        )
    if scenario_type == "medication_review":
        return manager.create_medication_reconciliation_crew(request.patient_id)
    raise HTTPException(
        status_code=400, detail=f"No CrewAI crew configured for scenario: {scenario_type}"
    )


async def execute_crewai_scenario(
    request: ScenarioExecutionRequest,
    scenario_type: str,
):
    """Generic executor for CrewAI scenarios"""
    scenario_id = str(uuid.uuid4())
    start_time = datetime.now()
    fhir_config = get_fhir_config()
    logger.info(f"Executing CrewAI scenario '{scenario_type}' with ID: {scenario_id}")

    active_scenarios[scenario_id] = {
        "status": "running",
        "start_time": start_time.isoformat(),
        "framework": "crewai",
        "scenario_type": scenario_type,
        "patient_id": request.patient_id
    }

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")

    try:
        from crewai_fhir_agent.agents import HealthcareAgentManager
        
        # Initialize CrewAI system
        crewai_manager = HealthcareAgentManager(api_key, fhir_config)
        
        task_description = (
            f"Execute the {scenario_type} for patient {request.patient_id}. "
            f"Chief complaint: {request.scenario_config.chief_complaint}. "
            f"Urgency: {request.scenario_config.urgency_level}. "
            f"Context: {request.scenario_config.additional_context}"
        )

        crew_executor = build_crewai_crew(crewai_manager, scenario_type, request)

        # Every agent in the crew shares the manager's single ChatOpenAI instance, so
        # attaching once here covers the whole crew.
        crew_id = f"{scenario_id}-crew"
        tracking = CrewAITrackingCallback(
            agent_id=crew_id,
            agent_name=f"{scenario_type}_crew",
            specialty="multi_disciplinary",
            model=request.agent_config.model,
        )
        crewai_manager.llm.callbacks = [tracking]

        result = await asyncio.to_thread(crew_executor.kickoff)

        # A crew whose every LLM call was refused still returns a placebo result string.
        # Surface that as unavailability rather than a completed assessment.
        if tracking.upstream_error and tracking.succeeded == 0:
            raise tracking.upstream_error

        active_scenarios[scenario_id]["status"] = "completed"
        active_scenarios[scenario_id]["end_time"] = datetime.now().isoformat()
        active_scenarios[scenario_id]["result"] = str(result)

        return {"scenario_id": scenario_id, "status": "completed", "result": str(result)}

    except ImportError:
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = "CrewAI module not available"
        raise HTTPException(status_code=500, detail="CrewAI module not available.")
    except (HTTPException, LLMUpstreamUnavailable):
        active_scenarios[scenario_id]["status"] = "failed"
        raise
    except Exception as e:
        logger.error(f"Scenario execution failed: {e}")
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = str(e)
        raise_if_upstream_unavailable(e)
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {e}")


@api_router.get("/scenarios")
async def get_scenarios():
    """Get all scenarios"""
    return list(active_scenarios.values())


@api_router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario"""
    if scenario_id not in active_scenarios:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return active_scenarios[scenario_id]


@api_router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str):
    """Delete a scenario"""
    if scenario_id not in active_scenarios:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    del active_scenarios[scenario_id]
    return {"message": "Scenario deleted successfully"}


@api_router.get("/export/communications")
async def export_communications():
    """Export all communications data"""
    return {"data": tracker.export_communications()}

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 