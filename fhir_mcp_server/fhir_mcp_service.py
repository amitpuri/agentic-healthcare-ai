#!/usr/bin/env python3
"""
FHIR MCP Server with proper MCP protocol implementation
"""

import click
import logging
import os
import asyncio
import ssl
import certifi
from typing import Dict, Any, Optional, List
from datetime import datetime
from fhirpy import AsyncFHIRClient
from fhirpy.base.exceptions import OperationOutcome
from starlette.responses import Response, JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
import uvicorn
import httpx

logger = logging.getLogger(__name__)

# Configuration from environment variables
FHIR_BASE_URL = os.getenv('FHIR_MCP_FHIR__BASE_URL', 'https://hapi.fhir.org/baseR4')
FHIR_ACCESS_TOKEN = os.getenv('FHIR_MCP_FHIR__ACCESS_TOKEN', '')
MCP_HOST = os.getenv('FHIR_MCP_HOST', '0.0.0.0')
MCP_PORT = int(os.getenv('FHIR_MCP_PORT', '8004'))
MCP_TIMEOUT = int(os.getenv('FHIR_MCP_FHIR__TIMEOUT', '30'))
# SSL Configuration
SSL_VERIFY = os.getenv('FHIR_MCP_SSL_VERIFY', 'true').lower() == 'true'

# Tool configuration for AI agents
TOOL_USE_CONFIG = {
    'fhir': {
        'enabled': True,
        'capabilities': [
            'patient_assessment',
            'encounter_analysis', 
            'observation_retrieval',
            'medication_review',
            'condition_monitoring',
            'vital_signs_analysis',
            'clinical_summary_generation'
        ]
    }
}

async def create_fhir_client() -> AsyncFHIRClient:
    """Create a simple FHIR client with proper SSL handling"""
    client_kwargs = {
        "url": FHIR_BASE_URL,
        "extra_headers": {
            "Accept": "application/fhir+json", 
            "Content-Type": "application/fhir+json",
            "User-Agent": "FHIR-MCP-Server/1.0.0"
        }
    }
    
    if FHIR_ACCESS_TOKEN:
        client_kwargs["authorization"] = f"Bearer {FHIR_ACCESS_TOKEN}"
    
    try:
        client = AsyncFHIRClient(**client_kwargs)
        # Test the connection with a simple capability statement request
        try:
            await client.resources("CapabilityStatement").search().fetch()
            logger.info(f"Successfully connected to FHIR server: {FHIR_BASE_URL}")
            return client
        except Exception as test_ex:
            logger.warning(f"Connection test failed, but client created: {test_ex}")
            return client
    except Exception as ex:
        logger.warning(f"Failed to create FHIR client for {FHIR_BASE_URL}: {ex}")
        return None

async def get_operation_outcome_error(code: str, diagnostics: str) -> dict:
    """Create a FHIR OperationOutcome for errors"""
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": code,
                "diagnostics": diagnostics,
            }
        ],
    }

async def process_bundle_entries(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Process FHIR bundle entries"""
    # Handle case where bundle is a list (direct resource list)
    if isinstance(bundle, list):
        return {
            "entry": bundle
        }
    
    # Handle case where bundle is a dictionary with entries
    if "entry" in bundle and isinstance(bundle["entry"], list):
        return {
            "entry": [
                entry.get("resource")
                for entry in bundle["entry"]
                if "resource" in entry
            ]
        }
    
    # Return as is if it's already in the right format
    return bundle

# MCP Protocol Methods
async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize method"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "FHIR MCP Server",
            "version": "1.0.0"
        }
    }

async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/list method"""
    return {
        "tools": [
            {
                "name": "get_capabilities",
                "description": "Get FHIR server capabilities and server information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_tool_config",
                "description": "Get tool configuration for AI agents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "toolUse": {
                            "type": "string",
                            "description": "Tool type ('fhir' for FHIR operations)",
                            "default": "fhir"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_patient_comprehensive_data",
                "description": "Get comprehensive patient data for AI assessment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "string",
                            "description": "Patient identifier"
                        }
                    },
                    "required": ["patient_id"]
                }
            },
            {
                "name": "search",
                "description": "Search FHIR resources",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "FHIR resource type"
                        },
                        "searchParam": {
                            "type": "object",
                            "description": "Search parameters"
                        }
                    },
                    "required": ["type", "searchParam"]
                }
            },
            {
                "name": "read",
                "description": "Read a specific FHIR resource by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "FHIR resource type (e.g., 'Patient', 'Observation')"
                        },
                        "id": {
                            "type": "string",
                            "description": "Resource ID"
                        }
                    },
                    "required": ["type", "id"]
                }
            }
        ]
    }

