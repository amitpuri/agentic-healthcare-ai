# FHIR R4 Patient Schema Documentation

A comprehensive guide to the **FHIR R4 Patient** resource schema, including field descriptions, JSON structure, and Python implementation.

## Table of Contents

- [Overview](#overview)
- [Core Patient Schema](#core-patient-schema)
- [Field Descriptions](#field-descriptions)
- [JSON Implementation](#json-implementation)
- [Python Implementation](#python-implementation)
- [Field Reference Table](#field-reference-table)
- [Validation & Best Practices](#validation--best-practices)
- [Next Steps](#next-steps)
- [References](#references)

## Overview

The `Patient` resource in FHIR R4 stores demographic and administrative information about individuals receiving healthcare services. This resource follows the HL7 FHIR specification and can be implemented using various libraries including HAPI FHIR.

## Core Patient Schema

The `Patient` resource contains the following key elements according to the [FHIR R4 specification](https://hl7.org/fhir/r4/patient.html):

### Required Elements
- **resourceType**: Always `"Patient"` - identifies the resource type
- **id**: Logical identifier for the resource (inherited from meta info)

### Core Data Elements
- **identifier** (`Identifier[]`): Medical Record Numbers (MRNs), social security numbers, etc.
- **active** (`boolean`, 0..1): Indicates if this patient record is in active use
- **name** (`HumanName[]`): Patient's full names, including prefixes and suffixes
- **telecom** (`ContactPoint[]`): Contact information (phone, email, fax)
- **gender** (`code`): Administrative gender (male/female/other/unknown)
- **birthDate** (`date`): Date of birth
- **deceased[x]** (`boolean` or `dateTime`): Death indicator and date if applicable

### Address & Contact Information
- **address** (`Address[]`): Physical addresses (home, work, temporary, etc.)
- **contact** (`Patient.Contact[]`): Emergency contact and next-of-kin information

### Administrative Data
- **maritalStatus** (`CodeableConcept`): Marital status using standard codes
- **multipleBirth[x]** (`boolean`/`integer`): Multiple birth indicator (twins, triplets, etc.)
- **communication** (`Patient.Communication[]`): Preferred languages for communication
- **generalPractitioner** (`Reference[]`): Primary care provider references
- **managingOrganization** (`Reference(Organization)`): Organization managing this record

### Additional Elements
- **photo** (`Attachment[]`): Patient photographs
- **link** (`Patient.Link[]`): Links to related or duplicate patient resources

## Field Descriptions

| Field | Type | Cardinality | Description |
|-------|------|-------------|-------------|
| `resourceType` | string | 1..1 | Always "Patient" |
| `id` | string | 0..1 | Logical identifier for this resource |
| `identifier` | Identifier[] | 0..* | External identifiers (MRN, SSN, etc.) |
| `active` | boolean | 0..1 | Whether this patient record is active |
| `name` | HumanName[] | 0..* | A name associated with the patient |
| `telecom` | ContactPoint[] | 0..* | Contact information |
| `gender` | code | 0..1 | male \| female \| other \| unknown |
| `birthDate` | date | 0..1 | Date of birth |
| `deceased[x]` | boolean/dateTime | 0..1 | Indicates if patient is deceased |
| `address` | Address[] | 0..* | Physical addresses |
| `maritalStatus` | CodeableConcept | 0..1 | Marital (civil) status |
| `contact` | Patient.Contact[] | 0..* | Contact party information |
| `communication` | Patient.Communication[] | 0..* | Language communication preferences |

## JSON Implementation

Here's a comprehensive FHIR R4 Patient resource in JSON format:

```json
{
  "resourceType": "Patient",
  "id": "pat-arjun-patel-001",
  "identifier": [
    {
      "system": "http://hospital.org/mrn",
      "value": "MRN00123",
      "use": "official"
    },
    {
      "system": "http://www.aadhaar.gov.in",
      "value": "1234-5678-9012",
      "use": "secondary"
    }
  ],
  "active": true,
  "name": [
    {
      "use": "official",
      "family": "Patel",
      "given": ["Arjun", "R."],
      "prefix": ["Mr."]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+91-9876543210",
      "use": "mobile",
      "rank": 1
    },
    {
      "system": "email",
      "value": "arjun.patel@gmail.com",
      "use": "home"
    }
  ],
  "gender": "male",
  "birthDate": "1985-02-15",
  "address": [
    {
      "use": "home",
      "type": "physical",
      "line": ["123 MG Road", "Apartment 4B"],
      "city": "Lucknow",
      "state": "Uttar Pradesh",
      "postalCode": "226001",
      "country": "India",
      "period": {
        "start": "2020-01-01"
      }
    }
  ],
  "maritalStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
        "code": "M",
        "display": "Married"
      }
    ]
  },
  "contact": [
    {
      "relationship": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
              "code": "C",
              "display": "Emergency Contact"
            }
          ]
        }
      ],
      "name": {
        "family": "Sharma",
        "given": ["Leela"],
        "prefix": ["Mrs."]
      },
      "telecom": [
        {
          "system": "phone",
          "value": "+91-9123456780",
          "use": "home"
        }
      ],
      "address": {
        "line": ["45 MG Colony"],
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "postalCode": "226002",
        "country": "India"
      },
      "gender": "female"
    }
  ],
  "communication": [
    {
      "language": {
        "coding": [
          {
            "system": "urn:ietf:bcp:47",
            "code": "hi",
            "display": "Hindi"
          }
        ]
      },
      "preferred": true
    },
    {
      "language": {
        "coding": [
          {
            "system": "urn:ietf:bcp:47",
            "code": "en",
            "display": "English"
          }
        ]
      },
      "preferred": false
    }
  ],
  "generalPractitioner": [
    {
      "reference": "Practitioner/prac-john-smith-md",
      "display": "Dr. John Smith"
    }
  ],
  "managingOrganization": {
    "reference": "Organization/healthsystem1",
    "display": "Lucknow General Hospital"
  }
}
```

## Python Implementation

### Installation

Install the required dependencies:

```bash
pip install requests jsonschema
```

### Configuration

The implementation uses a configurable FHIR server endpoint. To change the server, simply modify the `FHIR_SERVER_BASE_URL` variable at the top of the code:

- **HAPI FHIR Test Server** (Default): `https://hapi.fhir.org/baseR4`
- **SMART Health IT**: `https://launch.smarthealthit.org/v/r4/fhir`
- **Firely Server**: `https://server.fire.ly/r4`
- **Local HAPI FHIR**: `http://localhost:8080/fhir`

All functions (`post_patient_to_fhir_server`, `get_patient_from_fhir_server`, `search_patients_on_fhir_server`) automatically use the configured server URL.

### Code Implementation

```python
import json
import requests
import time
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FHIR Server Configuration
FHIR_SERVERS = [
    "https://hapi.fhir.org/baseR4",
    "https://server.fire.ly/r4",
    "https://launch.smarthealthit.org/v/r4/fhir"
]

# Default to first server
FHIR_SERVER_BASE_URL = FHIR_SERVERS[0]

def create_patient_resource():
    """Create a FHIR Patient resource using pure Python dictionaries."""
    
    patient = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org/mrn",
                "value": "MRN00123",
                "use": "official"
            }
        ],
        "active": True,
        "name": [
            {
                "use": "official",
                "family": "Doe",
                "given": ["John", "M."],
                "prefix": ["Mr."]
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "+1-555-555-5555",
                "use": "mobile",
                "rank": 1
            },
            {
                "system": "email",
                "value": "john.doe@example.com",
                "use": "home"
            }
        ],
        "gender": "male",
        "birthDate": "1990-01-15",
        "address": [
            {
                "use": "home",
                "type": "physical",
                "line": ["123 Main St"],
                "city": "Anytown",
                "state": "CA",
                "postalCode": "12345",
                "country": "USA"
            }
        ],
        "maritalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                    "code": "S",
                    "display": "Single"
                }
            ]
        },
        "communication": [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": "en",
                            "display": "English"
                        }
                    ]
                },
                "preferred": True
            }
        ]
    }
    
    return json.dumps(patient, indent=2)

def create_resilient_session():
    """Create a requests session with retry logic."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504]  # retry on these status codes
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def try_alternate_servers(func):
    """Decorator to try alternate FHIR servers if the primary fails."""
    def wrapper(*args, **kwargs):
        global FHIR_SERVER_BASE_URL
        last_result = None
        
        for server in FHIR_SERVERS:
            FHIR_SERVER_BASE_URL = server
            logger.info(f"Attempting to use FHIR server: {server}")
            print(f"🌐 Trying FHIR server: {server}")
            
            try:
                result = func(*args, **kwargs)
                last_result = result
                
                # If request was successful, keep using this server
                if result.get("success"):
                    logger.info(f"Successfully used server: {server}")
                    return result
                else:
                    logger.warning(f"Request to {server} failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"Error with server {server}: {str(e)}")
                print(f"⚠️ Error with server {server}: {str(e)}")
                last_result = {"success": False, "error": str(e)}
            
            # Add a small delay before trying next server
            time.sleep(1)
        
        # If all servers failed, return the last error
        logger.error("All FHIR servers failed")
        return last_result
    
    return wrapper

@try_alternate_servers
def search_patients_on_fhir_server(family_name=None, given_name=None, limit=5):
    """Search for patients on the configured FHIR server by name."""
    try:
        # Build search parameters
        search_params = {"_count": limit}
        if family_name:
            search_params["family"] = family_name
        if given_name:
            search_params["given"] = given_name
            
        # FHIR server search endpoint
        fhir_server_url = f"{FHIR_SERVER_BASE_URL}/Patient"
        
        # Set headers for FHIR JSON
        headers = {
            "Accept": "application/fhir+json"
        }
        
        logger.info(f"Searching FHIR server with params: {search_params}")
        print(f"🔍 Searching for patients on FHIR server...")
        if family_name or given_name:
            print(f"🔎 Search criteria: family='{family_name}', given='{given_name}'")
        else:
            print(f"📋 Getting recent patients (limit: {limit})")
        print(f"📡 URL: {fhir_server_url}")
        
        # Create session with retry logic
        session = create_resilient_session()
        
        # GET search results with retry logic
        response = session.get(
            fhir_server_url,
            params=search_params,
            headers=headers,
            timeout=30
        )
        
        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        # Add a small delay after the request
        time.sleep(0.5)
        
        # Check response
        if response.status_code == 200:
            # Successfully retrieved
            bundle = response.json()
            
            if bundle.get("resourceType") == "Bundle":
                entries = bundle.get("entry", [])
                total = bundle.get("total", 0)
                
                logger.info(f"Search completed. Found {total} results")
                print(f"✅ Search completed!")
                print(f"📊 Total results: {total}")
                print(f"📋 Showing: {len(entries)} patients")
                
                patients = []
                for i, entry in enumerate(entries, 1):
                    if "resource" in entry:
                        patient = entry["resource"]
                        patient_id = patient.get("id", "Unknown")
                        
                        # Extract patient name
                        patient_name = "Unknown"
                        if "name" in patient and patient["name"]:
                            name_parts = patient["name"][0]
                            given_names = " ".join(name_parts.get("given", []))
                            family_name_found = name_parts.get("family", "")
                            patient_name = f"{given_names} {family_name_found}".strip()
                        
                        logger.debug(f"Found patient: {patient_name} (ID: {patient_id})")
                        print(f"  {i}. {patient_name} (ID: {patient_id})")
                        patients.append({
                            "id": patient_id,
                            "name": patient_name,
                            "resource": patient
                        })
                
                return {
                    "success": True,
                    "total": total,
                    "patients": patients,
                    "bundle": bundle
                }
            else:
                error_msg = "Unexpected response format"
                logger.error(error_msg)
                print(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        else:
            # Handle errors
            error_msg = f"Search failed. Status code: {response.status_code}"
            logger.error(f"{error_msg}\nResponse: {response.text}")
            print(f"❌ {error_msg}")
            print(f"📝 Response: {response.text}")
            
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
            
    except requests.exceptions.Timeout as e:
        error_msg = "Request timed out. Server may be slow."
        logger.error(f"{error_msg}: {str(e)}")
        print(f"⏰ {error_msg}")
        return {"success": False, "error": "Timeout"}
        
    except requests.exceptions.ConnectionError as e:
        error_msg = "Connection error. Check your internet connection."
        logger.error(f"{error_msg}: {str(e)}")
        print(f"🌐 {error_msg}")
        return {"success": False, "error": "Connection error"}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        print(f"📡 {error_msg}")
        return {"success": False, "error": str(e)}

# Usage implementation
def create_fhir_patient():
    """Create and display a FHIR Patient resource."""
    print("🏥 Creating FHIR Patient resource...")
    print("="*60)
    
    # Create patient JSON
    patient_json = create_patient_resource()
    
    print("✅ Patient resource created successfully!")
    print("\n" + "="*60)
    print("📋 PATIENT JSON:")
    print("="*60)
    print(patient_json)
    
    return patient_json

def validate_patient_json(patient_json_str):
    """Basic validation of patient JSON structure."""
    try:
        patient = json.loads(patient_json_str)
        
        # Basic validation checks
        assert patient.get("resourceType") == "Patient", "resourceType must be 'Patient'"
        # Note: ID is optional for new resources (server will assign)
        assert patient.get("active") is not None, "Patient must have active status"
        
        # Validate required structure
        if "name" in patient and patient["name"]:
            assert isinstance(patient["name"], list), "name must be an array"
            for name in patient["name"]:
                assert "family" in name or "given" in name, "name must have family or given name"
        
        if "identifier" in patient and patient["identifier"]:
            assert isinstance(patient["identifier"], list), "identifier must be an array"
            for identifier in patient["identifier"]:
                assert "system" in identifier and "value" in identifier, "identifier must have system and value"
        
        logger.info("Patient JSON validation passed")
        print("✅ Patient JSON validation passed")
        return True
        
    except (json.JSONDecodeError, AssertionError, KeyError) as e:
        logger.error(f"Patient JSON validation failed: {e}")
        print(f"❌ Patient JSON validation failed: {e}")
        return False

def validate_fhir_patient(patient_json):
    """Validate the FHIR Patient resource."""
    print("\n" + "="*60)
    print("🔍 VALIDATION:")
    print("="*60)
    
    is_valid = validate_patient_json(patient_json)
    
    if is_valid:
        print("✅ Patient validation passed!")
    else:
        print("❌ Patient validation failed!")
    
    return is_valid

def post_fhir_patient(patient_json):
    """Post the FHIR Patient resource to the server."""
    print("\n" + "="*60)
    print("🚀 POSTING TO FHIR SERVER:")
    print("="*60)
    
    result = post_patient_to_fhir_server(patient_json)
    
    if result["success"]:
        print(f"\n🎉 Success! Patient is now stored on FHIR server.")
        print(f"💾 You can view it at: {FHIR_SERVER_BASE_URL}/Patient/{result['patient_id']}")
        
        # Demonstrate reading back the created patient
        created_patient_id = result['patient_id']
        
        print("\n" + "="*60)
        print("📥 READING BACK THE CREATED PATIENT:")
        print("="*60)
        
        read_result = get_patient_from_fhir_server(created_patient_id)
        
        if read_result["success"]:
            print(f"\n✅ Successfully read back patient!")
            print(f"📋 Retrieved patient matches our created resource.")
        else:
            print(f"\n⚠️ Failed to read back patient: {read_result.get('error', 'Unknown error')}")
        
        return result
    else:
        print(f"\n⚠️ Failed to post to server: {result.get('error', 'Unknown error')}")
        return result

@try_alternate_servers
def post_patient_to_fhir_server(patient_json_str):
    """Post the patient resource to the configured FHIR server."""
    try:
        # Parse JSON to ensure it's valid
        patient_data = json.loads(patient_json_str)
        
        # FHIR server endpoint
        fhir_server_url = f"{FHIR_SERVER_BASE_URL}/Patient"
        
        # Set headers for FHIR JSON
        headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }
        
        logger.info(f"Posting patient to FHIR server: {fhir_server_url}")
        print(f"🌐 Posting patient to FHIR server...")
        print(f"📡 URL: {fhir_server_url}")
        
        # Create session with retry logic
        session = create_resilient_session()
        
        # POST the patient resource
        response = session.post(
            fhir_server_url,
            json=patient_data,
            headers=headers,
            timeout=30
        )
        
        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        # Add a small delay after the request
        time.sleep(0.5)
        
        # Check response
        if response.status_code == 201:
            # Successfully created
            created_patient = response.json()
            patient_id = created_patient.get("id")
            server_version = created_patient.get("meta", {}).get("versionId", "1")
            
            logger.info(f"Patient successfully created with ID: {patient_id}")
            print(f"✅ Patient successfully created!")
            print(f"🆔 Server-assigned ID: {patient_id}")
            print(f"📋 Version: {server_version}")
            print(f"🔗 Location: {response.headers.get('Location', 'N/A')}")
            
            return {
                "success": True,
                "patient_id": patient_id,
                "version": server_version,
                "location": response.headers.get('Location'),
                "full_response": created_patient
            }
            
        else:
            # Handle errors
            error_msg = f"Failed to create patient. Status code: {response.status_code}"
            logger.error(f"{error_msg}\nResponse: {response.text}")
            print(f"❌ {error_msg}")
            print(f"📝 Response: {response.text}")
            
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
            
    except requests.exceptions.Timeout as e:
        error_msg = "Request timed out. Server may be slow."
        logger.error(f"{error_msg}: {str(e)}")
        print(f"⏰ {error_msg}")
        return {"success": False, "error": "Timeout"}
        
    except requests.exceptions.ConnectionError as e:
        error_msg = "Connection error. Check your internet connection."
        logger.error(f"{error_msg}: {str(e)}")
        print(f"🌐 {error_msg}")
        return {"success": False, "error": "Connection error"}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        print(f"📡 {error_msg}")
        return {"success": False, "error": str(e)}

@try_alternate_servers
def get_patient_from_fhir_server(patient_id):
    """Retrieve a specific patient from the configured FHIR server by ID."""
    try:
        # FHIR server endpoint for specific patient
        fhir_server_url = f"{FHIR_SERVER_BASE_URL}/Patient/{patient_id}"
        
        # Set headers for FHIR JSON
        headers = {
            "Accept": "application/fhir+json"
        }
        
        logger.info(f"Retrieving patient from FHIR server: {fhir_server_url}")
        print(f"📥 Retrieving patient from FHIR server...")
        print(f"📡 URL: {fhir_server_url}")
        
        # Create session with retry logic
        session = create_resilient_session()
        
        # GET the patient resource
        response = session.get(
            fhir_server_url,
            headers=headers,
            timeout=30
        )
        
        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        # Add a small delay after the request
        time.sleep(0.5)
        
        # Check response
        if response.status_code == 200:
            # Successfully retrieved
            patient_data = response.json()
            patient_name = "Unknown"
            
            # Extract patient name for display
            if "name" in patient_data and patient_data["name"]:
                name_parts = patient_data["name"][0]
                given_names = " ".join(name_parts.get("given", []))
                family_name = name_parts.get("family", "")
                patient_name = f"{given_names} {family_name}".strip()
            
            logger.info(f"Successfully retrieved patient: {patient_name}")
            print(f"✅ Patient successfully retrieved!")
            print(f"👤 Patient Name: {patient_name}")
            print(f"🆔 Patient ID: {patient_id}")
            print(f"📅 Last Updated: {patient_data.get('meta', {}).get('lastUpdated', 'N/A')}")
            
            return {
                "success": True,
                "patient_data": patient_data,
                "patient_name": patient_name
            }
            
        elif response.status_code == 404:
            error_msg = f"Patient not found (ID: {patient_id})"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "status_code": 404,
                "error": "Patient not found"
            }
            
        else:
            # Handle other errors
            error_msg = f"Failed to retrieve patient. Status code: {response.status_code}"
            logger.error(f"{error_msg}\nResponse: {response.text}")
            print(f"❌ {error_msg}")
            print(f"📝 Response: {response.text}")
            
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
            
    except requests.exceptions.Timeout as e:
        error_msg = "Request timed out. Server may be slow."
        logger.error(f"{error_msg}: {str(e)}")
        print(f"⏰ {error_msg}")
        return {"success": False, "error": "Timeout"}
        
    except requests.exceptions.ConnectionError as e:
        error_msg = "Connection error. Check your internet connection."
        logger.error(f"{error_msg}: {str(e)}")
        print(f"🌐 {error_msg}")
        return {"success": False, "error": "Connection error"}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        logger.error(error_msg)
        print(f"📡 {error_msg}")
        return {"success": False, "error": str(e)}

def search_fhir_patients(family_name=None, given_name=None, limit=3):
    """Search for patients on the FHIR server.
    
    Args:
        family_name (str, optional): Family name to search for
        given_name (str, optional): Given name to search for
        limit (int, optional): Maximum number of results to return. Defaults to 3.
    """
    print("\n" + "="*60)
    print("🔍 DEMONSTRATING PATIENT SEARCH:")
    print("="*60)
    
    # Search for patients with provided parameters
    search_result = search_patients_on_fhir_server(family_name=family_name, given_name=given_name, limit=limit)
    
    if search_result["success"] and search_result["patients"]:
        print(f"\n🔎 Found {len(search_result['patients'])} patient(s)")
        
        # Try to read the first patient found
        first_patient = search_result["patients"][0]
        print(f"\n📖 Reading details for: {first_patient['name']}")
        
        read_result = get_patient_from_fhir_server(first_patient["id"])
        
        if read_result["success"]:
            print(f"✅ Successfully retrieved patient details!")
        else:
            print(f"⚠️ Failed to retrieve patient details: {read_result.get('error', 'Unknown error')}")
    else:
        print("\n🔍 No patients found or search failed.")
        
        # Fallback: get recent patients
        print("\n📋 Getting recent patients instead...")
        recent_result = search_patients_on_fhir_server(limit=limit)
        
        if recent_result["success"] and recent_result["patients"]:
            first_patient = recent_result["patients"][0]
            print(f"\n📖 Reading details for recent patient: {first_patient['name']}")
            
            read_result = get_patient_from_fhir_server(first_patient["id"])
            
            if read_result["success"]:
                print(f"✅ Successfully retrieved patient details!")
            else:
                print(f"⚠️ Failed to retrieve patient details: {read_result.get('error', 'Unknown error')}")
        else:
            print("⚠️ Could not retrieve any patients from server.")
    
    return search_result

if __name__ == "__main__":
    try:
        logger.info("Starting FHIR patient operations demo")
        
        # 1. Create FHIR Patient resource
        logger.info("Creating patient resource")
        patient_json = create_fhir_patient()
        
        # 2. Validate the patient resource
        logger.info("Validating patient resource")
        is_valid = validate_fhir_patient(patient_json)
        
        # 3. Post to FHIR server if validation passed
        if is_valid:
            logger.info("Posting patient to server")
            post_result = post_fhir_patient(patient_json)
            
            # 4. If posting was successful, retrieve the patient
            if post_result.get("success"):
                patient_id = post_result["patient_id"]
                logger.info(f"Retrieving posted patient with ID: {patient_id}")
                get_result = get_patient_from_fhir_server(patient_id)
        else:
            logger.warning("Skipping server post due to validation failure")
            print("\n⚠️ Skipping server post due to validation failure.")
        
        # 5. Search for specific patients
        logger.info("Performing patient search")
        search_result = search_fhir_patients(given_name="John", family_name="Doe")
        
        logger.info("Demo completed")
        
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        print(f"❌ An unexpected error occurred: {str(e)}")
```

The above code demonstrates a complete FHIR Patient resource implementation with creation, validation, posting to a FHIR server, and search functionality. The implementation includes robust error handling, multiple FHIR server support with failover, and comprehensive logging. Below you'll find detailed reference information about each field and best practices for implementation.

## Field Reference Table

| Field | Purpose | Implementation Notes | Validation Rules |
|-------|---------|---------------------|------------------|
| `resourceType` | Resource identification | Always `"Patient"` | Required, immutable |
| `identifier` | External IDs (MRN, SSN) | Include system URL for namespace | At least one recommended |
| `active` | Record validity | Prevents using archived records | Boolean, defaults to true |
| `name` | Patient identification | Support multiple name types | At least one recommended |
| `telecom` | Contact methods | Tag with appropriate `use` values | Validate phone/email formats |
| `gender` | Administrative gender | Use standard FHIR codes | Bound to AdministrativeGender |
| `birthDate` | Demographics | YYYY-MM-DD format | Date validation required |
| `address` | Physical locations | Support multiple address types | Validate postal codes |
| `maritalStatus` | Civil status | Use standard terminology codes | Optional but recommended |
| `contact` | Emergency contacts | Must include name and contact info | Relationship code required |
| `communication` | Language preferences | Only one `preferred=true` allowed | Language code validation |
| `managingOrganization` | Record custodian | Reference to Organization resource | Must resolve to valid org |

## Validation & Best Practices

### Data Validation Rules

1. **Identifier Requirements**
   - At least one identifier should be provided
   - System URL should be included for proper namespacing
   - Use appropriate identifier types (MRN, SSN, etc.)

2. **Communication Constraints**
   - Only one communication entry can have `preferred=true`
   - Language codes must follow BCP 47 standard

3. **Contact Information**
   - Emergency contacts must include name and telecom
   - Relationship codes should use standard terminologies

4. **Address Validation**
   - Postal codes should match country-specific formats
   - Use appropriate `use` and `type` values

### Implementation Best Practices

1. **Resource Construction**
   - Create resources using structured Python dictionaries
   - Follow FHIR R4 specification for field names and types
   - Always validate resources before persistence

2. **Data Quality**
   - Implement business rules for required fields
   - Validate against organizational policies
   - Use extensions for additional data needs

3. **Performance Considerations**
   - Index frequently searched fields (identifiers, names)
   - Consider pagination for large result sets
   - Implement proper caching strategies

## Testing with HAPI FHIR Server

The code implementation includes functionality to post your patient resource to the public HAPI FHIR test server at `https://hapi.fhir.org/baseR4`. This allows you to:

- **Test your FHIR resources** against a real FHIR server
- **Verify compliance** with FHIR R4 specification  
- **Get server-assigned IDs** and metadata
- **View resources** via the HAPI FHIR web interface

### How It Works

1. **Create** the patient resource using `create_patient_resource()`
2. **Validate** locally with `validate_patient_json()`
3. **Post** to HAPI FHIR server with `post_patient_to_hapi_fhir()`
4. **Receive** server response with patient ID and location
5. **Read back** the created patient with `get_patient_from_hapi_fhir()`
6. **Search** for patients using `search_patients_on_hapi_fhir()`

### HAPI FHIR Server Response

When successful, you'll receive:
- **Patient ID**: Server-assigned unique identifier
- **Version**: Resource version number
- **Location**: Direct URL to view the resource
- **Full Response**: Complete FHIR resource with server metadata

### Viewing Created Resources

After posting, you can view your patient at:
```
https://hapi.fhir.org/baseR4/Patient/{patient-id}
```

You can also browse all resources via the [HAPI FHIR web interface](https://hapi.fhir.org/).

### Reading and Searching Patients

The implementation includes comprehensive functionality to read and search patients:

#### Reading Individual Patients

Use `get_patient_from_hapi_fhir(patient_id)` to retrieve a specific patient:

```python
# Read a specific patient by ID
result = get_patient_from_hapi_fhir("12345")

if result["success"]:
    patient_data = result["patient_data"]
    patient_name = result["patient_name"]
    print(f"Retrieved: {patient_name}")
else:
    print(f"Error: {result['error']}")
```

#### Searching Patients

Use `search_patients_on_hapi_fhir()` to find patients by criteria:

```python
# Search by family name
results = search_patients_on_hapi_fhir(family_name="Smith", limit=10)

# Search by given name
results = search_patients_on_hapi_fhir(given_name="John", limit=5)

# Get recent patients (no search criteria)
results = search_patients_on_hapi_fhir(limit=20)

# Process results
if results["success"]:
    for patient in results["patients"]:
        print(f"Found: {patient['name']} (ID: {patient['id']})")
```

#### Search Parameters

FHIR supports various search parameters for patients:

- **family**: Search by family name (surname)
- **given**: Search by given name (first name)
- **birthdate**: Search by birth date
- **gender**: Search by gender
- **identifier**: Search by identifier (MRN, SSN, etc.)
- **active**: Search by active status
- **_count**: Limit number of results

#### Response Format

Search operations return a FHIR Bundle containing:
- **total**: Total number of matching patients
- **entry**: Array of patient resources
- **link**: Pagination links for large result sets

### Important Notes

- **Server Issues**: The public HAPI FHIR server occasionally experiences downtime or technical issues (HTTP 500 errors). This is normal for a public test server.
- **ID Assignment**: The server automatically assigns unique IDs to new resources. Don't include an `id` field when creating new resources.
- **Rate Limiting**: The server may have rate limits in place. If you encounter issues, wait a few minutes before retrying.
- **Data Persistence**: Resources on the public server may be periodically cleaned up, so don't rely on them for permanent storage.
- **Read Operations**: GET requests (reading/searching) work the same way as POST requests and may encounter similar server issues.
- **Error Handling**: All functions include comprehensive error handling for server downtime, timeouts, and network issues.

## Next Steps

### Immediate Actions
1. **Validation Setup**
   - Configure FHIR validator for your environment
   - Test against the provided JSON implementation
   - Implement automated validation in your pipeline

2. **Data Mapping**
   - Map existing patient data to FHIR elements
   - Create transformation scripts for data migration
   - Document any custom extensions needed

3. **Integration Planning**
   - Design API endpoints for patient operations
   - Implement search parameters based on use cases
   - Plan for data synchronization with external systems

### Advanced Implementation
1. **Profiles and Extensions**
   - Consider US Core or country-specific profiles
   - Implement custom extensions for specialized data
   - Document profile requirements clearly

2. **Security and Privacy**
   - Implement appropriate access controls
   - Consider data masking for sensitive information
   - Plan for audit logging and compliance

3. **Interoperability**
   - Test with external FHIR systems
   - Implement bulk data operations
   - Consider SMART on FHIR for app integration

## References

- [HL7 FHIR R4 Patient Resource](https://hl7.org/fhir/r4/patient.html) - Official specification
- [US Core Patient Profile](https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-patient.html) - US-specific implementation
- [FHIR JSON Format](https://hl7.org/fhir/r4/json.html) - JSON representation specification
- [FHIR Terminology](https://terminology.hl7.org/) - Standard code systems and value sets

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Maintained By**: Healthcare AI Development Team
