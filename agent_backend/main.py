"""
Real AI Agent Backend Service
FastAPI backend that integrates AutoGen and CrewAI agents with LLM communication tracking
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
import uuid
import httpx

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'autogen_fhir_agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'crewai_fhir_agent'))

from llm_communication_tracker import (
    LLMCommunicationTracker, 
    AutoGenLLMWrapper, 
    CrewAILLMWrapper,
    AgentFramework,
    LLMProvider
)
from fhir_client import FHIRClient, FHIRConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Real AI Agent Backend", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Add a logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
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
crewai_wrapper = CrewAILLMWrapper(tracker)

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


@api_router.get("/health")
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
    fhir_config: FHIRConfig = Depends(get_fhir_config)
):
    """Generic executor for AutoGen scenarios"""
    scenario_id = str(uuid.uuid4())
    logger.info(f"Executing AutoGen scenario '{scenario_type}' with ID: {scenario_id}")
    
    active_scenarios[scenario_id] = {
        "status": "running",
        "start_time": datetime.now().isoformat(),
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
                    response_time_ms=int((datetime.now() - active_scenarios[scenario_id]["start_time"]).total_seconds() * 1000)
                )

        return {"scenario_id": scenario_id, "status": "completed", "result": result}

    except ImportError:
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = "AutoGen module not available"
        raise HTTPException(status_code=500, detail="AutoGen module not available.")
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
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {e}")


async def execute_crewai_scenario(
    request: ScenarioExecutionRequest, 
    scenario_type: str,
    fhir_config: FHIRConfig = Depends(get_fhir_config)
):
    """Generic executor for CrewAI scenarios"""
    scenario_id = str(uuid.uuid4())
    logger.info(f"Executing CrewAI scenario '{scenario_type}' with ID: {scenario_id}")

    active_scenarios[scenario_id] = {
        "status": "running",
        "start_time": datetime.now().isoformat(),
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

        # The agent that will be used for tracking is the one that executes the task
        crew_executor = crewai_manager.get_crew_for_scenario(scenario_type, task_description)
        
        # Start tracking session for the crew
        crew_id = f"{scenario_id}-crew"
        tracker.start_communication(
            agent_id=crew_id,
            agent_name=f"{scenario_type}_crew",
            agent_specialty="multi_disciplinary",  # Placeholder for crew
            framework=AgentFramework.CREWAI,
            provider=LLMProvider.OPENAI,
            patient_id=request.patient_id,
            scenario_type=scenario_type,
        )

        # Wrap the LLM for the crew
        crewai_wrapper.wrap_llm(
            llm=crew_executor.llm,
            agent_id=crew_id,
            agent_name=f"{scenario_type}_crew"
        )

        result = crew_executor.kickoff()
        
        active_scenarios[scenario_id]["status"] = "completed"
        active_scenarios[scenario_id]["end_time"] = datetime.now().isoformat()
        active_scenarios[scenario_id]["result"] = result
        
        # End tracking session
        comm_id = tracker.active_sessions.get(crew_id)
        if comm_id:
            tracker.complete_communication(
                comm_id,
                final_response=str(result),
                response_time_ms=int((datetime.now() - active_scenarios[scenario_id]["start_time"]).total_seconds() * 1000)
            )
        
        return {"scenario_id": scenario_id, "status": "completed", "result": result}
        
    except ImportError:
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = "CrewAI module not available"
        raise HTTPException(status_code=500, detail="CrewAI module not available.")
    except Exception as e:
        logger.error(f"Scenario execution failed: {e}")
        active_scenarios[scenario_id]["status"] = "failed"
        active_scenarios[scenario_id]["error"] = str(e)
        if 'crew_id' in locals():
            comm_id = tracker.active_sessions.get(crew_id)
            if comm_id:
                tracker.complete_communication(
                    comm_id,
                    final_response="",
                    response_time_ms=0,
                    error_message=str(e)
                )
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