async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tools/call method"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if tool_name == "get_capabilities":
        return await get_capabilities()
    elif tool_name == "get_tool_config":
        return await get_tool_config(arguments.get("toolUse", "fhir"))
    elif tool_name == "get_patient_comprehensive_data":
        return await get_patient_comprehensive_data(arguments.get("patient_id"))
    elif tool_name == "search":
        return await search(arguments.get("type"), arguments.get("searchParam", {}), arguments.get("format", "mcp"))
    elif tool_name == "read":
        return await read(arguments.get("type"), arguments.get("id"), arguments.get("format", "mcp"))
    else:
        raise Exception(f"Unknown tool: {tool_name}")

# FHIR Tool Implementations
async def get_capabilities() -> Dict[str, Any]:
    """Get FHIR server capabilities and server information"""
    try:
        client = await create_fhir_client()
        
        # Get capability statement
        capability_statement = await client.resources("CapabilityStatement").search().fetch()
        
        # Extract key information
        capabilities = {}
        if capability_statement.get("entry"):
            cap_resource = capability_statement["entry"][0].get("resource", {})
            capabilities = {
                "software": cap_resource.get("software", {"name": "FHIR Server"}),
                "fhirVersion": cap_resource.get("fhirVersion", "R4"),
                "format": cap_resource.get("format", ["application/fhir+json"]),
                "rest": cap_resource.get("rest", []),
                "status": cap_resource.get("status", "active")
            }
        else:
            # Fallback if no capability statement found
            capabilities = {
                "software": {"name": "FHIR Server"},
                "fhirVersion": "R4",
                "format": ["application/fhir+json"],
                "status": "active"
            }
        
        return {
            "capabilities": capabilities,
            "server_info": {
                "base_url": FHIR_BASE_URL,
                "mcp_server": "FHIR MCP Server v1.0.0",
                "connection_time": datetime.now().isoformat()
            }
        }
        
    except Exception as ex:
        logger.warning(f"Could not get full capabilities, using fallback: {ex}")
        return {
            "capabilities": {
                "software": {"name": "FHIR Server"},
                "fhirVersion": "R4",
                "format": ["application/fhir+json"],
                "status": "active"
            },
            "server_info": {
                "base_url": FHIR_BASE_URL,
                "mcp_server": "FHIR MCP Server v1.0.0",
                "connection_time": datetime.now().isoformat(),
                "note": "Limited capabilities due to server access restrictions"
            }
        }

async def get_tool_config(toolUse: str = 'fhir') -> Dict[str, Any]:
    """Get tool configuration for AI agents"""
    if toolUse in TOOL_USE_CONFIG:
        return {
            "toolUse": toolUse,
            "config": TOOL_USE_CONFIG[toolUse],
            "server": {
                "name": "FHIR MCP Server",
                "version": "2.0.0",
                "fhir_version": "R4",
                "base_url": FHIR_BASE_URL
            }
        }
    else:
        return {"error": f"Tool configuration not found for: {toolUse}"}

