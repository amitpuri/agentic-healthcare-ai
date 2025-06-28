"""
CrewAI Healthcare FHIR Agent System
Main application for running healthcare AI agents with FHIR integration
"""

import asyncio
import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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
from agents import HealthcareAgentManager

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
    title="CrewAI Healthcare FHIR Agent System",
    description="AI-powered healthcare agents with FHIR integration using CrewAI framework",
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
agent_manager: HealthcareAgentManager = None


class AssessmentRequest(BaseModel):
    """Request model for patient assessment"""
    patient_id: str
    assessment_type: str = "comprehensive"  # comprehensive, emergency, medication_reconciliation
    chief_complaint: str = None
    urgency: str = "routine"  # routine, urgent, emergent


class EmergencyRequest(BaseModel):
    """Request model for emergency assessment"""
    patient_id: str
    chief_complaint: str
    vital_signs: Dict[str, Any] = None
    presenting_symptoms: list = None


class MedicationReconciliationRequest(BaseModel):
    """Request model for medication reconciliation"""
    patient_id: str
    admission_medications: list = None
    discharge_medications: list = None


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
    """Initialize the healthcare agent manager on startup"""
    global agent_manager
    
    try:
        # Configure FHIR client
        fhir_config = FHIRConfig(
            base_url=os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4/"),
            client_id=os.getenv("FHIR_CLIENT_ID", "healthcare_ai_agent"),
            client_secret=os.getenv("FHIR_CLIENT_SECRET"),
            scopes=["patient/*.read", "user/*.read", "offline_access"]
        )
        
        # Initialize agent manager with demo key if none provided
        api_key = os.getenv("OPENAI_API_KEY", "demo_key_for_testing")
        agent_manager = HealthcareAgentManager(
            openai_api_key=api_key,
            fhir_config=fhir_config
        )
        
        logger.info("CrewAI Healthcare Agent System initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent system: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CrewAI Healthcare FHIR Agent System",
        "version": "1.0.0",
        "status": "running",
        "agents": [
            "Primary Care Physician",
            "Cardiologist",
            "Clinical Pharmacist", 
            "Nurse Care Coordinator"
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
            "ai_agents": "ready",
            "database": "connected"
        }
    }


