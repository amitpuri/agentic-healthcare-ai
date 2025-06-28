from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FHIR Proxy Service", description="Proxy service to handle FHIR requests with CORS support")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default FHIR server
DEFAULT_FHIR_URL = "https://hapi.fhir.org/baseR4"

def normalize_fhir_url(url: str) -> str:
    """Normalize FHIR URL by removing trailing slash to prevent double slash issues"""
    return url.rstrip('/')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fhir-proxy"}

@app.get("/fhir/metadata")
async def get_metadata(fhir_url: Optional[str] = None):
    """Get FHIR server metadata/CapabilityStatement"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/metadata")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Patient")
async def search_patients(fhir_url: Optional[str] = None, name: Optional[str] = None, _count: Optional[int] = 20):
    """Search for patients"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    # Build query parameters
    params = {"_count": _count}
    if name:
        params["name"] = name
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/Patient", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Patient/{patient_id}")
async def get_patient(patient_id: str, fhir_url: Optional[str] = None):
    """Get specific patient by ID"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/Patient/{patient_id}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Patient/{patient_id}/Condition")
async def get_patient_conditions(patient_id: str, fhir_url: Optional[str] = None):
    """Get conditions for a specific patient"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/Condition?patient={patient_id}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Patient/{patient_id}/MedicationStatement")
async def get_patient_medications(patient_id: str, fhir_url: Optional[str] = None):
    """Get medications for a specific patient"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/MedicationStatement?patient={patient_id}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Patient/{patient_id}/Observation")
async def get_patient_observations(patient_id: str, fhir_url: Optional[str] = None):
    """Get observations for a specific patient"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/Observation?patient={patient_id}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Condition")
async def search_conditions(request: Request, fhir_url: Optional[str] = None):
    """Search for conditions with query parameters"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    # Extract all query parameters except fhir_url
    params = dict(request.query_params)
    params.pop('fhir_url', None)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/Condition", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/MedicationRequest")
async def search_medication_requests(request: Request, fhir_url: Optional[str] = None):
    """Search for medication requests with query parameters"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    # Extract all query parameters except fhir_url
    params = dict(request.query_params)
    params.pop('fhir_url', None)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/MedicationRequest", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/Observation")
async def search_observations(request: Request, fhir_url: Optional[str] = None):
    """Search for observations with query parameters"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    # Extract all query parameters except fhir_url
    params = dict(request.query_params)
    params.pop('fhir_url', None)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{target_url}/Observation", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to FHIR server: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"FHIR server error: {str(e)}")

@app.get("/fhir/test-connection")
async def test_fhir_connection(fhir_url: Optional[str] = None):
    """Test connection to FHIR server"""
    target_url = normalize_fhir_url(fhir_url or DEFAULT_FHIR_URL)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test with metadata endpoint
            response = await client.get(f"{target_url}/metadata")
            response.raise_for_status()
            
            metadata = response.json()
            server_info = {
                "software": metadata.get("software", {}).get("name", "Unknown"),
                "version": metadata.get("software", {}).get("version", "Unknown"),
                "fhirVersion": metadata.get("fhirVersion", "Unknown")
            }
            
            return {
                "success": True,
                "message": "Successfully connected to FHIR server",
                "serverInfo": server_info,
                "url": target_url
            }
    except httpx.RequestError as e:
        logger.error(f"Network error connecting to FHIR server: {e}")
        return {
            "success": False,
            "message": f"Failed to connect to FHIR server: {str(e)}",
            "url": target_url
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from FHIR server: {e}")
        return {
            "success": False,
            "message": f"FHIR server returned error: {e.response.status_code}",
            "url": target_url
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 