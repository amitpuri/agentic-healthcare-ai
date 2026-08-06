"""
Healthcare AI Agents using CrewAI Framework
Implements specialized medical agents for different healthcare domains
"""

from crewai import Agent, Task, Crew, Process
from langchain.tools import BaseTool
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
import json
import asyncio
import concurrent.futures
import logging
import threading
import time
from datetime import datetime
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from fhir_client import FHIRClient, FHIRConfig
from fhir_tools import FHIRToolsForAgents, FHIRMCPClient, PatientAssessmentReport
from healthcare_models import (
    PatientSummary, ClinicalAssessment, ClinicalAlert,
    ClinicalDecisionSupport, Severity, Priority, ClinicalSpecialty
)
import clinical_rules

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run a coroutine from CrewAI's synchronous tool interface.

    Tools execute inside uvicorn's already-running event loop, so calling
    run_until_complete on the current thread raises "Cannot run the event loop
    while another loop is running". Giving the coroutine its own loop on a
    worker thread keeps the tool synchronous without touching the live loop.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


class LLMQuotaExhausted(Exception):
    """The LLM provider rejected the call for quota or rate-limit reasons.

    Distinct from a service fault so callers can tell "the AI provider is out of
    credit" apart from "this service is broken".
    """

    def __init__(self, message: str, error_code: str = "llm_quota_exhausted",
                 retry_after: Optional[int] = None):
        super().__init__(message)
        self.error_code = error_code
        self.retry_after = retry_after


_QUOTA_MARKERS = ("insufficient_quota", "exceeded your current quota",
                  "billing_hard_limit_reached", "check your plan and billing")
_RATE_LIMIT_MARKERS = ("rate_limit_exceeded", "rate limit reached",
                       "too many requests", "429")


def _exception_chain(exc: BaseException):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def _retry_after_from(exc: BaseException) -> Optional[int]:
    headers = getattr(getattr(exc, "response", None), "headers", None)
    if not headers:
        return None
    for key in ("retry-after", "x-ratelimit-reset-requests"):
        raw = headers.get(key)
        if raw:
            try:
                return int(float(str(raw).rstrip("s")))
            except ValueError:
                continue
    return None


def classify_llm_failure(exc: BaseException) -> Optional[LLMQuotaExhausted]:
    """Map a provider quota/rate-limit failure onto LLMQuotaExhausted.

    Returns None for anything else, which stays a genuine 500.
    """
    for item in _exception_chain(exc):
        text = str(item).lower()
        code = getattr(item, "code", None) or getattr(item, "type", None)
        if str(code).lower() == "insufficient_quota" or any(m in text for m in _QUOTA_MARKERS):
            return LLMQuotaExhausted(
                "The configured LLM provider account has no remaining quota.",
                error_code="llm_quota_exhausted",
                retry_after=_retry_after_from(item),
            )
        if type(item).__name__ == "RateLimitError" or any(m in text for m in _RATE_LIMIT_MARKERS):
            return LLMQuotaExhausted(
                "The configured LLM provider is rate limiting this service.",
                error_code="llm_rate_limited",
                retry_after=_retry_after_from(item) or 30,
            )
    return None


# CrewAI executes LLM calls on its own worker threads, so the failure record is
# process-global and scoped by timestamp rather than thread-local.
_llm_failure_lock = threading.Lock()
_llm_failure_state: Dict[str, Any] = {"error": None, "at": 0.0}


class LLMFailureRecorder(BaseCallbackHandler):
    """Records provider errors raised during a crew run.

    CrewAI's agent executor turns every LLM exception into an observation and
    finishes with the sentinel "Agent stopped due to iteration limit or time
    limit", so an exhausted API key otherwise surfaces as a successful-looking
    assessment containing no reasoning at all.
    """

    def on_llm_error(self, error: BaseException, **kwargs) -> None:
        record_llm_failure(error)


def record_llm_failure(exc: BaseException) -> None:
    with _llm_failure_lock:
        _llm_failure_state["error"] = exc
        _llm_failure_state["at"] = time.monotonic()


def reset_llm_failures() -> float:
    with _llm_failure_lock:
        _llm_failure_state["error"] = None
        _llm_failure_state["at"] = 0.0
    return time.monotonic()


def llm_failure_since(started: float) -> Optional[BaseException]:
    with _llm_failure_lock:
        if _llm_failure_state["error"] is not None and _llm_failure_state["at"] >= started:
            return _llm_failure_state["error"]
    return None


DEGRADED_OUTPUT_MARKERS = ("agent stopped due to iteration limit",)