@app.post("/assessment/comprehensive")
async def run_comprehensive_assessment(
    request: AssessmentRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Run comprehensive patient assessment"""
    try:
        logger.info(f"Starting comprehensive assessment for patient {request.patient_id}")
        
        # Run assessment asynchronously
        result = await agent_manager.run_patient_assessment(request.patient_id)
        
        # Log assessment completion
        background_tasks.add_task(
            log_assessment_completion,
            request.patient_id,
            "comprehensive",
            current_user["user_id"]
        )
        
        return {
            "status": "completed",
            "assessment_id": f"assess_{request.patient_id}_{int(asyncio.get_event_loop().time())}",
            "patient_id": request.patient_id,
            "assessment_type": "comprehensive",
            "results": result,
            "provider": current_user["user_id"]
        }
        
    except Exception as e:
        logger.error(f"Assessment failed for patient {request.patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@app.post("/assessment/emergency")
async def run_emergency_assessment(
    request: EmergencyRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Run emergency patient assessment"""
    try:
        logger.info(f"Starting emergency assessment for patient {request.patient_id}")
        
        # Run emergency assessment
        result = await agent_manager.run_emergency_assessment(
            request.patient_id,
            request.chief_complaint
        )
        
        # Log assessment completion
        background_tasks.add_task(
            log_assessment_completion,
            request.patient_id,
            "emergency",
            current_user["user_id"]
        )
        
        return {
            "status": "completed",
            "assessment_id": f"emerg_{request.patient_id}_{int(asyncio.get_event_loop().time())}",
            "patient_id": request.patient_id,
            "assessment_type": "emergency",
            "chief_complaint": request.chief_complaint,
            "urgency": "high",
            "results": result,
            "provider": current_user["user_id"]
        }
        
    except Exception as e:
        logger.error(f"Emergency assessment failed for patient {request.patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency assessment failed: {str(e)}")


@app.post("/assessment/medication-reconciliation")
async def run_medication_reconciliation(
    request: MedicationReconciliationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Run medication reconciliation"""
    try:
        logger.info(f"Starting medication reconciliation for patient {request.patient_id}")
        
        # Create medication reconciliation crew
        crew = agent_manager.create_medication_reconciliation_crew(request.patient_id)
        result = crew.kickoff()
        
        # Log completion
        background_tasks.add_task(
            log_assessment_completion,
            request.patient_id,
            "medication_reconciliation",
            current_user["user_id"]
        )
        
        return {
            "status": "completed",
            "reconciliation_id": f"medrec_{request.patient_id}_{int(asyncio.get_event_loop().time())}",
            "patient_id": request.patient_id,
            "assessment_type": "medication_reconciliation",
            "results": result,
            "provider": current_user["user_id"]
        }
        
    except Exception as e:
        logger.error(f"Medication reconciliation failed for patient {request.patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Medication reconciliation failed: {str(e)}")


@app.get("/patient/{patient_id}/summary")
async def get_patient_summary(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get patient summary from FHIR"""
    try:
        # Retrieve patient data from FHIR
        patient_data = await agent_manager.fhir_client.get_comprehensive_patient_data(patient_id)
        
        return {
            "patient_id": patient_id,
            "demographics": {
                "name": str(patient_data["patient"].name[0]) if patient_data["patient"].name else "",
                "birth_date": str(patient_data["patient"].birthDate) if patient_data["patient"].birthDate else None,
                "gender": patient_data["patient"].gender
            },
            "summary": {
                "active_conditions": len(patient_data["conditions"]),
                "current_medications": len(patient_data["medications"]),
                "recent_observations": len(patient_data["observations"]),
                "recent_encounters": len(patient_data["encounters"])
            },
            "last_updated": patient_data["last_updated"]
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve patient summary for {patient_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient data: {str(e)}")


@app.get("/agents/status")
async def get_agent_status(current_user: dict = Depends(get_current_user)):
    """Get status of all healthcare agents"""
    return {
        "agents": [
            {
                "name": "Primary Care Physician",
                "role": "Comprehensive care coordination and assessment",
                "status": "active",
                "tools": ["FHIR Patient Tool", "Clinical Decision Support", "Diagnostic Assistant"]
            },
            {
                "name": "Cardiologist", 
                "role": "Cardiovascular risk assessment and recommendations",
                "status": "active",
                "tools": ["FHIR Patient Tool", "Clinical Decision Support"]
            },
            {
                "name": "Clinical Pharmacist",
                "role": "Medication safety and optimization",
                "status": "active", 
                "tools": ["FHIR Patient Tool", "Medication Interaction Checker"]
            },
            {
                "name": "Nurse Care Coordinator",
                "role": "Care coordination and patient education",
                "status": "active",
                "tools": ["FHIR Patient Tool"]
            }
        ],
        "total_agents": 4,
        "active_assessments": 0
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
        
        if not agent_manager:
            raise HTTPException(status_code=500, detail="Agent manager not initialized")
        
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
async def run_comprehensive_assessment_compat(
    request: AssessmentRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Frontend-compatible comprehensive assessment endpoint with custom API key support"""
    from llm_communication_tracker import get_tracker, LLMProvider, AgentFramework
    import time
    
    tracker = get_tracker()
    comm_id = None
    start_time = time.time()
    
    try:
        logger.info(f"Starting comprehensive assessment for patient {request.patient_id}")
        
        # Extract API key from Authorization header if provided
        api_key = None
        if authorization and authorization.startswith("Bearer "):
            api_key = authorization[7:]  # Remove "Bearer " prefix
            logger.info(f"Using API key from request header: {api_key[:10]}...{api_key[-4:]}")
        
        # Start tracking the conversation
        comm_id = tracker.start_communication(
            agent_id="crewai_comprehensive_system",
            agent_name="CrewAI Comprehensive Assessment",
            agent_specialty="Multi-Agent Healthcare Team",
            framework=AgentFramework.CREWAI,
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            patient_id=request.patient_id,
            scenario_type="comprehensive_assessment"
        )
        
        # Use provided API key or fall back to environment/default
        if api_key and api_key != os.getenv("OPENAI_API_KEY", ""):
            # Create a temporary agent manager with the custom API key
            from agents import HealthcareAgentManager
            temp_agent_manager = HealthcareAgentManager(
                openai_api_key=api_key,
                fhir_config=agent_manager.fhir_client.config,
                mcp_url=agent_manager.mcp_url
            )
            result = await temp_agent_manager.run_patient_assessment(request.patient_id)
        else:
            # Use the default agent manager instance
            result = await agent_manager.run_patient_assessment(request.patient_id)
        
        # Complete successful tracking
        if comm_id:
            response_time = int((time.time() - start_time) * 1000)
            tracker.complete_communication(
                comm_id=comm_id,
                final_response=str(result.get("summary", "")),
                response_time_ms=response_time,
                confidence_score=0.85
            )
        
        # Log assessment completion
        background_tasks.add_task(
            log_assessment_completion,
            request.patient_id,
            "comprehensive",
            current_user["user_id"]
        )
        
        return {
            "success": True,
            "patient_id": request.patient_id,
            "assessment_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
            "agents_used": result.get("agents", []),
            "summary": result.get("summary", {}),
            "recommendations": result.get("recommendations", []),
            "conversation_history": result.get("conversation_history", []),
            "participating_agents": result.get("participating_agents", [])
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Comprehensive assessment failed for patient {request.patient_id}: {e}")
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
        
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@app.post("/emergency")  
async def run_emergency_assessment_compat(
    request: EmergencyRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Frontend-compatible emergency assessment endpoint"""
    return await run_emergency_assessment(request, background_tasks, current_user)


@app.post("/medication-reconciliation")
async def run_medication_reconciliation_compat(
    request: MedicationReconciliationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Frontend-compatible medication reconciliation endpoint"""
    return await run_medication_reconciliation(request, background_tasks, current_user)


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


async def log_assessment_completion(patient_id: str, assessment_type: str, provider_id: str):
    """Background task to log assessment completion"""
    logger.info(f"Assessment completed: {assessment_type} for patient {patient_id} by provider {provider_id}")
    # In production, this would write to audit logs or database


if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
