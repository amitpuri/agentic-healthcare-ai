"""
Healthcare Data Models and Clinical Decision Support
Defines data structures for clinical workflows and AI agent interactions
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class Severity(str, Enum):
    """Clinical severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(str, Enum):
    """Task priority levels"""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class ClinicalSpecialty(str, Enum):
    """Medical specialties"""
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    PSYCHIATRY = "psychiatry"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    EMERGENCY = "emergency"
    INTERNAL_MEDICINE = "internal_medicine"
    SURGERY = "surgery"
    PEDIATRICS = "pediatrics"


class PatientDemographics(BaseModel):
    """Patient demographic information"""
    patient_id: str = Field(..., description="Unique patient identifier")
    name: str = Field(..., description="Patient full name")
    birth_date: date = Field(..., description="Date of birth")
    gender: Literal["male", "female", "other", "unknown"] = Field(..., description="Patient gender")
    age: Optional[int] = Field(None, description="Calculated age")
    address: Optional[str] = Field(None, description="Patient address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact information")
    
    @validator('age', always=True)
    def calculate_age(cls, v, values):
        if 'birth_date' in values:
            today = date.today()
            birth_date = values['birth_date']
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return v


class VitalSigns(BaseModel):
    """Patient vital signs"""
    timestamp: datetime = Field(default_factory=datetime.now)
    systolic_bp: Optional[int] = Field(None, description="Systolic blood pressure (mmHg)")
    diastolic_bp: Optional[int] = Field(None, description="Diastolic blood pressure (mmHg)")
    heart_rate: Optional[int] = Field(None, description="Heart rate (bpm)")
    respiratory_rate: Optional[int] = Field(None, description="Respiratory rate (breaths/min)")
    temperature: Optional[float] = Field(None, description="Body temperature (°C)")
    oxygen_saturation: Optional[float] = Field(None, description="Oxygen saturation (%)")
    pain_score: Optional[int] = Field(None, description="Pain score (0-10)")
    
    @validator('systolic_bp')
    def validate_systolic_bp(cls, v):
        if v is not None and (v < 70 or v > 250):
            raise ValueError("Systolic BP must be between 70-250 mmHg")
        return v
    
    @validator('diastolic_bp')
    def validate_diastolic_bp(cls, v):
        if v is not None and (v < 40 or v > 150):
            raise ValueError("Diastolic BP must be between 40-150 mmHg")
        return v
    
    @validator('heart_rate')
    def validate_heart_rate(cls, v):
        if v is not None and (v < 30 or v > 200):
            raise ValueError("Heart rate must be between 30-200 bpm")
        return v


class LabResult(BaseModel):
    """Laboratory test result"""
    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Name of the test")
    value: Union[str, float, int] = Field(..., description="Test result value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal reference range")
    abnormal_flag: Optional[str] = Field(None, description="Abnormal result flag")
    timestamp: datetime = Field(default_factory=datetime.now)
    status: Literal["preliminary", "final", "corrected", "cancelled"] = Field(default="final")


class Medication(BaseModel):
    """Medication information"""
    medication_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Medication name")
    dosage: str = Field(..., description="Dosage strength")
    route: str = Field(..., description="Route of administration")
    frequency: str = Field(..., description="Frequency of administration")
    start_date: datetime = Field(..., description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    prescriber: str = Field(..., description="Prescribing physician")
    indication: Optional[str] = Field(None, description="Indication for medication")
    status: Literal["active", "completed", "stopped", "suspended"] = Field(default="active")


class ClinicalCondition(BaseModel):
    """Clinical condition or diagnosis"""
    condition_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., description="ICD-10 or SNOMED code")
    display: str = Field(..., description="Human-readable condition name")
    severity: Severity = Field(..., description="Condition severity")
    onset_date: Optional[datetime] = Field(None, description="Date of onset")
    status: Literal["active", "resolved", "inactive"] = Field(default="active")
    notes: Optional[str] = Field(None, description="Additional clinical notes")