def _output_is_degraded(result: Any) -> bool:
    """True when the crew produced no real reasoning."""
    raw = (getattr(result, "raw", "") or "").strip().lower()
    return not raw or any(marker in raw for marker in DEGRADED_OUTPUT_MARKERS)


def kickoff(crew: Crew):
    """Run a crew, surfacing provider quota failures as a distinct error type."""
    started = reset_llm_failures()
    try:
        result = crew.kickoff()
    except Exception as exc:
        quota_error = classify_llm_failure(exc)
        if quota_error:
            logger.error(f"LLM provider unavailable ({quota_error.error_code}): {exc}")
            raise quota_error from exc
        raise

    # A swallowed provider failure plus empty output means the assessment is not
    # a result, it is an outage. Report it as one rather than returning 200.
    recorded = llm_failure_since(started)
    if recorded is not None and _output_is_degraded(result):
        quota_error = classify_llm_failure(recorded)
        if quota_error:
            logger.error(f"LLM provider unavailable ({quota_error.error_code}): {recorded}")
            raise quota_error from recorded
    return result


def serialize_crew_output(result: Any, crew: Crew = None) -> Dict[str, Any]:
    """Convert CrewOutput into a response payload without the built prompts.

    Task descriptions interpolate untrusted patient free text, so echoing them
    (and the summary derived from them) would return PHI-bearing input to the
    caller and persist it downstream. Only the static task identity and the
    agents' own output are returned.
    """
    # TaskOutput carries no name, so task identity comes from the crew definition
    # by position rather than from the interpolated description.
    task_names = [getattr(task, "name", None) for task in getattr(crew, "tasks", None) or []]

    tasks = []
    for index, task_output in enumerate(getattr(result, "tasks_output", None) or []):
        name = task_names[index] if index < len(task_names) else None
        tasks.append({
            "task": name or f"task_{index + 1}",
            "agent": getattr(task_output, "agent", None),
            "expected_output": getattr(task_output, "expected_output", None),
            "raw": getattr(task_output, "raw", None),
        })

    token_usage = getattr(result, "token_usage", None)
    if hasattr(token_usage, "model_dump"):
        token_usage = token_usage.model_dump()

    return {
        "raw": getattr(result, "raw", None) if hasattr(result, "raw") else str(result),
        "tasks": tasks,
        "token_usage": token_usage,
    }


