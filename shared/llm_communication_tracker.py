"""
LLM Communication Tracker
Monitors and tracks real-time LLM communications for healthcare AI agents
Supports both AutoGen and CrewAI frameworks
"""

import json
import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class CommunicationType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    STREAMING = "streaming"
    FUNCTION_CALL = "function_call"
    TOOL_USE = "tool_use"


class AgentFramework(Enum):
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    CUSTOM = "custom"


@dataclass
class LLMMessage:
    """Represents a single message in LLM communication"""
    id: str
    timestamp: datetime
    role: str  # system, user, assistant, function
    content: str
    tokens: Optional[int] = None
    function_call: Optional[Dict] = None
    tool_calls: Optional[List[Dict]] = None


@dataclass
class LLMCommunication:
    """Represents a complete LLM communication session"""
    id: str
    agent_id: str
    agent_name: str
    agent_specialty: str
    framework: AgentFramework
    provider: LLMProvider
    model: str
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    scenario_type: str = "assessment"  # assessment, emergency, medication_review, etc.
    
    # Message exchange
    messages: List[LLMMessage] = None
    system_prompt: Optional[str] = None
    
    # Metrics
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    response_time_ms: int = 0
    
    # Results
    final_response: Optional[str] = None
    confidence_score: Optional[float] = None
    function_calls_made: List[str] = None
    tools_used: List[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None  # quota_exceeded, auth_failed, rate_limit, invalid_key, etc.
    error_code: Optional[int] = None  # HTTP status code
    retry_count: int = 0
    
    def __post_init__(self):
        if self.session_start is None:
            self.session_start = datetime.now()
        if self.messages is None:
            self.messages = []
        if self.function_calls_made is None:
            self.function_calls_made = []
        if self.tools_used is None:
            self.tools_used = []


class LLMCommunicationTracker:
    """Tracks and manages LLM communications across different AI frameworks"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.communications: Dict[str, LLMCommunication] = {}
        self.active_sessions: Dict[str, str] = {}  # agent_id -> communication_id
        self.webhook_url = webhook_url
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._lock = threading.Lock()
        
        # Pricing per 1k tokens (approximate)
        self.pricing = {
            LLMProvider.OPENAI: {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
            }
        }
    
    def start_communication(
        self,
        agent_id: str,
        agent_name: str,
        agent_specialty: str,
        framework: AgentFramework,
        provider: LLMProvider,
        model: str,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        scenario_type: str = "assessment",
        system_prompt: Optional[str] = None
    ) -> str:
        """Start tracking a new LLM communication session"""
        
        comm_id = f"comm_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        communication = LLMCommunication(
            id=comm_id,
            agent_id=agent_id,
            agent_name=agent_name,
            agent_specialty=agent_specialty,
            framework=framework,
            provider=provider,
            model=model,
            patient_id=patient_id,
            patient_name=patient_name,
            scenario_type=scenario_type,
            system_prompt=system_prompt
        )
        
        with self._lock:
            self.communications[comm_id] = communication
            self.active_sessions[agent_id] = comm_id
        
        logger.info(f"Started LLM communication tracking: {comm_id} for agent {agent_name}")
        return comm_id
    
    def add_message(
        self,
        comm_id: str,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        function_call: Optional[Dict] = None,
        tool_calls: Optional[List[Dict]] = None
    ) -> str:
        """Add a message to the communication log"""
        
        message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        message = LLMMessage(
            id=message_id,
            timestamp=datetime.now(),
            role=role,
            content=content,
            tokens=tokens,
            function_call=function_call,
            tool_calls=tool_calls
        )
        
        with self._lock:
            if comm_id in self.communications:
                self.communications[comm_id].messages.append(message)
                
                # Update token counts
                if tokens:
                    if role == "user" or role == "system":
                        self.communications[comm_id].total_input_tokens += tokens
                    elif role == "assistant":
                        self.communications[comm_id].total_output_tokens += tokens
                    
                    self.communications[comm_id].total_tokens = (
                        self.communications[comm_id].total_input_tokens +
                        self.communications[comm_id].total_output_tokens
                    )
                
                # Track function calls and tools
                if function_call:
                    self.communications[comm_id].function_calls_made.append(function_call.get("name", "unknown"))
                
                if tool_calls:
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("function", {}).get("name", "unknown")
                        self.communications[comm_id].tools_used.append(tool_name)
        
        return message_id
    
    def complete_communication(
        self,
        comm_id: str,
        final_response: str,
        response_time_ms: int,
        confidence_score: Optional[float] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        error_code: Optional[int] = None,
        retry_count: int = 0
    ):
        """Complete and finalize a communication session"""
        
        with self._lock:
            if comm_id not in self.communications:
                return  # Communication already deleted or never existed

            comm = self.communications[comm_id]

            # If no messages were ever added, it was a phantom run. Delete it.
            if not comm.messages:
                del self.communications[comm_id]
                logger.info(f"Deleted empty LLM communication record: {comm_id}")
                return

            comm.session_end = datetime.now()
            comm.final_response = final_response
            comm.response_time_ms = response_time_ms
            comm.confidence_score = confidence_score
            comm.error_message = error_message
            comm.error_type = error_type
            comm.error_code = error_code
            comm.retry_count = retry_count
            
            # Calculate cost estimate
            comm.cost_estimate = self._calculate_cost(comm)
            
            # Remove from active sessions
            if comm.agent_id in self.active_sessions:
                del self.active_sessions[comm.agent_id]
            
            # Send webhook notification if configured
            if self.webhook_url:
                self.executor.submit(self._send_webhook_notification, comm)
            
            logger.info(f"Completed LLM communication: {comm_id}")
    
    def get_communication(self, comm_id: str) -> Optional[LLMCommunication]:
        """Retrieve a specific communication by ID"""
        return self.communications.get(comm_id)
    
    def get_agent_communications(self, agent_id: str) -> List[LLMCommunication]:
        """Get all communications for a specific agent"""
        return [comm for comm in self.communications.values() if comm.agent_id == agent_id]
    
    def get_patient_communications(self, patient_id: str) -> List[LLMCommunication]:
        """Get all communications for a specific patient"""
        return [comm for comm in self.communications.values() if comm.patient_id == patient_id]
    
    def get_recent_communications(self, limit: int = 10) -> List[LLMCommunication]:
        """Get most recent communications"""
        sorted_comms = sorted(
            self.communications.values(),
            key=lambda x: x.session_start,
            reverse=True
        )
        return sorted_comms[:limit]
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get overall communication statistics"""
        comms = list(self.communications.values())
        completed_comms = [c for c in comms if c.session_end is not None]
        
        if not completed_comms:
            return {"total": 0, "completed": 0}
        
        total_tokens = sum(c.total_tokens for c in completed_comms)
        total_cost = sum(c.cost_estimate for c in completed_comms)
        avg_response_time = sum(c.response_time_ms for c in completed_comms) / len(completed_comms)
        
        framework_stats = {}
        for framework in AgentFramework:
            framework_comms = [c for c in completed_comms if c.framework == framework]
            framework_stats[framework.value] = {
                "count": len(framework_comms),
                "tokens": sum(c.total_tokens for c in framework_comms),
                "cost": sum(c.cost_estimate for c in framework_comms)
            }
        
        # Error statistics
        error_stats = {}
        error_comms = [c for c in completed_comms if c.error_message]
        for error_comm in error_comms:
            error_type = error_comm.error_type or "unknown"
            if error_type not in error_stats:
                error_stats[error_type] = {"count": 0, "latest_error": None}
            error_stats[error_type]["count"] += 1
            error_stats[error_type]["latest_error"] = {
                "message": error_comm.error_message,
                "code": error_comm.error_code,
                "timestamp": error_comm.session_start.isoformat(),
                "agent": error_comm.agent_name
            }

        return {
            "total": len(comms),
            "completed": len(completed_comms),
            "active": len(self.active_sessions),
            "errors": len(error_comms),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "average_response_time_ms": int(avg_response_time),
            "by_framework": framework_stats,
            "error_breakdown": error_stats
        }
    
    def export_communications(self, format: str = "json") -> str:
        """Export all communications data"""
        if format == "json":
            # Convert dataclasses to dict for JSON serialization
            export_data = []
            for comm in self.communications.values():
                comm_dict = asdict(comm)
                # Convert datetime objects to ISO strings
                comm_dict["session_start"] = comm.session_start.isoformat()
                if comm.session_end:
                    comm_dict["session_end"] = comm.session_end.isoformat()
                
                # Convert message timestamps
                for msg in comm_dict["messages"]:
                    msg["timestamp"] = msg["timestamp"].isoformat() if isinstance(msg["timestamp"], datetime) else msg["timestamp"]
                
                export_data.append(comm_dict)
            
            return json.dumps(export_data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _calculate_cost(self, comm: LLMCommunication) -> float:
        """Calculate estimated cost for a communication"""
        if comm.provider not in self.pricing:
            return 0.0
        
        model_pricing = self.pricing[comm.provider].get(comm.model)
        if not model_pricing:
            return 0.0
        
        input_cost = (comm.total_input_tokens / 1000) * model_pricing["input"]
        output_cost = (comm.total_output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost
    
    def _send_webhook_notification(self, comm: LLMCommunication):
        """Send webhook notification about completed communication"""
        try:
            payload = {
                "event": "communication_completed",
                "communication_id": comm.id,
                "agent_name": comm.agent_name,
                "framework": comm.framework.value,
                "duration_seconds": (comm.session_end - comm.session_start).total_seconds() if comm.session_end else 0,
                "total_tokens": comm.total_tokens,
                "cost_estimate": comm.cost_estimate,
                "patient_id": comm.patient_id,
                "scenario_type": comm.scenario_type
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook notification sent for communication {comm.id}")
            else:
                logger.warning(f"Webhook notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
    
    def parse_openai_error(self, exception) -> tuple:
        """Parse OpenAI exception and extract error details"""
        error_message = str(exception)
        error_type = "unknown_error"
        error_code = None
        
        # Check for specific OpenAI error types
        if hasattr(exception, 'status_code'):
            error_code = exception.status_code
        
        if "insufficient_quota" in error_message.lower() or "quota" in error_message.lower():
            error_type = "quota_exceeded"
            error_code = 429
        elif "rate limit" in error_message.lower() or "429" in error_message:
            error_type = "rate_limit"
            error_code = 429
        elif "invalid api key" in error_message.lower() or "unauthorized" in error_message.lower() or "401" in error_message:
            error_type = "auth_failed"
            error_code = 401
        elif "api key specified is not a valid openai format" in error_message.lower():
            error_type = "invalid_key_format"
            error_code = 400
        elif "400" in error_message:
            error_type = "bad_request"
            error_code = 400
        elif "500" in error_message:
            error_type = "server_error"
            error_code = 500
        
        return error_message, error_type, error_code
    
    def get_quota_exceeded_details(self) -> Dict[str, Any]:
        """Get detailed information about quota exceeded errors"""
        quota_errors = [
            comm for comm in self.communications.values() 
            if comm.error_type == "quota_exceeded"
        ]
        
        if not quota_errors:
            return {"has_quota_errors": False}
        
        latest_quota_error = max(quota_errors, key=lambda x: x.session_start)
        
        return {
            "has_quota_errors": True,
            "total_quota_errors": len(quota_errors),
            "latest_quota_error": {
                "timestamp": latest_quota_error.session_start.isoformat(),
                "agent_name": latest_quota_error.agent_name,
                "error_message": latest_quota_error.error_message,
                "patient_id": latest_quota_error.patient_id,
                "scenario_type": latest_quota_error.scenario_type
            },
            "affected_agents": list(set(comm.agent_name for comm in quota_errors)),
            "recommendation": "Please check your OpenAI account billing and usage limits at https://platform.openai.com/account/billing"
        }


class AutoGenLLMWrapper:
    """Wraps AutoGen agents for comprehensive communication tracking"""
    
    def __init__(self, tracker: LLMCommunicationTracker):
        self.tracker = tracker

    def wrap_agent(self, agent, agent_id: str, agent_name: str, specialty: str):
        """Wraps an AutoGen agent's generate_reply method for tracking"""
        original_generate_reply = agent.generate_reply

        def tracked_generate_reply(messages: Optional[List[Dict]] = None, sender: "Agent" = None, **kwargs):
            logger.info(f"--- ENTERING AutoGenLLMWrapper.tracked_generate_reply for agent: {agent_name} ---")
            # If messages are not provided, try to get them from the sender's chat history
            if messages is None:
                if sender is not None and hasattr(sender, 'chat_messages') and agent in sender.chat_messages:
                    messages = sender.chat_messages[agent]
                else:
                    messages = []
            
            # Determine model from llm_config
            model = "unknown"
            if agent.llm_config and agent.llm_config.get("config_list"):
                model = agent.llm_config["config_list"][0].get("model", "unknown")

            # Start tracking
            comm_id = self.tracker.start_communication(
                agent_id=agent_id,
                agent_name=agent_name,
                agent_specialty=specialty,
                framework=AgentFramework.AUTOGEN,
                provider=LLMProvider.OPENAI,  # Assuming OpenAI
                model=model,
                system_prompt=agent.system_message
            )

            # Log existing messages
            if messages:
                print("--- Messages sent to OpenAI ---")
                print(json.dumps(messages, indent=2))
                for msg in messages:
                    self.tracker.add_message(
                        comm_id, 
                        role=msg.get("role"), 
                        content=str(msg.get("content"))
                    )

            start_time = time.time()
            
            try:
                # Call original method
                reply = original_generate_reply(messages=messages, sender=sender, **kwargs)
                
                response_time_ms = int((time.time() - start_time) * 1000)

                # Log agent's reply
                response_content = ""
                if isinstance(reply, str):
                    response_content = reply
                elif isinstance(reply, dict) and reply.get("content"):
                    response_content = str(reply["content"])

                self.tracker.add_message(
                    comm_id,
                    role="assistant",
                    content=response_content
                )

                self.tracker.complete_communication(
                    comm_id,
                    final_response=response_content,
                    response_time_ms=response_time_ms
                )

                return reply

            except Exception as e:
                # Log the error and complete the communication with an error state
                error_type, error_message, error_code = self.tracker.parse_openai_error(e)
                logger.error(f"AutoGen LLM communication failed for agent {agent_name}: {error_type} ({error_code}) - {error_message}")
                
                # Ensure we have a final response value, even if it's just the error
                final_response_on_error = f"Error: {error_message}"

                self.tracker.complete_communication(
                    comm_id,
                    final_response=final_response_on_error,
                    response_time_ms=int((time.time() - start_time) * 1000),
                    error_message=error_message,
                    error_type=error_type,
                    error_code=error_code,
                    retry_count=getattr(e, "retry_count", 0)
                )
                raise e

        agent.generate_reply = tracked_generate_reply
        return agent

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (simple version)"""
        return max(1, len(text) // 4)


class CrewAILLMWrapper:
    """Wrapper for CrewAI agents to track LLM communications"""
    
    def __init__(self, tracker: LLMCommunicationTracker):
        self.tracker = tracker
    
    def wrap_agent_llm(self, agent, agent_id: str, agent_name: str, specialty: str):
        """Wrap a CrewAI agent's LLM to track communications"""
        if hasattr(agent, 'llm') and agent.llm:
            original_call = agent.llm._call if hasattr(agent.llm, '_call') else agent.llm.__call__
            
            def tracked_call(prompt, **kwargs):
                # Start tracking
                comm_id = self.tracker.start_communication(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    agent_specialty=specialty,
                    framework=AgentFramework.CREWAI,
                    provider=LLMProvider.OPENAI,  # Assuming OpenAI
                    model=getattr(agent.llm, 'model_name', 'gpt-4')
                )
                
                start_time = time.time()
                
                try:
                    # Log input
                    self.tracker.add_message(
                        comm_id=comm_id,
                        role="user",
                        content=prompt,
                        tokens=self._estimate_tokens(prompt)
                    )
                    
                    # Call original method
                    result = original_call(prompt, **kwargs)
                    
                    # Log response
                    response_content = str(result)
                    self.tracker.add_message(
                        comm_id=comm_id,
                        role="assistant",
                        content=response_content,
                        tokens=self._estimate_tokens(response_content)
                    )
                    
                    # Complete tracking
                    response_time = int((time.time() - start_time) * 1000)
                    self.tracker.complete_communication(
                        comm_id=comm_id,
                        final_response=response_content,
                        response_time_ms=response_time
                    )
                    
                    return result
                    
                except Exception as e:
                    # Complete with error
                    response_time = int((time.time() - start_time) * 1000)
                    error_message, error_type, error_code = self.tracker.parse_openai_error(e)
                    
                    logger.error(f"CrewAI LLM communication failed: {error_type} ({error_code}) - {error_message}")
                    
                    self.tracker.complete_communication(
                        comm_id=comm_id,
                        final_response="",
                        response_time_ms=response_time,
                        error_message=error_message,
                        error_type=error_type,
                        error_code=error_code
                    )
                    raise
            
            # Replace the method
            if hasattr(agent.llm, '_call'):
                agent.llm._call = tracked_call
            else:
                agent.llm.__call__ = tracked_call
        
        return agent
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)"""
        return max(1, len(text) // 4)


# Global tracker instance
global_llm_tracker = LLMCommunicationTracker()


def get_tracker() -> LLMCommunicationTracker:
    """Get the global LLM communication tracker instance"""
    return global_llm_tracker


def reset_tracker():
    """Reset the global tracker (useful for testing)"""
    global global_llm_tracker
    global_llm_tracker = LLMCommunicationTracker() 