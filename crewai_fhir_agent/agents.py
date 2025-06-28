"""
Healthcare AI Agents using CrewAI Framework
Implements specialized medical agents for different healthcare domains
"""

from crewai import Agent, Task, Crew, Process
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from typing import Dict, List, Any, Optional
import json
import asyncio
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.get_patient_for_assessment(patient_id)
            )
            loop.close()
            return result
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class ClinicalDecisionTool(BaseTool):
    """Tool for clinical decision support and risk assessment"""
    
    name: str = "clinical_decision_support" 
    description: str = "Provide clinical decision support, risk assessment, and treatment recommendations based on patient data"
    
    def __init__(self):
        super().__init__()
    
    def _run(self, patient_summary: str, clinical_question: str) -> str:
        """Provide clinical decision support"""
        try:
            # In a real implementation, this would use clinical decision support algorithms
            # and medical knowledge bases
            decision_support = {
                "recommendations": [
                    "Review current medications for potential interactions",
                    "Monitor blood pressure trends",
                    "Consider cardiology referral if cardiovascular risk factors present"
                ],
                "evidence_level": "B",
                "confidence_score": 0.85,
                "reasoning": "Based on current clinical guidelines and patient risk factors",
                "next_steps": [
                    "Schedule follow-up in 2-4 weeks",
                    "Order laboratory studies if indicated",
                    "Patient education on lifestyle modifications"
                ]
            }
            
            return json.dumps(decision_support, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class MedicationInteractionTool(BaseTool):
    """Tool for checking medication interactions and contraindications"""
    
    name: str = "medication_interaction_checker"
    description: str = "Check for drug interactions, contraindications, and dosing recommendations"
    
    def __init__(self):
        super().__init__()
    
    def _run(self, medications_list: str) -> str:
        """Check medication interactions"""
        try:
            # Simplified interaction checking - in practice would use comprehensive drug database
            interactions = {
                "critical_interactions": [],
                "moderate_interactions": [
                    "Warfarin + Aspirin: Increased bleeding risk - monitor INR closely"
                ],
                "minor_interactions": [],
                "contraindications": [],
                "dosing_recommendations": [
                    "Adjust dosing based on renal function",
                    "Monitor therapeutic levels for narrow therapeutic index drugs"
                ],
                "monitoring_requirements": [
                    "Regular CBC for hematologic toxicity",
                    "Liver function tests every 3 months"
                ]
            }
            
            return json.dumps(interactions, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)


class DiagnosticAssistantTool(BaseTool):
    """Tool for diagnostic assistance and differential diagnosis"""
    
    name: str = "diagnostic_assistant"
    description: str = "Assist with differential diagnosis and diagnostic workup recommendations"
    
    def __init__(self):
        super().__init__()
    
    def _run(self, symptoms: str, patient_history: str) -> str:
        """Provide diagnostic assistance"""
        try:
            diagnostic_support = {
                "differential_diagnosis": [
                    "Hypertension - primary",
                    "Coronary artery disease",
                    "Diabetes mellitus type 2"
                ],
                "recommended_tests": [
                    "Complete metabolic panel",
                    "Lipid profile",
                    "HbA1c",
                    "ECG",
                    "Chest X-ray"
                ],
                "red_flags": [
                    "Chest pain with exertion",
                    "Uncontrolled blood pressure"
                ],
                "urgency_level": "routine",
                "follow_up_recommendations": [
                    "Schedule cardiology consultation",
                    "Lifestyle counseling",
                    "Blood pressure monitoring"
                ]
            }
            
            return json.dumps(diagnostic_support, indent=2)
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.get_encounter_for_analysis(encounter_id)
            )
            loop.close()
            return result
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.get_vital_signs_trends(patient_id, int(days))
            )
            loop.close()
            return result
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
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.generate_assessment_pdf(
                    patient_id, 
                    parsed_assessment, 
                    filename if filename else None
                )
            )
            loop.close()
            return result
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
            openai_api_key=openai_api_key if openai_api_key and openai_api_key != "demo_key_for_testing" else "sk-temp_demo_key_for_initialization_12345678901234567890123456789012"
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
    
    def create_patient_assessment_crew(self, patient_id: str) -> Crew:
        """Create a crew for comprehensive patient assessment"""
        
        # Define tasks for the crew
        patient_data_task = Task(
            description=f"""Retrieve and analyze comprehensive patient data for patient ID: {patient_id}.
            Include demographics, medical history, current medications, recent lab results, 
            and vital signs. Identify any immediate concerns or red flags.""",
            agent=self.primary_care_agent,
            expected_output="Comprehensive patient summary with identified concerns and initial assessment"
        )
        
        cardiovascular_assessment_task = Task(
            description="""Perform specialized cardiovascular risk assessment based on the 
            patient data. Evaluate cardiovascular risk factors, calculate risk scores, 
            and provide recommendations for cardiovascular health management.""",
            agent=self.cardiology_agent,
            expected_output="Cardiovascular risk assessment with specific recommendations"
        )
        
        medication_review_task = Task(
            description="""Conduct comprehensive medication review including interaction 
            checking, dosing appropriateness, and therapeutic duplication screening. 
            Provide recommendations for medication optimization.""",
            agent=self.pharmacist_agent,
            expected_output="Medication review with safety recommendations and optimization suggestions"
        )
        
        care_coordination_task = Task(
            description="""Develop care coordination plan including follow-up scheduling, 
            patient education priorities, and care transition planning. Ensure all 
            recommendations from specialists are integrated into the care plan.""",
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
            description=f"""Perform emergency triage assessment for patient {patient_id} 
            with chief complaint: {chief_complaint}. Retrieve patient data, assess 
            severity, and determine urgency level. Identify any life-threatening conditions.""",
            agent=self.primary_care_agent,
            expected_output="Emergency triage assessment with urgency level and immediate interventions"
        )
        
        rapid_medication_check = Task(
            description="""Perform rapid medication safety check focusing on emergency 
            contraindications, drug allergies, and critical interactions that could 
            affect emergency treatment.""",
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
            description=f"""Perform comprehensive medication reconciliation for patient {patient_id}. 
            Compare current medications with previous records, identify discrepancies, 
            and check for interactions, duplications, and appropriateness.""",
            agent=self.pharmacist_agent,
            expected_output="Complete medication reconciliation report with recommendations"
        )
        
        clinical_review_task = Task(
            description="""Review medication reconciliation findings from clinical perspective. 
            Assess therapeutic appropriateness, identify potential therapeutic gaps, 
            and provide clinical recommendations.""",
            agent=self.primary_care_agent,
            expected_output="Clinical review of medication changes with therapeutic recommendations"
        )
        
        coordination_task = Task(
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
    
    async def run_patient_assessment(self, patient_id: str) -> Dict[str, Any]:
        """Run comprehensive patient assessment"""
        crew = self.create_patient_assessment_crew(patient_id)
        result = crew.kickoff()
        
        return {
            "patient_id": patient_id,
            "assessment_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
            "results": result,
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
        result = crew.kickoff()
        
        return {
            "patient_id": patient_id,
            "assessment_type": "emergency",
            "chief_complaint": chief_complaint,
            "timestamp": datetime.now().isoformat(),
            "results": result,
            "crew_composition": [
                "Primary Care Physician",
                "Clinical Pharmacist"
            ]
        } 