class FHIRPatientTool(BaseTool):
    """Enhanced tool for retrieving patient data from FHIR server via MCP"""
    
    name: str = "fhir_patient_retrieval"
    description: str = "Retrieve comprehensive patient data from FHIR server via MCP including demographics, conditions, medications, vital signs, and encounters"
    fhir_tools: FHIRToolsForAgents = None
    
    def __init__(self, fhir_tools: FHIRToolsForAgents):
        super().__init__()
        object.__setattr__(self, 'fhir_tools', fhir_tools)
    
    def _run(self, patient_id: str) -> str:
        """Retrieve comprehensive patient data via MCP"""
        try:
            return run_async(self.fhir_tools.get_patient_for_assessment(patient_id))
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class ClinicalDecisionTool(BaseTool):
    """Tool for clinical decision support and risk assessment"""
    
    name: str = "clinical_decision_support" 
    description: str = "Provide clinical decision support, risk assessment, and treatment recommendations based on patient data"
    
    def __init__(self):
        super().__init__()
    
    def _run(self, patient_summary: str, clinical_question: str = "") -> str:
        """Provide clinical decision support derived from the supplied patient context"""
        try:
            return json.dumps(
                clinical_rules.assess(patient_summary, clinical_question), indent=2
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class MedicationInteractionTool(BaseTool):
    """Tool for checking medication interactions and contraindications"""
    
    name: str = "medication_interaction_checker"
    description: str = "Check for drug interactions, contraindications, and dosing recommendations"
    
    def __init__(self):
        super().__init__()
    
    def _run(self, medications_list: str) -> str:
        """Screen the supplied medications against the interaction rule table"""
        try:
            return json.dumps(clinical_rules.check_medications(medications_list), indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class DiagnosticAssistantTool(BaseTool):
    """Tool for diagnostic assistance and differential diagnosis"""
    
    name: str = "diagnostic_assistant"
    description: str = "Assist with differential diagnosis and diagnostic workup recommendations"
    
    def __init__(self):
        super().__init__()
    
    def _run(self, symptoms: str, patient_history: str = "") -> str:
        """Provide diagnostic assistance grounded in the presented symptoms"""
        try:
            findings = clinical_rules.assess(patient_history, symptoms)
            return json.dumps({
                "presenting_features_recognized": findings["conditions_identified"],
                "red_flags": findings["red_flags"],
                "urgency_level": findings["urgency_level"],
                "workup_and_management": findings["recommendations"],
                "monitoring": findings["monitoring"],
                "medication_safety": findings["medication_safety"],
                "basis": findings["basis"],
            }, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class FHIREncounterTool(BaseTool):
    """Tool for retrieving and analyzing encounter data via MCP"""
    
    name: str = "fhir_encounter_analysis"
    description: str = "Retrieve and analyze encounter details including observations, procedures, and diagnostic reports"
    fhir_tools: FHIRToolsForAgents = None
    
    def __init__(self, fhir_tools: FHIRToolsForAgents):
        super().__init__()
        object.__setattr__(self, 'fhir_tools', fhir_tools)
    
    def _run(self, encounter_id: str) -> str:
        """Retrieve encounter analysis via MCP"""
        try:
            return run_async(self.fhir_tools.get_encounter_for_analysis(encounter_id))
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class FHIRVitalSignsTool(BaseTool):
    """Tool for retrieving and analyzing vital signs trends via MCP"""
    
    name: str = "fhir_vital_signs_analysis"
    description: str = "Retrieve and analyze vital signs trends and patterns over specified time period"
    fhir_tools: FHIRToolsForAgents = None
    
    def __init__(self, fhir_tools: FHIRToolsForAgents):
        super().__init__()
        object.__setattr__(self, 'fhir_tools', fhir_tools)
    
    def _run(self, patient_id: str, days: str = "30") -> str:
        """Retrieve vital signs trends via MCP"""
        try:
            return run_async(self.fhir_tools.get_vital_signs_trends(patient_id, int(days)))
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class PDFAssessmentReportTool(BaseTool):
    """Tool for generating PDF assessment reports"""
    
    name: str = "generate_assessment_pdf"
    description: str = "Generate comprehensive patient assessment report in PDF format"
    fhir_tools: FHIRToolsForAgents = None
    
    def __init__(self, fhir_tools: FHIRToolsForAgents):
        super().__init__()
        object.__setattr__(self, 'fhir_tools', fhir_tools)
    
    def _run(self, patient_id: str, assessment_data: str = "", filename: str = "") -> str:
        """Generate PDF assessment report"""
        try:
            # Parse assessment data if provided
            parsed_assessment = None
            if assessment_data:
                try:
                    parsed_assessment = json.loads(assessment_data)
                except:
                    parsed_assessment = {"ai_assessment_summary": assessment_data}
            
            return run_async(
                self.fhir_tools.generate_assessment_pdf(
                    patient_id,
                    parsed_assessment,
                    filename if filename else None
                )
            )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class HealthcareAgentManager:
    """Manager for coordinating healthcare AI agents with MCP integration"""
    
    def __init__(self, openai_api_key: str, fhir_config: FHIRConfig, mcp_url: str = None):
        # Handle API key validation - use environment variable temporarily for initialization
        if not openai_api_key or openai_api_key == "demo_key_for_testing":
            # Set environment variable temporarily for langchain_openai initialization
            os.environ["OPENAI_API_KEY"] = "sk-temp_demo_key_for_initialization_12345678901234567890123456789012"
            
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=openai_api_key if openai_api_key and openai_api_key != "demo_key_for_testing" else "sk-temp_demo_key_for_initialization_12345678901234567890123456789012",
            callbacks=[LLMFailureRecorder()]
        )
        self.fhir_client = FHIRClient(fhir_config)
        self.mcp_url = mcp_url or os.getenv('REACT_APP_FHIR_MCP_URL', 'http://localhost:8004')
        self.fhir_tools = FHIRToolsForAgents(self.mcp_url)
        
        # Initialize enhanced MCP-based tools
        self.fhir_tool = FHIRPatientTool(self.fhir_tools)
        self.encounter_tool = FHIREncounterTool(self.fhir_tools)
        self.vitals_tool = FHIRVitalSignsTool(self.fhir_tools)
        self.pdf_tool = PDFAssessmentReportTool(self.fhir_tools)
        self.clinical_decision_tool = ClinicalDecisionTool()
        self.medication_tool = MedicationInteractionTool()
        self.diagnostic_tool = DiagnosticAssistantTool()
        
        # Create specialized agents
        self.primary_care_agent = self._create_primary_care_agent()
        self.cardiology_agent = self._create_cardiology_agent()
        self.pharmacist_agent = self._create_pharmacist_agent()
        self.nurse_coordinator_agent = self._create_nurse_coordinator_agent()
        
    def _create_primary_care_agent(self) -> Agent:
        """Create primary care physician agent"""
        return Agent(
            role="Primary Care Physician",
            goal="Provide comprehensive primary care assessment, coordinate care, and ensure continuity of patient management",
            backstory="""You are an experienced primary care physician with expertise in 
            internal medicine, preventive care, and care coordination. You focus on 
            comprehensive patient assessment, risk factor identification, and 
            coordination with specialists when needed.""",
            verbose=True,
            allow_delegation=True,
            tools=[self.fhir_tool, self.encounter_tool, self.vitals_tool, self.pdf_tool, self.clinical_decision_tool, self.diagnostic_tool],
            llm=self.llm
        )
    
    def _create_cardiology_agent(self) -> Agent:
        """Create cardiology specialist agent"""
        return Agent(
            role="Cardiologist",
            goal="Provide specialized cardiovascular assessment, risk stratification, and treatment recommendations",
            backstory="""You are a board-certified cardiologist with expertise in 
            cardiovascular disease prevention, diagnosis, and treatment. You specialize 
            in risk assessment, ECG interpretation, and evidence-based cardiovascular 
            therapeutics.""",
            verbose=True,
            allow_delegation=False,
            tools=[self.fhir_tool, self.encounter_tool, self.vitals_tool, self.clinical_decision_tool],
            llm=self.llm
        )
    
    def _create_pharmacist_agent(self) -> Agent:
        """Create clinical pharmacist agent"""
        return Agent(
            role="Clinical Pharmacist",
            goal="Ensure medication safety, optimize drug therapy, and prevent adverse drug interactions",
            backstory="""You are a clinical pharmacist with expertise in 
            pharmacotherapy, drug interactions, and medication safety. You focus on 
            medication reconciliation, dosing optimization, and patient education 
            about medications.""",
            verbose=True,
            allow_delegation=False,
            tools=[self.fhir_tool, self.encounter_tool, self.vitals_tool, self.medication_tool],
            llm=self.llm
        )
    
    def _create_nurse_coordinator_agent(self) -> Agent:
        """Create nurse care coordinator agent"""
        return Agent(
            role="Nurse Care Coordinator",
            goal="Coordinate patient care, ensure follow-up compliance, and provide patient education",
            backstory="""You are an experienced registered nurse with expertise in 
            care coordination, patient education, and care transition management. 
            You focus on ensuring patients receive appropriate follow-up care and 
            understand their treatment plans.""",
            verbose=True,
            allow_delegation=False,
            tools=[self.fhir_tool, self.encounter_tool, self.pdf_tool],
            llm=self.llm
        )
    
    def create_patient_assessment_crew(self, patient_id: str, chief_complaint: str = None) -> Crew:
        """Create a crew for comprehensive patient assessment"""

        complaint_context = ""
        if chief_complaint:
            complaint_context = (
                f"\n\nThe requesting clinician recorded this chief complaint / reason for "
                f"the assessment, which you must address explicitly:\n{chief_complaint}"
            )

        # Define tasks for the crew
        patient_data_task = Task(
            name="patient_data_review",
            description=f"""Retrieve and analyze comprehensive patient data for patient ID: {patient_id}.
            Include demographics, medical history, current medications, recent lab results,
            and vital signs. Identify any immediate concerns or red flags.{complaint_context}""",
            agent=self.primary_care_agent,
            expected_output="Comprehensive patient summary with identified concerns and initial assessment"
        )

        cardiovascular_assessment_task = Task(
            name="cardiovascular_risk_assessment",
            description=f"""Perform specialized cardiovascular risk assessment based on the
            patient data. Evaluate cardiovascular risk factors, calculate risk scores,
            and provide recommendations for cardiovascular health management.{complaint_context}""",
            agent=self.cardiology_agent,
            expected_output="Cardiovascular risk assessment with specific recommendations"
        )

        medication_review_task = Task(
            name="medication_review",
            description=f"""Conduct comprehensive medication review including interaction
            checking, dosing appropriateness, and therapeutic duplication screening.
            Use the medication_interaction_checker tool with the patient's actual medication
            list retrieved from FHIR, and report every interaction it returns.
            Provide recommendations for medication optimization.{complaint_context}""",
            agent=self.pharmacist_agent,
            expected_output="Medication review with safety recommendations and optimization suggestions"
        )

        care_coordination_task = Task(
            name="care_coordination_plan",
            description=f"""Develop care coordination plan including follow-up scheduling,
            patient education priorities, and care transition planning. Ensure all
            recommendations from specialists are integrated into the care plan.{complaint_context}""",
            agent=self.nurse_coordinator_agent,
            expected_output="Comprehensive care coordination plan with follow-up timeline"
        )

        return Crew(
            agents=[
                self.primary_care_agent, 
                self.cardiology_agent, 
                self.pharmacist_agent,
                self.nurse_coordinator_agent
            ],
            tasks=[
                patient_data_task,
                cardiovascular_assessment_task,
                medication_review_task,
                care_coordination_task
            ],
            process=Process.sequential,
            verbose=True
        )
    
    def create_emergency_assessment_crew(self, patient_id: str, chief_complaint: str) -> Crew:
        """Create a crew for emergency patient assessment"""
        
        triage_task = Task(
            name="emergency_triage",
            description=f"""Perform emergency triage assessment for patient {patient_id}
            with chief complaint: {chief_complaint}. Retrieve patient data, assess
            severity, and determine urgency level. Identify any life-threatening conditions.""",
            agent=self.primary_care_agent,
            expected_output="Emergency triage assessment with urgency level and immediate interventions"
        )

        rapid_medication_check = Task(
            name="rapid_medication_safety_check",
            description="""Perform rapid medication safety check focusing on emergency
            contraindications, drug allergies, and critical interactions that could
            affect emergency treatment. Retrieve the patient's actual medication list from
            FHIR and pass it to the medication_interaction_checker tool; report every
            interaction the tool returns.""",
            agent=self.pharmacist_agent,
            expected_output="Critical medication safety information for emergency care"
        )
        
        return Crew(
            agents=[self.primary_care_agent, self.pharmacist_agent],
            tasks=[triage_task, rapid_medication_check],
            process=Process.sequential,
            verbose=True
        )
    
    def create_medication_reconciliation_crew(self, patient_id: str) -> Crew:
        """Create a crew for medication reconciliation"""
        
        med_reconciliation_task = Task(
            name="medication_reconciliation",
            description=f"""Perform comprehensive medication reconciliation for patient {patient_id}.
            Compare current medications with previous records, identify discrepancies, 
            and check for interactions, duplications, and appropriateness.""",
            agent=self.pharmacist_agent,
            expected_output="Complete medication reconciliation report with recommendations"
        )
        
        clinical_review_task = Task(
            name="clinical_review",
            description="""Review medication reconciliation findings from clinical perspective.
            Assess therapeutic appropriateness, identify potential therapeutic gaps, 
            and provide clinical recommendations.""",
            agent=self.primary_care_agent,
            expected_output="Clinical review of medication changes with therapeutic recommendations"
        )
        
        coordination_task = Task(
            name="medication_change_coordination",
            description="""Coordinate implementation of medication changes including
            patient education, pharmacy communication, and follow-up scheduling 
            for medication monitoring.""",
            agent=self.nurse_coordinator_agent,
            expected_output="Medication change implementation plan with patient education materials"
        )
        
        return Crew(
            agents=[self.pharmacist_agent, self.primary_care_agent, self.nurse_coordinator_agent],
            tasks=[med_reconciliation_task, clinical_review_task, coordination_task],
            process=Process.sequential,
            verbose=True
        )
    
    async def run_patient_assessment(self, patient_id: str, chief_complaint: str = None) -> Dict[str, Any]:
        """Run comprehensive patient assessment"""
        crew = self.create_patient_assessment_crew(patient_id, chief_complaint)
        result = await asyncio.to_thread(kickoff, crew)

        return {
            "patient_id": patient_id,
            "assessment_type": "comprehensive",
            "chief_complaint_provided": bool(chief_complaint),
            "timestamp": datetime.now().isoformat(),
            "results": serialize_crew_output(result, crew),
            "crew_composition": [
                "Primary Care Physician",
                "Cardiologist",
                "Clinical Pharmacist",
                "Nurse Care Coordinator"
            ]
        }

    async def run_emergency_assessment(self, patient_id: str, chief_complaint: str) -> Dict[str, Any]:
        """Run emergency patient assessment"""
        crew = self.create_emergency_assessment_crew(patient_id, chief_complaint)
        result = await asyncio.to_thread(kickoff, crew)

        return {
            "patient_id": patient_id,
            "assessment_type": "emergency",
            "timestamp": datetime.now().isoformat(),
            "results": serialize_crew_output(result, crew),
            "crew_composition": [
                "Primary Care Physician",
                "Clinical Pharmacist"
            ]
        }