async def get_patient_comprehensive_data(patient_id: str) -> Dict[str, Any]:
    """Get comprehensive patient data for AI assessment"""
    logger.info(f"Comprehensive data request for patient {patient_id}")
    try:
        client = await create_fhir_client()
        
        if client is None:
            logger.error("FHIR client not available")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"ERROR: Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                    }
                ]
            }
        
        # Get patient demographics
        patient_bundle = await client.resources("Patient").search(_id=patient_id).fetch()
        
        # Handle both list and dict responses from FHIR client
        if isinstance(patient_bundle, list):
            if patient_bundle:
                patient = patient_bundle[0]
                logger.info(f"Found patient {patient_id} from list response")
            else:
                logger.warning(f"Patient {patient_id} not found - empty list")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Patient {patient_id} not found in FHIR server."
                        }
                    ]
                }
        else:
            processed_patient_bundle = await process_bundle_entries(patient_bundle)
            if processed_patient_bundle.get("entry") and len(processed_patient_bundle["entry"]) > 0:
                patient = processed_patient_bundle["entry"][0]
                logger.info(f"Found patient {patient_id} from bundle response")
            else:
                logger.warning(f"Patient {patient_id} not found - empty bundle")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Patient {patient_id} not found in FHIR server."
                        }
                    ]
                }
        
        # Get basic observations data
        observations = await client.resources("Observation").search(patient=f"Patient/{patient_id}").fetch()
        conditions = await client.resources("Condition").search(patient=f"Patient/{patient_id}").fetch()
        
        # Extract patient information
        patient_name = ""
        names = patient.get("name", [])
        if names:
            name_parts = []
            for name in names:
                given = name.get("given", [])
                family = name.get("family", "")
                if given:
                    name_parts.extend(given)
                if family:
                    name_parts.append(family)
            patient_name = " ".join(name_parts)
        
        # Extract address
        address = ""
        addresses = patient.get("address", [])
        if addresses:
            addr = addresses[0]
            addr_parts = []
            if addr.get("line"):
                addr_parts.extend(addr.get("line"))
            if addr.get("city"):
                addr_parts.append(addr.get("city"))
            if addr.get("state"):
                addr_parts.append(addr.get("state"))
            if addr.get("postalCode"):
                addr_parts.append(addr.get("postalCode"))
            address = ", ".join(addr_parts)
        
        # Extract phone
        phone = ""
        telecoms = patient.get("telecom", [])
        for telecom in telecoms:
            if telecom.get("system") == "phone" and telecom.get("value"):
                phone = telecom.get("value")
                break
        
        # Count observations and conditions
        obs_processed = await process_bundle_entries(observations)
        cond_processed = await process_bundle_entries(conditions)
        
        obs_count = len(obs_processed.get("entry", []))
        cond_count = len(cond_processed.get("entry", []))
        
        # Create a text response that Claude can easily understand
        response_text = f"""PATIENT DATA FOUND:

Patient ID: {patient.get('id')}
Name: {patient_name}
Gender: {patient.get('gender', 'Unknown')}
Birth Date: {patient.get('birthDate', 'Unknown')}
Active: {patient.get('active', True)}
Address: {address or 'Not provided'}
Phone: {phone or 'Not provided'}
Medical Records: {obs_count} observations, {cond_count} conditions

Status: Successfully retrieved patient data from FHIR server"""
        
        logger.info(f"Successfully returning data for patient {patient_id}: {patient_name}")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text
                }
            ]
        }
        
    except Exception as ex:
        logger.error(f"Failed to get comprehensive patient data for {patient_id}: {ex}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ERROR: Failed to retrieve patient {patient_id}: {str(ex)}"
                }
            ]
        }

