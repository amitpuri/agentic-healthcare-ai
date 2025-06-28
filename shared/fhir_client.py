"""
FHIR Client for Healthcare AI Agents
Handles FHIR resource management, SMART on FHIR authentication, and data validation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

# Try to import FHIR resources with fallback
try:
    from fhir.resources import Bundle, Patient, Observation, Condition, MedicationRequest, Encounter
    from fhir.resources.fhirtypes import DateTime
    FHIR_AVAILABLE = True
except ImportError:
    # Fallback: create simple placeholder classes
    FHIR_AVAILABLE = False
    
    class Bundle(BaseModel):
        entry: list = []
        
    class Patient(BaseModel):
        id: str = ""
        
    class Observation(BaseModel):
        id: str = ""
        
    class Condition(BaseModel):
        id: str = ""
        
    class MedicationRequest(BaseModel):
        id: str = ""
        
    class Encounter(BaseModel):
        id: str = ""
                
    DateTime = str

# Try to import JWT with fallback
try:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    # Create dummy modules for fallback
    class DummyJWT:
        @staticmethod
        def encode(*args, **kwargs):
            return "dummy_token"
        
        @staticmethod
        def decode(*args, **kwargs):
            return {"sub": "dummy_user"}
    
    jwt = DummyJWT()
    serialization = None
    rsa = None


class FHIRConfig(BaseModel):
    """Configuration for FHIR server connection"""
    base_url: str = Field(..., description="FHIR server base URL")
    client_id: str = Field(..., description="SMART on FHIR client ID")
    client_secret: Optional[str] = Field(None, description="Client secret for confidential clients")
    scopes: List[str] = Field(default=["patient/*.read", "user/*.read"], description="SMART scopes")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class SMARTAuthenticator:
    """SMART on FHIR authentication handler"""
    
    def __init__(self, config: FHIRConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
    async def get_well_known_configuration(self) -> Dict[str, Any]:
        """Retrieve SMART configuration from .well-known endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                urljoin(self.config.base_url, ".well-known/smart_configuration"),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def authenticate(self) -> str:
        """Perform SMART on FHIR authentication flow"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
            
        smart_config = await self.get_well_known_configuration()
        token_endpoint = smart_config.get("token_endpoint")
        
        if not token_endpoint:
            raise ValueError("Token endpoint not found in SMART configuration")
        
        # Client credentials flow for backend services
        token_data = {
            "grant_type": "client_credentials",
            "scope": " ".join(self.config.scopes),
            "client_id": self.config.client_id
        }
        
        if self.config.client_secret:
            token_data["client_secret"] = self.config.client_secret
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            token_response = response.json()
            self.access_token = token_response["access_token"]
            expires_in = token_response.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            return self.access_token


class FHIRClient:
    """Comprehensive FHIR client with authentication and error handling"""
    
    def __init__(self, config: FHIRConfig):
        self.config = config
        self.authenticator = SMARTAuthenticator(config)
        self.logger = logging.getLogger(__name__)
        
    async def _get_headers(self) -> Dict[str, str]:
        """Get authenticated headers for FHIR requests"""
        token = await self.authenticator.authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated FHIR request with retry logic"""
        url = urljoin(self.config.base_url, endpoint)
        headers = await self._get_headers()
        
        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params,
                        timeout=self.config.timeout
                    )
                    response.raise_for_status()
                    return response.json()
                    
            except httpx.HTTPError as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def get_patient(self, patient_id: str) -> Patient:
        """Retrieve patient by ID"""
        data = await self._make_request("GET", f"Patient/{patient_id}")
        return Patient(**data)
    
    async def search_patients(self, **params) -> List[Patient]:
        """Search for patients with given parameters"""
        data = await self._make_request("GET", "Patient", params=params)
        bundle = Bundle(**data)
        
        patients = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource and entry.resource.resource_type == "Patient":
                    patients.append(Patient(**entry.resource.dict()))
        return patients
    
    async def get_patient_observations(self, patient_id: str) -> List[Observation]:
        """Get all observations for a patient"""
        params = {"patient": patient_id, "_sort": "-date"}
        data = await self._make_request("GET", "Observation", params=params)
        bundle = Bundle(**data)
        
        observations = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource and entry.resource.resource_type == "Observation":
                    observations.append(Observation(**entry.resource.dict()))
        return observations
    
    async def get_patient_conditions(self, patient_id: str) -> List[Condition]:
        """Get all conditions for a patient"""
        params = {"patient": patient_id, "_sort": "-date"}
        data = await self._make_request("GET", "Condition", params=params)
        bundle = Bundle(**data)
        
        conditions = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource and entry.resource.resource_type == "Condition":
                    conditions.append(Condition(**entry.resource.dict()))
        return conditions
    
    async def get_patient_medications(self, patient_id: str) -> List[MedicationRequest]:
        """Get all medication requests for a patient"""
        params = {"patient": patient_id, "_sort": "-date"}
        data = await self._make_request("GET", "MedicationRequest", params=params)
        bundle = Bundle(**data)
        
        medications = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource and entry.resource.resource_type == "MedicationRequest":
                    medications.append(MedicationRequest(**entry.resource.dict()))
        return medications
    
    async def get_patient_encounters(self, patient_id: str) -> List[Encounter]:
        """Get all encounters for a patient"""
        params = {"patient": patient_id, "_sort": "-date"}
        data = await self._make_request("GET", "Encounter", params=params)
        bundle = Bundle(**data)
        
        encounters = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource and entry.resource.resource_type == "Encounter":
                    encounters.append(Encounter(**entry.resource.dict()))
        return encounters
    
    async def create_observation(self, observation_data: Dict[str, Any]) -> Observation:
        """Create a new observation"""
        data = await self._make_request("POST", "Observation", data=observation_data)
        return Observation(**data)
    
    async def update_patient(self, patient_id: str, patient_data: Dict[str, Any]) -> Patient:
        """Update patient information"""
        data = await self._make_request("PUT", f"Patient/{patient_id}", data=patient_data)
        return Patient(**data)
    
    async def get_comprehensive_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient data including all related resources"""
        patient_data = {}
        
        # Fetch all patient-related data concurrently
        patient_task = self.get_patient(patient_id)
        observations_task = self.get_patient_observations(patient_id)
        conditions_task = self.get_patient_conditions(patient_id)
        medications_task = self.get_patient_medications(patient_id)
        encounters_task = self.get_patient_encounters(patient_id)
        
        # Wait for all requests to complete
        patient, observations, conditions, medications, encounters = await asyncio.gather(
            patient_task, observations_task, conditions_task, medications_task, encounters_task
        )
        
        return {
            "patient": patient,
            "observations": observations,
            "conditions": conditions,
            "medications": medications,
            "encounters": encounters,
            "last_updated": datetime.now().isoformat()
        }


class FHIRDataValidator:
    """Validates FHIR data integrity and clinical rules"""
    
    @staticmethod
    def validate_patient_data(patient: Patient) -> List[str]:
        """Validate patient data completeness and consistency"""
        issues = []
        
        if not patient.identifier:
            issues.append("Patient missing required identifiers")
        
        if not patient.name:
            issues.append("Patient missing name information")
        
        if not patient.birthDate:
            issues.append("Patient missing birth date")
        
        return issues
    
    @staticmethod
    def validate_observation_data(observation: Observation) -> List[str]:
        """Validate observation data for clinical consistency"""
        issues = []
        
        if not observation.code:
            issues.append("Observation missing code")
        
        if not observation.subject:
            issues.append("Observation missing subject reference")
        
        if observation.value and hasattr(observation.value, 'value'):
            # Check for reasonable vital sign ranges
            if observation.code.coding:
                for coding in observation.code.coding:
                    if coding.code == "8480-6":  # Systolic BP
                        if hasattr(observation.value, 'value') and (observation.value.value < 70 or observation.value.value > 250):
                            issues.append("Systolic blood pressure out of normal range")
                    elif coding.code == "8462-4":  # Diastolic BP
                        if hasattr(observation.value, 'value') and (observation.value.value < 40 or observation.value.value > 150):
                            issues.append("Diastolic blood pressure out of normal range")
        
        return issues
    
    @staticmethod
    def check_medication_interactions(medications: List[MedicationRequest]) -> List[str]:
        """Basic medication interaction checking"""
        warnings = []
        
        # This is a simplified example - in practice, you'd use a comprehensive drug interaction database
        blood_thinners = ["warfarin", "heparin", "aspirin"]
        nsaids = ["ibuprofen", "naproxen", "diclofenac"]
        
        active_meds = []
        for med in medications:
            if med.status == "active" and med.medicationCodeableConcept:
                if med.medicationCodeableConcept.text:
                    active_meds.append(med.medicationCodeableConcept.text.lower())
        
        # Check for blood thinner + NSAID interaction
        has_blood_thinner = any(bt in " ".join(active_meds) for bt in blood_thinners)
        has_nsaid = any(nsaid in " ".join(active_meds) for nsaid in nsaids)
        
        if has_blood_thinner and has_nsaid:
            warnings.append("Potential interaction: Blood thinner with NSAID increases bleeding risk")
        
        return warnings 