class ClinicalAssessment(BaseModel):
    """Clinical assessment and recommendations"""
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = Field(..., description="Patient identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    specialty: ClinicalSpecialty = Field(..., description="Medical specialty")
    
    # Assessment components
    chief_complaint: str = Field(..., description="Primary reason for visit")
    history_present_illness: str = Field(..., description="History of present illness")
    assessment: str = Field(..., description="Clinical assessment")
    plan: str = Field(..., description="Treatment plan")
    
    # Risk factors and scores
    risk_score: Optional[float] = Field(None, description="Calculated risk score (0-1)")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    follow_up: Optional[str] = Field(None, description="Follow-up instructions")
    priority: Priority = Field(default=Priority.ROUTINE, description="Assessment priority")


class ClinicalAlert(BaseModel):
    """Clinical alert or warning"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = Field(..., description="Patient identifier")
    alert_type: Literal["critical_value", "drug_interaction", "allergy", "duplicate_therapy", "dosage"] = Field(..., description="Type of alert")
    severity: Severity = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    details: Optional[str] = Field(None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.now)
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")


class PatientSummary(BaseModel):
    """Comprehensive patient summary"""
    demographics: PatientDemographics
    vital_signs: Optional[VitalSigns] = None
    active_conditions: List[ClinicalCondition] = Field(default_factory=list)
    current_medications: List[Medication] = Field(default_factory=list)
    recent_lab_results: List[LabResult] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    active_alerts: List[ClinicalAlert] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    @property
    def has_critical_alerts(self) -> bool:
        """Check if patient has any critical alerts"""
        return any(alert.severity == Severity.CRITICAL for alert in self.active_alerts)
    
    @property
    def medication_count(self) -> int:
        """Get count of active medications"""
        return len([med for med in self.current_medications if med.status == "active"])


class ClinicalDecisionSupport(BaseModel):
    """Clinical decision support recommendations"""
    patient_id: str = Field(..., description="Patient identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    recommendations: List[str] = Field(..., description="Clinical recommendations")
    evidence_level: Literal["A", "B", "C", "D"] = Field(..., description="Strength of evidence")
    confidence_score: float = Field(..., description="AI confidence score (0-1)")
    reasoning: str = Field(..., description="Explanation of reasoning")
    references: List[str] = Field(default_factory=list, description="Supporting references")


class ClinicalWorkflow(BaseModel):
    """Clinical workflow definition"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Workflow name")
    specialty: ClinicalSpecialty = Field(..., description="Medical specialty")
    steps: List[str] = Field(..., description="Workflow steps")
    triggers: List[str] = Field(..., description="Workflow triggers")
    outcomes: List[str] = Field(..., description="Expected outcomes")
    duration_estimate: Optional[int] = Field(None, description="Estimated duration in minutes")


class QualityMeasure(BaseModel):
    """Healthcare quality measure"""
    measure_id: str = Field(..., description="Quality measure identifier")
    name: str = Field(..., description="Measure name")
    description: str = Field(..., description="Measure description")
    numerator: int = Field(..., description="Numerator count")
    denominator: int = Field(..., description="Denominator count")
    percentage: float = Field(..., description="Calculated percentage")
    target: Optional[float] = Field(None, description="Target percentage")
    period: str = Field(..., description="Measurement period")
    
    @validator('percentage', always=True)
    def calculate_percentage(cls, v, values):
        if 'numerator' in values and 'denominator' in values and values['denominator'] > 0:
            return (values['numerator'] / values['denominator']) * 100
        return 0.0


class ClinicalTrial(BaseModel):
    """Clinical trial matching information"""
    trial_id: str = Field(..., description="Clinical trial identifier")
    title: str = Field(..., description="Trial title")
    condition: str = Field(..., description="Target condition")
    phase: Literal["I", "II", "III", "IV"] = Field(..., description="Trial phase")
    enrollment_status: Literal["recruiting", "active", "completed", "suspended"] = Field(..., description="Enrollment status")
    inclusion_criteria: List[str] = Field(..., description="Inclusion criteria")
    exclusion_criteria: List[str] = Field(..., description="Exclusion criteria")
    location: str = Field(..., description="Trial location")
    contact_info: str = Field(..., description="Contact information")
    match_score: Optional[float] = Field(None, description="Patient match score (0-1)")