async def search(type: str, searchParam: Dict[str, str], format: str = "mcp") -> Dict[str, Any]:
    """Search for resources based on criteria"""
    try:
        client = await create_fhir_client()
        
        # Validate required parameters
        if not type:
            if format == "fhir":
                return await get_operation_outcome_error("invalid", "Resource type is required")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "ERROR: Resource type is required for search"
                    }
                ]
            }
        
        # If client is None, return error
        if client is None:
            logger.error("FHIR client not available")
            if format == "fhir":
                return await get_operation_outcome_error(
                    "connection", 
                    f"Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"ERROR: Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                    }
                ]
            }
        
        # Log the search attempt
        logger.info(f"Searching for {type} with parameters: {searchParam}, format: {format}")
        
        resources = await client.resources(type).search(**searchParam).fetch()
        
        # Handle both list and dict responses from FHIR client
        if isinstance(resources, list):
            # Direct list of resources
            result_entries = resources
        else:
            # Bundle format
            result = await process_bundle_entries(resources)
            result_entries = result.get("entry", [])
        
        logger.info(f"Search successful for {type}, found {len(result_entries)} resources")
        
        # Return format based on requested format
        if format == "fhir":
            # Return traditional FHIR Bundle format for UI compatibility
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(result_entries),
                "entry": [{"resource": resource} for resource in result_entries]
            }
        
        # For Patient searches, create user-friendly responses (MCP format)
        if type == "Patient" and result_entries:
            patient_summaries = []
            
            for i, patient in enumerate(result_entries):
                # Extract patient information
                patient_name = ""
                names = patient.get("name", [])
                if names:
                    name_parts = []
                    for name in names:
                        given = name.get("given", [])
                        family = name.get("family", "")
                        if given:
                            name_parts.extend(given)
                        if family:
                            name_parts.append(family)
                    patient_name = " ".join(name_parts)
                
                # Extract phone
                phone = ""
                telecoms = patient.get("telecom", [])
                for telecom in telecoms:
                    if telecom.get("system") == "phone" and telecom.get("value"):
                        phone = telecom.get("value")
                        break
                
                # Extract address
                address = ""
                addresses = patient.get("address", [])
                if addresses:
                    addr = addresses[0]
                    addr_parts = []
                    if addr.get("line"):
                        addr_parts.extend(addr.get("line"))
                    if addr.get("city"):
                        addr_parts.append(addr.get("city"))
                    if addr.get("state"):
                        addr_parts.append(addr.get("state"))
                    if addr.get("postalCode"):
                        addr_parts.append(addr.get("postalCode"))
                    address = ", ".join(addr_parts)
                
                patient_summary = f"""Patient {i+1}:
  ID: {patient.get('id')}
  Name: {patient_name}
  Gender: {patient.get('gender', 'Unknown')}
  Birth Date: {patient.get('birthDate', 'Unknown')}
  Phone: {phone or 'Not provided'}
  Address: {address or 'Not provided'}"""
                
                patient_summaries.append(patient_summary)
            
            response_text = f"""PATIENTS FOUND: {len(result_entries)} patient(s)

{chr(10).join(patient_summaries)}

Status: Successfully retrieved patient data from FHIR server"""
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
        
        elif result_entries:
            # For non-Patient resources or as fallback
            response_text = f"""{type.upper()} SEARCH RESULTS: Found {len(result_entries)} resource(s)

Resource IDs: {', '.join([r.get('id', 'Unknown') for r in result_entries[:10]])}
{"..." if len(result_entries) > 10 else ""}

Status: Successfully retrieved {type} resources from FHIR server"""
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
        else:
            # No results found
            if format == "fhir":
                return {
                    "resourceType": "Bundle",
                    "type": "searchset", 
                    "total": 0,
                    "entry": []
                }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"No {type} resources found matching the search criteria."
                    }
                ]
            }
        
    except Exception as ex:
        error_msg = f"Search failed for {type}: {str(ex)}"
        logger.error(error_msg)
        
        if format == "fhir":
            # Provide more specific error information in FHIR format
            if "SSL" in str(ex) or "certificate" in str(ex).lower():
                return await get_operation_outcome_error(
                    "ssl_error", 
                    f"SSL certificate verification failed when connecting to {FHIR_BASE_URL}. Please check your SSL configuration."
                )
            elif "Cannot connect to host" in str(ex):
                return await get_operation_outcome_error(
                    "connection", 
                    f"Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                )
            elif "timeout" in str(ex).lower():
                return await get_operation_outcome_error(
                    "timeout", 
                    f"Request to FHIR server timed out. The server may be slow or unavailable."
                )
            else:
                return await get_operation_outcome_error("exception", error_msg)

        # Provide more specific error information in MCP format
        if "SSL" in str(ex) or "certificate" in str(ex).lower():
            error_text = f"SSL certificate verification failed when connecting to {FHIR_BASE_URL}. Please check your SSL configuration."
        elif "Cannot connect to host" in str(ex):
            error_text = f"Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
        elif "timeout" in str(ex).lower():
            error_text = f"Request to FHIR server timed out. The server may be slow or unavailable."
        else:
            error_text = f"ERROR: {error_msg}"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_text
                }
            ]
        }

