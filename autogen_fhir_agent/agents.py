"""
Healthcare AI Agents using Autogen Framework
Implements multi-agent conversational AI system for healthcare with FHIR integration
"""

import autogen
from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager
from typing import Dict, List, Any, Optional, Callable
import json
import asyncio
import logging
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

logger = logging.getLogger(__name__)


class HealthcareFunctionRegistry:
    """Registry of healthcare-specific functions for Autogen agents with MCP integration"""
    
    def __init__(self, fhir_client: FHIRClient, mcp_url: str = None):
        self.fhir_client = fhir_client
        self.fhir_tools = FHIRToolsForAgents(mcp_url)
        self.pdf_generator = PatientAssessmentReport()
    
    def get_patient_data(self, patient_id: str) -> str:
        """Retrieve comprehensive patient data from FHIR server"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            patient_data = loop.run_until_complete(
                self.fhir_client.get_comprehensive_patient_data(patient_id)
            )
            loop.close()
            
            return json.dumps({
                "patient_id": patient_id,
                "demographics": {
                    "name": str(patient_data["patient"].name[0]) if patient_data["patient"].name else "",
                    "birth_date": str(patient_data["patient"].birthDate) if patient_data["patient"].birthDate else None,
                    "gender": patient_data["patient"].gender,
                    "age": self._calculate_age(patient_data["patient"].birthDate) if patient_data["patient"].birthDate else None
                },
                "conditions": [self._format_condition(cond) for cond in patient_data["conditions"][:5]],
                "medications": [self._format_medication(med) for med in patient_data["medications"][:5]],
                "vital_signs": [self._format_observation(obs) for obs in patient_data["observations"][:10] 
                              if self._is_vital_sign(obs)],
                "lab_results": [self._format_observation(obs) for obs in patient_data["observations"][:10] 
                              if not self._is_vital_sign(obs)]
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to retrieve patient data: {str(e)}"})
    
    def check_drug_interactions(self, medications: List[str]) -> str:
        """Check for drug interactions among current medications"""
        try:
            # Simplified interaction checking
            interactions = []
            warnings = []
            
            # Common interaction patterns
            blood_thinners = ["warfarin", "heparin", "aspirin", "clopidogrel"]
            nsaids = ["ibuprofen", "naproxen", "diclofenac", "celecoxib"]
            ace_inhibitors = ["lisinopril", "enalapril", "captopril"]
            
            med_lower = [med.lower() for med in medications]
            
            # Check blood thinner + NSAID interaction
            has_blood_thinner = any(bt in " ".join(med_lower) for bt in blood_thinners)
            has_nsaid = any(nsaid in " ".join(med_lower) for nsaid in nsaids)
            
            if has_blood_thinner and has_nsaid:
                interactions.append({
                    "severity": "major",
                    "interaction": "Blood thinner + NSAID",
                    "risk": "Increased bleeding risk",
                    "recommendation": "Monitor INR closely, consider gastroprotection"
                })
            
            # Check ACE inhibitor + potassium
            has_ace = any(ace in " ".join(med_lower) for ace in ace_inhibitors)
            has_potassium = "potassium" in " ".join(med_lower)
            
            if has_ace and has_potassium:
                warnings.append({
                    "severity": "moderate",
                    "interaction": "ACE inhibitor + Potassium supplement",
                    "risk": "Hyperkalemia",
                    "recommendation": "Monitor serum potassium levels"
                })
            
            return json.dumps({
                "total_medications": len(medications),
                "major_interactions": interactions,
                "warnings": warnings,
                "recommendations": [
                    "Review medication list with pharmacist",
                    "Monitor for signs of adverse effects",
                    "Consider alternative medications if interactions present"
                ]
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to check interactions: {str(e)}"})
    
    def calculate_risk_scores(self, patient_data: Dict[str, Any]) -> str:
        """Calculate various clinical risk scores"""
        try:
            risk_scores = {}
            
            # Simplified cardiovascular risk calculation
            age = patient_data.get("age", 0)
            gender = patient_data.get("gender", "unknown")
            
            # Basic CV risk factors
            cv_risk = 0
            if age > 65: cv_risk += 2
            elif age > 55: cv_risk += 1
            
            if gender.lower() == "male": cv_risk += 1
            
            # Check for diabetes, hypertension, smoking in conditions
            conditions = patient_data.get("conditions", [])
            condition_text = " ".join([str(cond) for cond in conditions]).lower()
            
            if "diabetes" in condition_text: cv_risk += 2
            if "hypertension" in condition_text: cv_risk += 1
            if "smoking" in condition_text or "tobacco" in condition_text: cv_risk += 2
            
            risk_scores["cardiovascular_risk"] = {
                "score": cv_risk,
                "risk_level": "high" if cv_risk >= 5 else "moderate" if cv_risk >= 3 else "low",
                "recommendations": [
                    "Lifestyle counseling",
                    "Regular monitoring",
                    "Consider statin therapy if high risk"
                ]
            }
            
            # Fall risk assessment (simplified)
            fall_risk = 0
            if age > 75: fall_risk += 2
            elif age > 65: fall_risk += 1
            
            medications = patient_data.get("medications", [])
            med_text = " ".join([str(med) for med in medications]).lower()
            
            if any(med in med_text for med in ["sedative", "benzodiazepine", "opioid"]): fall_risk += 2
            if "hypertension" in condition_text: fall_risk += 1
            
            risk_scores["fall_risk"] = {
                "score": fall_risk,
                "risk_level": "high" if fall_risk >= 4 else "moderate" if fall_risk >= 2 else "low",
                "recommendations": [
                    "Home safety evaluation",
                    "Physical therapy assessment",
                    "Medication review for sedating effects"
                ]
            }
            
            return json.dumps(risk_scores, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to calculate risk scores: {str(e)}"})
    
    def generate_care_plan(self, assessment_data: Dict[str, Any]) -> str:
        """Generate a comprehensive care plan based on assessment"""
        try:
            care_plan = {
                "patient_id": assessment_data.get("patient_id"),
                "assessment_date": datetime.now().isoformat(),
                "primary_diagnoses": [],
                "goals": [],
                "interventions": [],
                "monitoring": [],
                "follow_up": [],
                "patient_education": []
            }
            
            # Extract conditions and generate goals
            conditions = assessment_data.get("conditions", [])
            for condition in conditions:
                if "diabetes" in str(condition).lower():
                    care_plan["goals"].append("Achieve HbA1c < 7%")
                    care_plan["interventions"].append("Diabetes medication optimization")
                    care_plan["monitoring"].append("HbA1c every 3-6 months")
                    care_plan["patient_education"].append("Diabetes self-management education")
                
                if "hypertension" in str(condition).lower():
                    care_plan["goals"].append("Blood pressure < 140/90 mmHg")
                    care_plan["interventions"].append("Antihypertensive therapy adjustment")
                    care_plan["monitoring"].append("Blood pressure monitoring")
                    care_plan["patient_education"].append("DASH diet counseling")
            
            # General recommendations
            care_plan["interventions"].extend([
                "Annual wellness visit",
                "Preventive care screenings as appropriate",
                "Medication reconciliation"
            ])
            
            care_plan["follow_up"].extend([
                "Primary care follow-up in 3-6 months",
                "Specialist referrals as indicated",
                "Emergency contact instructions provided"
            ])
            
            return json.dumps(care_plan, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to generate care plan: {str(e)}"})
    
    def get_patient_comprehensive_assessment(self, patient_id: str) -> str:
        """Get comprehensive patient data using MCP FHIR tools for AI assessment"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.get_patient_for_assessment(patient_id)
            )
            loop.close()
            return result
        except Exception as e:
            return json.dumps({"error": f"Failed to get patient assessment data: {str(e)}"})
    
    def get_encounter_analysis(self, encounter_id: str) -> str:
        """Get encounter details for AI analysis using MCP FHIR tools"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.get_encounter_for_analysis(encounter_id)
            )
            loop.close()
            return result
        except Exception as e:
            return json.dumps({"error": f"Failed to get encounter analysis: {str(e)}"})
    
    def get_vital_signs_trends(self, patient_id: str, days: int = 30) -> str:
        """Get vital signs trends for AI analysis using MCP FHIR tools"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.get_vital_signs_trends(patient_id, days)
            )
            loop.close()
            return result
        except Exception as e:
            return json.dumps({"error": f"Failed to get vital signs trends: {str(e)}"})
    
    def generate_patient_assessment_pdf(self, patient_id: str, assessment_data: str = None, filename: str = None) -> str:
        """Generate comprehensive patient assessment PDF report"""
        try:
            # Parse assessment data if provided as JSON string
            parsed_assessment = None
            if assessment_data:
                try:
                    parsed_assessment = json.loads(assessment_data)
                except json.JSONDecodeError:
                    # If not JSON, create a simple assessment structure
                    parsed_assessment = {"ai_assessment": assessment_data}
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.fhir_tools.generate_assessment_pdf(patient_id, parsed_assessment, filename)
            )
            loop.close()
            return result
        except Exception as e:
            return json.dumps({"error": f"Failed to generate assessment PDF: {str(e)}"})
    
    def run_clinical_decision_support(self, patient_data: str, clinical_context: str = "") -> str:
        """Run clinical decision support using patient data and context"""
        try:
            # Parse patient data
            patient_info = json.loads(patient_data)
            
            # Generate clinical recommendations
            recommendations = []
            alerts = []
            
            # Analyze conditions for drug interactions
            conditions = patient_info.get("conditions", [])
            medications = patient_info.get("medications", [])
            
            # Check for diabetes management
            if any("diabetes" in str(cond).lower() for cond in conditions):
                recommendations.append({
                    "category": "diabetes_management",
                    "priority": "high",
                    "recommendation": "Monitor HbA1c every 3-6 months, target <7%"
                })
                
                # Check for diabetic complications
                if any("nephropathy" in str(cond).lower() or "kidney" in str(cond).lower() for cond in conditions):
                    alerts.append({
                        "severity": "high",
                        "alert": "Diabetic nephropathy detected - consider ACE inhibitor therapy"
                    })
            
            # Check for cardiovascular risk
            cv_risk_factors = ["hypertension", "hyperlipidemia", "smoking", "obesity"]
            cv_count = sum(1 for rf in cv_risk_factors if any(rf in str(cond).lower() for cond in conditions))
            
            if cv_count >= 2:
                recommendations.append({
                    "category": "cardiovascular_risk",
                    "priority": "high",
                    "recommendation": "Consider statin therapy and lifestyle counseling"
                })
            
            # Check medication interactions
            interaction_result = self.check_drug_interactions([str(med) for med in medications])
            interaction_data = json.loads(interaction_result)
            
            if interaction_data.get("major_interactions"):
                for interaction in interaction_data["major_interactions"]:
                    alerts.append({
                        "severity": interaction["severity"],
                        "alert": f"Drug interaction: {interaction['interaction']} - {interaction['risk']}"
                    })
            
            return json.dumps({
                "clinical_decision_support": {
                    "recommendations": recommendations,
                    "alerts": alerts,
                    "assessment_context": clinical_context,
                    "timestamp": datetime.now().isoformat()
                }
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to run clinical decision support: {str(e)}"})
    
    def _calculate_age(self, birth_date) -> int:
        """Calculate age from birth date"""
        from datetime import date
        if not birth_date:
            return 0
        
        try:
            birth = date.fromisoformat(str(birth_date))
            today = date.today()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return 0
    
    def _format_condition(self, condition) -> Dict[str, Any]:
        """Format FHIR condition for display"""
        return {
            "code": condition.code.coding[0].code if condition.code and condition.code.coding else "",
            "display": condition.code.text or (condition.code.coding[0].display if condition.code and condition.code.coding else ""),
            "status": condition.clinicalStatus.coding[0].code if condition.clinicalStatus and condition.clinicalStatus.coding else ""
        }
    
    def _format_medication(self, medication) -> Dict[str, Any]:
        """Format FHIR medication for display"""
        return {
            "medication": medication.medicationCodeableConcept.text if medication.medicationCodeableConcept else "",
            "status": medication.status,
            "dosage": str(medication.dosageInstruction[0]) if medication.dosageInstruction else ""
        }
    
    def _format_observation(self, observation) -> Dict[str, Any]:
        """Format FHIR observation for display"""
        return {
            "code": observation.code.coding[0].code if observation.code and observation.code.coding else "",
            "display": observation.code.text or (observation.code.coding[0].display if observation.code and observation.code.coding else ""),
            "value": str(observation.value) if hasattr(observation, 'value') and observation.value else "",
            "date": str(observation.effectiveDateTime) if observation.effectiveDateTime else ""
        }
    
    def _is_vital_sign(self, observation) -> bool:
        """Check if observation is a vital sign"""
        vital_codes = ["8480-6", "8462-4", "8867-4", "59408-5", "8310-5", "2708-6"]  # Common vital sign LOINC codes
        if observation.code and observation.code.coding:
            return any(coding.code in vital_codes for coding in observation.code.coding)
        return False


class HealthcareAutogenSystem:
    """Multi-agent system for healthcare using Autogen"""

    def __init__(self, openai_api_key: str, fhir_config: FHIRConfig, mcp_url: str = None):
        """Initialize the healthcare agent system"""
        self.fhir_client = FHIRClient(fhir_config)
        self.function_registry = HealthcareFunctionRegistry(self.fhir_client, mcp_url)
        self.config_list = [{"model": "gpt-4", "api_key": openai_api_key}]
        
        self.primary_care_agent = None
        self.cardiologist_agent = None
        self.pharmacist_agent = None
        self.nurse_coordinator_agent = None
        self.emergency_agent = None
        self.user_proxy = None
        
        self.agents = self._create_agents()

    def get_agents_for_scenario(self, scenario_type: str) -> Dict[str, ConversableAgent]:
        """Get the relevant agents for a given scenario."""
        if scenario_type == "emergency_assessment":
            return {
                "emergency_agent": self.agents["emergency_agent"],
                "nurse_coordinator_agent": self.agents["nurse_coordinator_agent"],
                "user_proxy": self.agents["user_proxy"]
            }
        return self.agents

    def _create_agents(self) -> Dict[str, ConversableAgent]:
        """Create all healthcare agents"""
        # Primary Care Physician Agent
        self.primary_care_agent = ConversableAgent(
            name="PrimaryCarePhysician",
            system_message="""You are an experienced primary care physician with expertise in 
            comprehensive patient assessment, preventive care, and care coordination. Your role is to:
            1. Conduct thorough patient evaluations
            2. Identify and prioritize health issues
            3. Coordinate care with specialists
            4. Ensure continuity of care
            5. Provide evidence-based recommendations
            
            Always consider the patient's complete medical history, current medications, and 
            psychosocial factors when making recommendations. Use clinical guidelines and 
            evidence-based medicine in your assessments.""",
            llm_config={"config_list": self.config_list},
            function_map={
                "get_patient_data": self.function_registry.get_patient_data,
                "get_patient_comprehensive_assessment": self.function_registry.get_patient_comprehensive_assessment,
                "get_vital_signs_trends": self.function_registry.get_vital_signs_trends,
                "calculate_risk_scores": self.function_registry.calculate_risk_scores,
                "generate_care_plan": self.function_registry.generate_care_plan,
                "generate_patient_assessment_pdf": self.function_registry.generate_patient_assessment_pdf,
                "run_clinical_decision_support": self.function_registry.run_clinical_decision_support
            }
        )
        
        # Cardiologist Agent
        self.cardiologist_agent = ConversableAgent(
            name="Cardiologist",
            system_message="""You are a board-certified cardiologist specializing in cardiovascular 
            disease prevention, diagnosis, and treatment. Your expertise includes:
            1. Cardiovascular risk stratification
            2. Heart disease diagnosis and management
            3. Hypertension management
            4. Lipid disorders
            5. Heart failure management
            
            Focus on evidence-based cardiovascular care, risk factor modification, and 
            appropriate use of cardiac interventions. Consider ACC/AHA guidelines in your recommendations.""",
            llm_config={"config_list": self.config_list},
            function_map={
                "get_patient_data": self.function_registry.get_patient_data,
                "calculate_risk_scores": self.function_registry.calculate_risk_scores
            }
        )
        
        # Clinical Pharmacist Agent
        self.pharmacist_agent = ConversableAgent(
            name="ClinicalPharmacist",
            system_message="""You are a clinical pharmacist with expertise in medication therapy 
            management, drug interactions, and pharmaceutical care. Your responsibilities include:
            1. Medication reconciliation and review
            2. Drug interaction screening
            3. Dosing optimization
            4. Adverse effect monitoring
            5. Patient medication education
            
            Always prioritize patient safety, consider renal/hepatic function in dosing, 
            and provide cost-effective therapeutic alternatives when appropriate.""",
            llm_config={"config_list": self.config_list},
            function_map={
                "get_patient_data": self.function_registry.get_patient_data,
                "get_patient_comprehensive_assessment": self.function_registry.get_patient_comprehensive_assessment,
                "get_encounter_analysis": self.function_registry.get_encounter_analysis,
                "check_drug_interactions": self.function_registry.check_drug_interactions,
                "run_clinical_decision_support": self.function_registry.run_clinical_decision_support
            }
        )
        
        # Nurse Care Coordinator Agent
        self.nurse_coordinator_agent = ConversableAgent(
            name="NurseCoordinator",
            system_message="""You are an experienced registered nurse specializing in care coordination 
            and patient education. Your role encompasses:
            1. Care transition management
            2. Patient and family education
            3. Discharge planning
            4. Follow-up coordination
            5. Resource identification and referral
            
            Focus on ensuring patients understand their care plans, have appropriate follow-up 
            scheduled, and can access necessary resources for optimal health outcomes.""",
            llm_config={"config_list": self.config_list},
            function_map={
                "get_patient_data": self.function_registry.get_patient_data,
                "generate_care_plan": self.function_registry.generate_care_plan
            }
        )
        
        # Emergency Medicine Agent
        self.emergency_agent = ConversableAgent(
            name="EmergencyPhysician",
            system_message="""You are an emergency medicine physician with expertise in acute care, 
            rapid assessment, and emergency interventions. Your focus areas include:
            1. Rapid triage and assessment
            2. Emergency stabilization
            3. Critical decision making under time pressure
            4. Risk stratification for disposition
            5. Emergency medication management
            
            Prioritize life-threatening conditions, use systematic approaches like ABCDE assessment, 
            and ensure appropriate disposition and follow-up care.""",
            llm_config={"config_list": self.config_list},
            function_map={
                "get_patient_data": self.function_registry.get_patient_data,
                "calculate_risk_scores": self.function_registry.calculate_risk_scores
            }
        )
        
        # User Proxy Agent for human interaction
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            code_execution_config=False
        )
        
        return {
            "primary_care_agent": self.primary_care_agent,
            "cardiologist_agent": self.cardiologist_agent,
            "pharmacist_agent": self.pharmacist_agent,
            "nurse_coordinator_agent": self.nurse_coordinator_agent,
            "emergency_agent": self.emergency_agent,
            "user_proxy": self.user_proxy
        }

    def create_comprehensive_assessment_chat(self, patient_id: str) -> GroupChat:
        """Create a group chat for comprehensive patient assessment"""
        agents = [
            self.user_proxy,
            self.primary_care_agent,
            self.cardiologist_agent,
            self.pharmacist_agent,
            self.nurse_coordinator_agent
        ]
        
        # Use round_robin speaker selection for now to avoid AutoGen framework issues
        # Custom speaker selection can be implemented later when framework is more stable
        
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=10,
            speaker_selection_method="round_robin"
        )
        
        return group_chat
    
    def create_emergency_assessment_chat(self, patient_id: str, chief_complaint: str) -> GroupChat:
        """Create group chat for emergency patient assessment"""
        
        agents = [
            self.user_proxy,
            self.emergency_agent,
            self.pharmacist_agent
        ]
        
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=6,
            speaker_selection_method="round_robin"
        )
        
        return group_chat
    
    def create_medication_review_chat(self, patient_id: str) -> GroupChat:
        """Create a group chat for medication reconciliation"""
        return GroupChat(
            agents=[self.pharmacist_agent, self.primary_care_agent, self.user_proxy],
            messages=[],
            max_round=15
        )

    async def execute_scenario(self, scenario_type: str, patient_id: str, task_description: str) -> Dict[str, Any]:
        """
        Execute a scenario based on its type.
        This centralizes the logic for running different kinds of assessments.
        """
        if scenario_type == "comprehensive_assessment":
            return await self.run_comprehensive_assessment(patient_id)
        elif scenario_type == "emergency_assessment":
            # Extract chief complaint from task description for emergency
            chief_complaint = "Emergency assessment"
            if "chief complaint" in task_description.lower():
                chief_complaint = task_description.split("Chief complaint:")[1].split(".")[0].strip()
            return await self.run_emergency_assessment(patient_id, chief_complaint)
        elif scenario_type == "medication_reconciliation":
            return await self.run_medication_reconciliation(patient_id)
        else:
            raise ValueError(f"Unsupported scenario type: {scenario_type}")

    async def run_comprehensive_assessment(self, patient_id: str) -> Dict[str, Any]:
        """Run a comprehensive patient assessment scenario"""
        groupchat = self.create_comprehensive_assessment_chat(patient_id)
        manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": self.config_list})
        
        # Start the conversation
        initial_message = f"""Please conduct a comprehensive assessment for patient ID: {patient_id}.
        
        Primary Care Physician: Start by retrieving and reviewing the patient's complete medical history, 
        current medications, recent lab results, and vital signs. Identify key health issues and risk factors.
        
        Cardiologist: Focus on cardiovascular risk assessment and any cardiac-related concerns.
        
        Clinical Pharmacist: Review all medications for interactions, appropriateness, and safety.
        
        Nurse Coordinator: Develop care coordination plan and patient education priorities.
        
        Please provide your assessments and recommendations."""
        
        conversation_result = self.user_proxy.initiate_chat(
            manager,
            message=initial_message,
            clear_history=True
        )
        
        return {
            "patient_id": patient_id,
            "assessment_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
            "conversation_history": conversation_result.chat_history,
            "participating_agents": ["PrimaryCarePhysician", "Cardiologist", "ClinicalPharmacist", "NurseCoordinator"],
            "summary": self._extract_conversation_summary(conversation_result.chat_history)
        }
    
    async def run_emergency_assessment(self, patient_id: str, chief_complaint: str) -> Dict[str, Any]:
        """Run emergency assessment using multi-agent conversation"""
        
        group_chat = self.create_emergency_assessment_chat(patient_id, chief_complaint)
        manager = GroupChatManager(groupchat=group_chat, llm_config={"config_list": self.config_list})
        
        initial_message = f"""EMERGENCY ASSESSMENT NEEDED for patient ID: {patient_id}
        Chief Complaint: {chief_complaint}
        
        Emergency Physician: Conduct rapid triage assessment, retrieve patient data, assess severity, 
        and determine immediate interventions needed. Consider life-threatening conditions.
        
        Clinical Pharmacist: Perform urgent medication safety check for emergency contraindications 
        and critical drug interactions that could affect treatment.
        
        Time is critical - provide rapid, focused assessments."""
        
        conversation_result = self.user_proxy.initiate_chat(
            manager,
            message=initial_message,
            clear_history=True
        )
        
        return {
            "patient_id": patient_id,
            "assessment_type": "emergency",
            "chief_complaint": chief_complaint,
            "timestamp": datetime.now().isoformat(),
            "conversation_history": conversation_result.chat_history,
            "participating_agents": ["EmergencyPhysician", "ClinicalPharmacist"],
            "summary": self._extract_conversation_summary(conversation_result.chat_history)
        }
    
    async def run_medication_reconciliation(self, patient_id: str) -> Dict[str, Any]:
        """Run medication reconciliation using multi-agent conversation"""
        
        group_chat = self.create_medication_review_chat(patient_id)
        manager = GroupChatManager(groupchat=group_chat, llm_config={"config_list": self.config_list})
        
        initial_message = f"""Please conduct medication reconciliation for patient ID: {patient_id}.
        
        Clinical Pharmacist: Lead the medication review process. Retrieve current medications, 
        check for interactions, duplications, and appropriateness. Identify any safety concerns.
        
        Primary Care Physician: Review medications from clinical perspective and assess 
        therapeutic appropriateness and potential therapeutic gaps.
        
        Nurse Coordinator: Plan implementation of any medication changes including patient 
        education and follow-up coordination.
        
        Focus on medication safety and optimization."""
        
        conversation_result = self.user_proxy.initiate_chat(
            manager,
            message=initial_message,
            clear_history=True
        )
        
        return {
            "patient_id": patient_id,
            "assessment_type": "medication_reconciliation",
            "timestamp": datetime.now().isoformat(),
            "conversation_history": conversation_result.chat_history,
            "participating_agents": ["ClinicalPharmacist", "PrimaryCarePhysician", "NurseCoordinator"],
            "summary": self._extract_conversation_summary(conversation_result.chat_history)
        }
    
    def _extract_conversation_summary(self, chat_history: List[Dict]) -> Dict[str, Any]:
        """Extract key findings and recommendations from conversation history"""
        summary = {
            "key_findings": [],
            "recommendations": [],
            "action_items": [],
            "follow_up_needed": [],
            "alerts": []
        }
        
        # Simple extraction logic - in production would use more sophisticated NLP
        for message in chat_history:
            content = message.get("content", "").lower()
            
            if "recommendation" in content or "recommend" in content:
                summary["recommendations"].append(message.get("content", ""))
            
            if "follow" in content and "up" in content:
                summary["follow_up_needed"].append(message.get("content", ""))
            
            if "urgent" in content or "critical" in content or "immediate" in content:
                summary["alerts"].append(message.get("content", ""))
        
        return summary 