class HealthcareMetrics(BaseModel):
    """Healthcare performance metrics"""
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Efficiency metrics
    average_wait_time: Optional[float] = Field(None, description="Average wait time in minutes")
    bed_occupancy_rate: Optional[float] = Field(None, description="Bed occupancy percentage")
    length_of_stay: Optional[float] = Field(None, description="Average length of stay in days")
    
    # Quality metrics
    readmission_rate: Optional[float] = Field(None, description="30-day readmission rate")
    infection_rate: Optional[float] = Field(None, description="Healthcare-associated infection rate")
    mortality_rate: Optional[float] = Field(None, description="Mortality rate")
    
    # Patient satisfaction
    patient_satisfaction_score: Optional[float] = Field(None, description="Patient satisfaction score (0-10)")
    physician_satisfaction_score: Optional[float] = Field(None, description="Physician satisfaction score (0-10)")
    
    # Financial metrics
    cost_per_case: Optional[float] = Field(None, description="Average cost per case")
    revenue_per_patient: Optional[float] = Field(None, description="Revenue per patient")


# Utility functions for clinical calculations
class ClinicalCalculations:
    """Clinical calculation utilities"""
    
    @staticmethod
    def calculate_bmi(weight_kg: float, height_m: float) -> float:
        """Calculate Body Mass Index"""
        return weight_kg / (height_m ** 2)
    
    @staticmethod
    def calculate_egfr(creatinine: float, age: int, gender: str, race: str = "other") -> float:
        """Calculate estimated Glomerular Filtration Rate using CKD-EPI equation"""
        # Simplified CKD-EPI equation
        k = 0.7 if gender.lower() == "female" else 0.9
        alpha = -0.329 if gender.lower() == "female" else -0.411
        gender_factor = 1.018 if gender.lower() == "female" else 1.0
        race_factor = 1.159 if race.lower() == "african_american" else 1.0
        
        egfr = 141 * min(creatinine/k, 1)**alpha * max(creatinine/k, 1)**(-1.209) * 0.993**age * gender_factor * race_factor
        return round(egfr, 1)
    
    @staticmethod
    def calculate_cardiovascular_risk(
        age: int, 
        gender: str, 
        total_cholesterol: float, 
        hdl_cholesterol: float, 
        systolic_bp: int,
        smoker: bool = False,
        diabetes: bool = False
    ) -> float:
        """Calculate 10-year cardiovascular risk (simplified Framingham Risk Score)"""
        # This is a simplified version - actual implementation would use full Framingham equations
        risk_score = 0
        
        # Age points
        if gender.lower() == "male":
            if age >= 70: risk_score += 5
            elif age >= 60: risk_score += 4
            elif age >= 50: risk_score += 3
            elif age >= 40: risk_score += 2
        else:  # female
            if age >= 70: risk_score += 4
            elif age >= 60: risk_score += 3
            elif age >= 50: risk_score += 2
            elif age >= 40: risk_score += 1
        
        # Cholesterol ratio
        chol_ratio = total_cholesterol / hdl_cholesterol
        if chol_ratio >= 7: risk_score += 3
        elif chol_ratio >= 5: risk_score += 2
        elif chol_ratio >= 4: risk_score += 1
        
        # Blood pressure
        if systolic_bp >= 160: risk_score += 3
        elif systolic_bp >= 140: risk_score += 2
        elif systolic_bp >= 120: risk_score += 1
        
        # Risk factors
        if smoker: risk_score += 2
        if diabetes: risk_score += 2
        
        # Convert to percentage (simplified mapping)
        risk_percentage = min(risk_score * 2, 40)  # Cap at 40%
        return risk_percentage 