async def read(type: str, id: str, format: str = "mcp") -> Dict[str, Any]:
    """Read a specific FHIR resource by ID"""
    logger.info(f"Read request: type={type}, id={id}, format={format}")
    try:
        client = await create_fhir_client()
        
        if client is None:
            logger.error("FHIR client not available")
            if format == "fhir":
                return await get_operation_outcome_error(
                    "connection", 
                    f"Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"ERROR: Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                    }
                ]
            }
        
        logger.info(f"Searching for {type} with ID {id}")
        bundle = await client.resources(type).search(_id=id).fetch()
        logger.info(f"Search completed, got response")
        
        # Handle both list and dict responses from FHIR client
        if isinstance(bundle, list):
            if bundle:
                resource = bundle[0]
                logger.info(f"Found {type} resource with ID {id}")
            else:
                logger.warning(f"{type} {id} not found - empty list")
                if format == "fhir":
                    return await get_operation_outcome_error("not_found", f"Resource {type}/{id} not found")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"{type} ID {id} not found in the FHIR server."
                        }
                    ]
                }
        else:
            processed_bundle = await process_bundle_entries(bundle)
            if processed_bundle.get("entry") and len(processed_bundle["entry"]) > 0:
                resource = processed_bundle["entry"][0]
                logger.info(f"Found {type} resource with ID {id}")
            else:
                logger.warning(f"{type} {id} not found - empty bundle")
                if format == "fhir":
                    return await get_operation_outcome_error("not_found", f"Resource {type}/{id} not found")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"{type} ID {id} not found in the FHIR server."
                        }
                    ]
                }
        
        # Return format based on requested format
        if format == "fhir":
            # Return raw FHIR resource for UI compatibility
            logger.info(f"Returning raw FHIR resource for {type} ID {id}")
            return resource
        
        # For Patient resources, create a simplified readable response (MCP format)
        if type == "Patient":
            # Extract patient information
            patient_name = ""
            names = resource.get("name", [])
            if names:
                name_parts = []
                for name in names:
                    given = name.get("given", [])
                    family = name.get("family", "")
                    if given:
                        name_parts.extend(given)
                    if family:
                        name_parts.append(family)
                patient_name = " ".join(name_parts)
            
            # Extract address
            address = ""
            addresses = resource.get("address", [])
            if addresses:
                addr = addresses[0]
                addr_parts = []
                if addr.get("line"):
                    addr_parts.extend(addr.get("line"))
                if addr.get("city"):
                    addr_parts.append(addr.get("city"))
                if addr.get("state"):
                    addr_parts.append(addr.get("state"))
                if addr.get("postalCode"):
                    addr_parts.append(addr.get("postalCode"))
                address = ", ".join(addr_parts)
            
            # Extract phone
            phone = ""
            telecoms = resource.get("telecom", [])
            for telecom in telecoms:
                if telecom.get("system") == "phone" and telecom.get("value"):
                    phone = telecom.get("value")
                    break
            
            response_text = f"""PATIENT FOUND:

Patient ID: {resource.get('id')}
Name: {patient_name}
Gender: {resource.get('gender', 'Unknown')}
Birth Date: {resource.get('birthDate', 'Unknown')}
Active: {resource.get('active', True)}
Address: {address or 'Not provided'}
Phone: {phone or 'Not provided'}

Status: Successfully retrieved patient from FHIR server"""
            
            logger.info(f"Returning simplified patient data for ID {id}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
        else:
            # For other resource types, return basic info (MCP format)
            response_text = f"""{type.upper()} FOUND:

Resource ID: {resource.get('id')}
Resource Type: {resource.get('resourceType')}

Status: Successfully retrieved {type} from FHIR server"""
            
            logger.info(f"Returning {type} data for ID {id}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
        
    except Exception as ex:
        logger.error(f"Failed to read {type}/{id}: {ex}")
        if format == "fhir":
            # Handle SSL and connection errors in FHIR format
            if "SSL" in str(ex) or "certificate" in str(ex).lower():
                return await get_operation_outcome_error(
                    "ssl_error", 
                    f"SSL certificate verification failed when connecting to {FHIR_BASE_URL}. Please check your SSL configuration."
                )
        elif "Cannot connect to host" in str(ex):
                return await get_operation_outcome_error(
                    "connection", 
                    f"Cannot connect to FHIR server {FHIR_BASE_URL}. Please check your network connection and server availability."
                )
        else:
                return await get_operation_outcome_error("exception", f"Read failed for {type}/{id}: {str(ex)}")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ERROR: Failed to retrieve {type} {id}: {str(ex)}"
                }
            ]
        }

