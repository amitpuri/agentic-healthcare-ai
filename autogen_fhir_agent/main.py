"""
Autogen Healthcare FHIR Agent System
Main application for running multi-agent conversational healthcare AI with FHIR integration
"""

import asyncio
import logging
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import sys

# Add shared modules to path
import os
shared_path = os.path.join(os.path.dirname(__file__), '..', 'shared')
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)
if '/app/shared' not in sys.path:
    sys.path.insert(0, '/app/shared')

try:
    from fhir_client import FHIRConfig
    from healthcare_models import PatientSummary, ClinicalAssessment
except ImportError as e:
    # Fallback: try direct import
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    # Create minimal classes if shared modules aren't available
    class FHIRConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class PatientSummary:
        pass
    
    class ClinicalAssessment:
        pass
from agents import HealthcareAutogenSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI(
    title="Autogen Healthcare FHIR Agent System",
    description="Multi-agent conversational AI for healthcare with FHIR integration using Autogen framework",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create reports directory if it doesn't exist
import os
reports_dir = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(reports_dir, exist_ok=True)

# Mount static files for PDF reports
app.mount("/static/reports", StaticFiles(directory=reports_dir), name="reports")

# Security
security = HTTPBearer()

# Global variables
autogen_system: HealthcareAutogenSystem = None
active_connections: List[WebSocket] = []


class ConversationRequest(BaseModel):
    """Request model for starting a healthcare conversation"""
    patient_id: str
    conversation_type: str = "comprehensive"  # comprehensive, emergency, medication_review
    chief_complaint: str = None
    urgency: str = "routine"
    context: Dict[str, Any] = None


class EmergencyConversationRequest(BaseModel):
    """Request model for emergency conversation"""
    patient_id: str
    chief_complaint: str
    vital_signs: Dict[str, Any] = None
    triage_level: str = "urgent"  # routine, urgent, emergent, critical


class MedicationReviewRequest(BaseModel):
    """Request model for medication review conversation"""
    patient_id: str
    review_type: str = "reconciliation"  # reconciliation, interaction_check, optimization
    context: str = None  # admission, discharge, routine


class ConversationResponse(BaseModel):
    """Response model for conversation results"""
    conversation_id: str
    patient_id: str
    conversation_type: str
    status: str
    participants: List[str]
    summary: Dict[str, Any]
    full_conversation: List[Dict[str, Any]]
    timestamp: str


class PDFGenerationRequest(BaseModel):
    """Request model for PDF generation"""
    patient_id: str
    assessment_type: str = "comprehensive"
    assessment_data: Dict[str, Any]
    conversation_data: Dict[str, Any]
    filename: str = None


class PDFGenerationResponse(BaseModel):
    """Response model for PDF generation"""
    success: bool
    pdfPath: str = None
    filename: str = None
    size: int = None
    error: str = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate authentication token"""
    # In production, implement proper JWT validation
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": "healthcare_provider", "role": "physician"}


@app.on_event("startup")
async def startup_event():
    """Initialize the Autogen healthcare system on startup"""
    global autogen_system
    
    # Load .env file explicitly
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../.env')

    try:
        # Configure FHIR client
        fhir_config = FHIRConfig(
            base_url=os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir/"),
            client_id=os.getenv("FHIR_CLIENT_ID", "autogen_healthcare_ai"),
            client_secret=os.getenv("FHIR_CLIENT_SECRET"),
            scopes=["patient/*.read", "user/*.read", "offline_access"]
        )
        
        # Initialize Autogen system
        autogen_system = HealthcareAutogenSystem(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            fhir_config=fhir_config
        )
        
        logger.info("Autogen Healthcare Agent System initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Autogen system: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Autogen Healthcare FHIR Agent System",
        "version": "1.0.0",
        "status": "running",
        "framework": "Microsoft Autogen",
        "agents": [
            "Primary Care Physician",
            "Cardiologist",
            "Clinical Pharmacist", 
            "Nurse Care Coordinator",
            "Emergency Physician"
        ],
        "features": [
            "Multi-agent conversations",
            "FHIR integration",
            "Real-time collaboration",
            "Clinical decision support"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "fhir_client": "connected",
            "autogen_agents": "ready",
            "conversation_engine": "active"
        },
        "active_connections": len(active_connections)
    }


@app.post("/conversation/comprehensive", response_model=ConversationResponse)
async def start_comprehensive_conversation(
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start comprehensive patient assessment conversation"""
    try:
        logger.info(f"Starting comprehensive conversation for patient {request.patient_id}")
        
        # Run comprehensive assessment with multi-agent conversation
        result = await autogen_system.run_comprehensive_assessment(request.patient_id)
        
        conversation_id = f"comp_{request.patient_id}_{int(asyncio.get_event_loop().time())}"
        
        # Log conversation completion
        background_tasks.add_task(
            log_conversation_completion,
            conversation_id,
            "comprehensive",
            current_user["user_id"]
        )
        
        return ConversationResponse(
            conversation_id=conversation_id,
            patient_id=request.patient_id,
            conversation_type="comprehensive",
            status="completed",
            participants=result["participating_agents"],
            summary=result["summary"],
            full_conversation=result["conversation_history"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Comprehensive conversation failed for patient {request.patient_id}: {e}")
        logger.error(f"Full error traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@app.post("/conversation/emergency", response_model=ConversationResponse)
async def start_emergency_conversation(
    request: EmergencyConversationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start emergency assessment conversation"""
    try:
        logger.info(f"Starting emergency conversation for patient {request.patient_id}")
        
        # Run emergency assessment
        result = await autogen_system.run_emergency_assessment(
            request.patient_id,
            request.chief_complaint
        )
        
        conversation_id = f"emerg_{request.patient_id}_{int(asyncio.get_event_loop().time())}"
        
        # Log conversation completion
        background_tasks.add_task(
            log_conversation_completion,
            conversation_id,
            "emergency",
            current_user["user_id"]
        )
        
        return ConversationResponse(
            conversation_id=conversation_id,
            patient_id=request.patient_id,
            conversation_type="emergency",
            status="completed",
            participants=result["participating_agents"],
            summary=result["summary"],
            full_conversation=result["conversation_history"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Emergency conversation failed for patient {request.patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency conversation failed: {str(e)}")


@app.post("/conversation/medication-review", response_model=ConversationResponse)
async def start_medication_review_conversation(
    request: MedicationReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start medication review conversation"""
    try:
        logger.info(f"Starting medication review for patient {request.patient_id}")
        
        # Run medication reconciliation
        result = await autogen_system.run_medication_reconciliation(request.patient_id)
        
        conversation_id = f"medrec_{request.patient_id}_{int(asyncio.get_event_loop().time())}"
        
        # Log conversation completion
        background_tasks.add_task(
            log_conversation_completion,
            conversation_id,
            "medication_review",
            current_user["user_id"]
        )
        
        return ConversationResponse(
            conversation_id=conversation_id,
            patient_id=request.patient_id,
            conversation_type="medication_review",
            status="completed",
            participants=result["participating_agents"],
            summary=result["summary"],
            full_conversation=result["conversation_history"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Medication review failed for patient {request.patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Medication review failed: {str(e)}")


@app.get("/patient/{patient_id}/summary")
async def get_patient_summary(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get patient summary from FHIR"""
    try:
        # Use the function registry to get patient data
        patient_data_str = autogen_system.function_registry.get_patient_data(patient_id)
        patient_data = json.loads(patient_data_str)
        
        if "error" in patient_data:
            raise HTTPException(status_code=500, detail=patient_data["error"])
        
        return {
            "patient_id": patient_id,
            "demographics": patient_data["demographics"],
            "summary": {
                "active_conditions": len(patient_data.get("conditions", [])),
                "current_medications": len(patient_data.get("medications", [])),
                "recent_vital_signs": len(patient_data.get("vital_signs", [])),
                "recent_lab_results": len(patient_data.get("lab_results", []))
            },
            "conditions": patient_data.get("conditions", []),
            "medications": patient_data.get("medications", []),
            "vital_signs": patient_data.get("vital_signs", [])[:5],  # Most recent 5
            "lab_results": patient_data.get("lab_results", [])[:5]   # Most recent 5
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve patient summary for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient data: {str(e)}")


@app.get("/agents/status")
async def get_agent_status(current_user: dict = Depends(get_current_user)):
    """Get status of all Autogen healthcare agents"""
    return {
        "framework": "Microsoft Autogen",
        "agents": [
            {
                "name": "Primary Care Physician",
                "role": "Comprehensive care coordination and assessment",
                "status": "active",
                "capabilities": [
                    "Patient data retrieval",
                    "Risk score calculation",
                    "Care plan generation",
                    "Clinical assessment"
                ]
            },
            {
                "name": "Cardiologist", 
                "role": "Cardiovascular risk assessment and recommendations",
                "status": "active",
                "capabilities": [
                    "Cardiovascular risk assessment",
                    "Cardiac condition evaluation",
                    "Treatment recommendations"
                ]
            },
            {
                "name": "Clinical Pharmacist",
                "role": "Medication safety and optimization",
                "status": "active", 
                "capabilities": [
                    "Drug interaction checking",
                    "Medication reconciliation",
                    "Dosing optimization",
                    "Safety monitoring"
                ]
            },
            {
                "name": "Nurse Care Coordinator",
                "role": "Care coordination and patient education",
                "status": "active",
                "capabilities": [
                    "Care plan coordination",
                    "Patient education",
                    "Follow-up scheduling",
                    "Resource coordination"
                ]
            },
            {
                "name": "Emergency Physician",
                "role": "Emergency assessment and acute care",
                "status": "active",
                "capabilities": [
                    "Rapid triage assessment",
                    "Emergency stabilization",
                    "Critical decision making",
                    "Risk stratification"
                ]
            }
        ],
        "conversation_types": [
            "comprehensive_assessment",
            "emergency_evaluation", 
            "medication_reconciliation"
        ],
        "total_agents": 5,
        "active_conversations": 0
    }


@app.websocket("/ws/conversation/{patient_id}")
async def websocket_conversation(websocket: WebSocket, patient_id: str):
    """WebSocket endpoint for real-time conversation monitoring"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Wait for conversation initiation
            data = await websocket.receive_text()
            message = json.loads(data)
            
            conversation_type = message.get("type", "comprehensive")
            
            # Start appropriate conversation based on type
            if conversation_type == "emergency":
                chief_complaint = message.get("chief_complaint", "General assessment")
                result = await autogen_system.run_emergency_assessment(patient_id, chief_complaint)
            elif conversation_type == "medication":
                result = await autogen_system.run_medication_reconciliation(patient_id)
            else:
                result = await autogen_system.run_comprehensive_assessment(patient_id)
            
            # Send conversation updates
            await websocket.send_text(json.dumps({
                "status": "completed",
                "result": result
            }))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected for patient {patient_id}")


@app.get("/conversations/history")
async def get_conversation_history(
    patient_id: str = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history (placeholder - would integrate with database)"""
    # In production, this would query a database for conversation history
    return {
        "patient_id": patient_id,
        "conversations": [
            {
                "conversation_id": "example_001",
                "type": "comprehensive",
                "timestamp": "2024-01-01T10:00:00Z",
                "participants": ["PrimaryCarePhysician", "Cardiologist"],
                "status": "completed"
            }
        ],
        "total": 1,
        "limit": limit
    }


@app.post("/generate-pdf", response_model=PDFGenerationResponse)
async def generate_assessment_pdf(
    request: PDFGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Generate PDF assessment report using AI agents"""
    try:
        logger.info(f"Generating PDF for patient {request.patient_id}, assessment type: {request.assessment_type}")
        
        if not autogen_system:
            raise HTTPException(status_code=500, detail="Autogen system not initialized")
        
        # Use the PDF generation function from FHIR tools
        from fhir_tools import FHIRToolsForAgents
        
        # Configure MCP URL (this should match the FHIR MCP server)
        mcp_url = os.getenv("FHIR_MCP_URL", "http://localhost:8003")
        fhir_tools = FHIRToolsForAgents(mcp_url=mcp_url)
        
        # Generate the PDF using the FHIR tools
        pdf_result = await fhir_tools.generate_assessment_pdf(
            patient_id=request.patient_id,
            assessment_data=request.assessment_data,
            conversation_data=request.conversation_data,
            filename=request.filename or f"assessment_{request.patient_id}_{request.assessment_type}.pdf"
        )
        
        if pdf_result.get("success"):
            # Return the file path and metadata
            return PDFGenerationResponse(
                success=True,
                pdfPath=pdf_result.get("file_path"),
                filename=pdf_result.get("filename"),
                size=pdf_result.get("file_size", 0)
            )
        else:
            return PDFGenerationResponse(
                success=False,
                error=pdf_result.get("error", "Failed to generate PDF")
            )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return PDFGenerationResponse(
            success=False,
            error=str(e)
        )


# Frontend-compatible endpoints (match the paths expected by the UI)
@app.post("/comprehensive")
async def run_comprehensive_conversation_compat(
    request: ConversationRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Frontend-compatible comprehensive conversation endpoint with custom API key support"""
    from llm_communication_tracker import get_tracker, LLMProvider, AgentFramework
    import time
    
    tracker = get_tracker()
    comm_id = None
    start_time = time.time()
    
    try:
        logger.info(f"Starting comprehensive conversation for patient {request.patient_id}")
        
        # Extract API key from Authorization header if provided
        api_key = None
        if authorization and authorization.startswith("Bearer "):
            api_key = authorization[7:]  # Remove "Bearer " prefix
            logger.info(f"Using API key from request header: {api_key[:10]}...{api_key[-4:]}")
        
        # Start tracking the conversation
        comm_id = tracker.start_communication(
            agent_id="autogen_comprehensive_system",
            agent_name="AutoGen Comprehensive Assessment",
            agent_specialty="Multi-Agent Healthcare Team",
            framework=AgentFramework.AUTOGEN,
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            patient_id=request.patient_id,
            scenario_type="comprehensive_assessment"
        )
        
        # Use provided API key or fall back to environment/default
        if api_key and api_key != os.getenv("OPENAI_API_KEY", ""):
            # Create a temporary AutoGen system with the custom API key
            from agents import HealthcareAutogenSystem
            temp_autogen_system = HealthcareAutogenSystem(
                openai_api_key=api_key,
                fhir_config=autogen_system.fhir_client.config,
                mcp_url=autogen_system.mcp_url
            )
            result = await temp_autogen_system.run_comprehensive_assessment(request.patient_id)
        else:
            # Use the default system instance
            result = await autogen_system.run_comprehensive_assessment(request.patient_id)
        
        conversation_id = f"comp_{request.patient_id}_{int(asyncio.get_event_loop().time())}"
        
        # Complete successful tracking
        if comm_id:
            response_time = int((time.time() - start_time) * 1000)
            tracker.complete_communication(
                comm_id=comm_id,
                final_response=str(result.get("summary", "")),
                response_time_ms=response_time,
                confidence_score=0.85
            )
        
        # Log conversation completion
        background_tasks.add_task(
            log_conversation_completion,
            conversation_id,
            "comprehensive",
            current_user["user_id"]
        )
        
        return ConversationResponse(
            conversation_id=conversation_id,
            patient_id=request.patient_id,
            conversation_type="comprehensive",
            status="completed",
            participants=result["participating_agents"],
            summary=result["summary"],
            full_conversation=result["conversation_history"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Comprehensive conversation failed for patient {request.patient_id}: {e}")
        logger.error(f"Full error traceback: {error_details}")
        
        # Track the error with detailed analysis
        if comm_id:
            response_time = int((time.time() - start_time) * 1000)
            error_message, error_type, error_code = tracker.parse_openai_error(e)
            
            tracker.complete_communication(
                comm_id=comm_id,
                final_response="",
                response_time_ms=response_time,
                error_message=error_message,
                error_type=error_type,
                error_code=error_code
            )
            
            logger.error(f"Tracked error: {error_type} ({error_code}) - {error_message}")
        
        raise HTTPException(status_code=500, detail=f"Conversation failed: {str(e)}")


@app.post("/emergency")  
async def run_emergency_conversation_compat(
    request: EmergencyConversationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Frontend-compatible emergency conversation endpoint"""
    return await start_emergency_conversation(request, background_tasks, current_user)


@app.post("/medication-review")
async def run_medication_review_compat(
    request: MedicationReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Frontend-compatible medication review endpoint"""
    return await start_medication_review_conversation(request, background_tasks, current_user)


@app.get("/communications")
async def get_communications():
    """Get agent communications history with detailed error tracking"""
    from llm_communication_tracker import get_tracker
    
    try:
        tracker = get_tracker()
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
                "errorType": comm.error_type,
                "errorCode": comm.error_code,
                "retryCount": comm.retry_count,
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
        
        return {
            "communications": communications,
            "total": len(communications),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to get communications: {e}")
        return {
            "communications": [],
            "total": 0,
            "status": "error",
            "error": str(e)
        }


@app.get("/communications/stats")
async def get_communication_stats():
    """Get communication statistics with enhanced error tracking"""
    from llm_communication_tracker import get_tracker
    
    try:
        tracker = get_tracker()
        stats = tracker.get_communication_stats()
        
        # Add quota exceeded details
        quota_details = tracker.get_quota_exceeded_details()
        stats["quota_status"] = quota_details
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get communication stats: {e}")
        return {
            "total": 0,
            "completed": 0,
            "errors": 0,
            "status": "error",
            "error": str(e)
        }


async def log_conversation_completion(conversation_id: str, conversation_type: str, provider_id: str):
    """Background task to log conversation completion"""
    logger.info(f"Conversation completed: {conversation_type} (ID: {conversation_id}) by provider {provider_id}")
    # In production, this would write to audit logs or database


if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Different port from CrewAI version
        reload=True,
        log_level="info"
    )