# HTTP Route Handlers
async def mcp_endpoint(request: Request) -> JSONResponse:
    """Main MCP endpoint that handles all MCP protocol methods"""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    
    if request.method == "OPTIONS":
        return JSONResponse({"message": "OK"}, headers=headers)
    
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", 1)
        
        # Handle MCP protocol methods
        if method == "initialize":
            result = await handle_initialize(params)
        elif method == "tools/list":
            result = await handle_tools_list(params)
        elif method == "tools/call":
            result = await handle_tools_call(params)
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }, headers=headers)
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }, headers=headers)
        
    except Exception as ex:
        logger.error(f"MCP endpoint error: {ex}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": f"Internal error: {str(ex)}"}
        }, headers=headers)

async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint"""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    
    if request.method == "OPTIONS":
        return JSONResponse({"message": "OK"}, headers=headers)
    
    return JSONResponse({
        "status": "healthy",
        "service": "FHIR MCP Server",
        "version": "1.0.0",
        "fhir_url": FHIR_BASE_URL
    }, headers=headers)

async def info_endpoint(request: Request) -> JSONResponse:
    """Info endpoint"""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }
    
    if request.method == "OPTIONS":
        return JSONResponse({"message": "OK"}, headers=headers)
    
    return JSONResponse({
        "service": "FHIR MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/ (POST with JSON-RPC 2.0)"
        },
        "fhir_url": FHIR_BASE_URL,
        "note": "This server implements the MCP protocol"
    }, headers=headers)

def create_app() -> Starlette:
    """Create the Starlette application with MCP protocol support"""
    
    # Define CORS middleware
    cors_middleware = Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Create routes
    routes = [
        Route("/", mcp_endpoint, methods=["POST", "OPTIONS"]),
        Route("/health", health_check, methods=["GET", "OPTIONS"]),
        Route("/info", info_endpoint, methods=["GET", "OPTIONS"]),
    ]
    
    # Create app with middleware
    app = Starlette(
        routes=routes,
        middleware=[cors_middleware]
    )
    
    return app

@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Log level to use",
)
def main(log_level: str) -> int:
    """Start the FHIR MCP server with proper MCP protocol implementation"""
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="[%(asctime)s] %(levelname)s {%(name)s.%(funcName)s:%(lineno)d} - %(message)s",
    )
    
    try:
        app = create_app()
        
        logger.info(f"Starting FHIR MCP server on {MCP_HOST}:{MCP_PORT}")
        logger.info(f"FHIR Server: {FHIR_BASE_URL}")
        logger.info("MCP Protocol: 2024-11-05")
        
        # Run the server
        uvicorn.run(
            app,
            host=MCP_HOST,
            port=MCP_PORT,
            log_level=log_level.lower()
        )
        
    except Exception as ex:
        logger.error(f"Failed to start FHIR MCP server: {ex}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    main() 
