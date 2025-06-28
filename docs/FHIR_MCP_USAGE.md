# FHIR MCP Server Usage Guide for Claude AI

This guide provides step-by-step instructions for setting up and using the FHIR MCP Server with Claude AI to retrieve patient information and perform healthcare data operations.

## Overview

The FHIR MCP Server is a Model Context Protocol (MCP) server that provides secure access to FHIR (Fast Healthcare Interoperability Resources) servers. It acts as a bridge between Claude AI and FHIR APIs, enabling AI-powered healthcare data analysis.

### Available Tools

The FHIR MCP Server provides the following tools for Claude AI:

- **get_capabilities** - Get FHIR server capabilities and server information
- **get_tool_config** - Get tool configuration for AI agents
- **get_patient_comprehensive_data** - Get comprehensive patient data for AI assessment
- **search** - Search for FHIR resources with parameters
- **read** - Read a specific FHIR resource by ID

## Part 1: Server Setup and Configuration

### Step 1: Start the FHIR MCP Server

First, you need to start the FHIR MCP Server. You have several options:

#### Option A: Using Docker (Recommended)

1. Navigate to the project root directory
2. Copy the environment template:
   ```bash
   cp env.template .env
   ```
3. Edit `.env` with your FHIR server configuration:
   ```env
   FHIR_MCP_FHIR__BASE_URL=https://hapi.fhir.org/baseR4
   FHIR_MCP_HOST=localhost
   FHIR_MCP_PORT=8004
   FHIR_MCP_FHIR__ACCESS_TOKEN=  # Optional Bearer token
   ```
4. Start the server:
   ```bash
   docker-compose up fhir-mcp-server
   ```

#### Option B: Manual Installation

1. Install dependencies:
   ```bash
   cd fhir_mcp_server
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export FHIR_MCP_FHIR__BASE_URL="https://hapi.fhir.org/baseR4"
   export FHIR_MCP_HOST="localhost"
   export FHIR_MCP_PORT="8004"
   ```

3. Run the server:
   ```bash
   python -m fhir_mcp_server
   ```

### Step 2: Verify Server is Running

Check that the server is running by visiting the health endpoint:
```bash
curl http://localhost:8004/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "FHIR MCP Server",
  "version": "1.0.0",
  "fhir_url": "https://hapi.fhir.org/baseR4"
}
```

## Part 2: Claude Code MCP Configuration

### Step 3: Configure Claude Code to Use FHIR MCP Server

To use the FHIR MCP Server directly with Claude Code, you need to add it using the `claude mcp add` command.

#### Prerequisites

1. **Install Claude Code**: Make sure you have Claude Code installed
2. **FHIR MCP Server Running**: Ensure your server is running at `http://localhost:8004`
3. **Verify Server**: Check the server is accessible:
   ```bash
   curl http://localhost:8004/health
   ```

#### Add FHIR MCP Server to Claude Code

**Option A: HTTP Transport (Recommended)**

Add the FHIR MCP Server using HTTP transport:

```bash
# Basic HTTP server configuration
claude mcp add --transport http fhir-mcp-server http://localhost:8004
```

**Option B: With Custom Headers (if authentication needed)**

If your FHIR server requires authentication:

```bash
# HTTP server with authentication header
claude mcp add --transport http fhir-mcp-server http://localhost:8004 --header "Authorization: Bearer your-token"
```

**Option C: Local Stdio Server**

If you want Claude Code to start the server itself:

```bash
# Stdio server that Claude manages
claude mcp add fhir-mcp-server -e FHIR_MCP_FHIR__BASE_URL=https://hapi.fhir.org/baseR4 -e FHIR_MCP_HOST=localhost -e FHIR_MCP_PORT=8004 -- python -m fhir_mcp_server
```

#### Complete Command Breakdown

**Command Structure:**
```bash
claude mcp add [OPTIONS] <name> <command_or_url> [args...]
```

**For HTTP Transport:**
```bash
claude mcp add --transport http [--scope SCOPE] [--header "KEY: VALUE"] <server-name> <url>
```

**For Stdio Transport:**
```bash
claude mcp add [--scope SCOPE] [-e KEY=VALUE] <server-name> -- <command> [args...]
```

#### Detailed Parameter Explanation

**1. Basic Components:**
```bash
claude mcp add                    # Base command
--transport http                  # Transport protocol (http, sse, or stdio)
fhir-mcp-server                  # Server name (you choose this)
http://localhost:8004            # Server URL
```

**2. Scope Options:**
```bash
-s local                         # Local scope (default) - current project only
-s project                       # Project scope - shared via .mcp.json file
-s user                         # User scope - available across all projects
```

**3. Environment Variables (for stdio):**
```bash
-e FHIR_MCP_FHIR__BASE_URL=https://hapi.fhir.org/baseR4    # FHIR server URL
-e FHIR_MCP_HOST=localhost                                  # MCP server host
-e FHIR_MCP_PORT=8004                                      # MCP server port
-e FHIR_MCP_FHIR__ACCESS_TOKEN=your_token                  # Optional auth token
```

**4. Authentication Headers (for HTTP):**
```bash
--header "Authorization: Bearer your-token"               # Bearer token
--header "X-API-Key: your-api-key"                       # API key
--header "Content-Type: application/json"                # Content type
```

#### Complete Command Examples

**Example 1: Simple HTTP Server (Most Common)**
```bash
claude mcp add --transport http fhir-mcp-server http://localhost:8004
```
- **Transport**: HTTP
- **Name**: `fhir-mcp-server`
- **URL**: `http://localhost:8004`
- **Scope**: local (default)

**Example 2: Project-Scoped with Authentication**
```bash
claude mcp add --transport http --scope project --header "Authorization: Bearer abc123" fhir-secure-server http://localhost:8004
```
- **Transport**: HTTP
- **Scope**: project (shared with team)
- **Auth**: Bearer token
- **Name**: `fhir-secure-server`

**Example 3: Stdio Server with Environment Variables**
```bash
claude mcp add --scope user -e FHIR_MCP_FHIR__BASE_URL=https://hapi.fhir.org/baseR4 -e FHIR_MCP_HOST=localhost -e FHIR_MCP_PORT=8004 fhir-stdio-server -- python -m fhir_mcp_server
```
- **Scope**: user (available across projects)
- **Environment**: Multiple env vars set
- **Command**: `python -m fhir_mcp_server`
- **Name**: `fhir-stdio-server`

**Example 4: Multiple Headers and Custom Port**
```bash
claude mcp add --transport http --scope project --header "Authorization: Bearer token123" --header "X-Client-ID: myapp" fhir-api-server http://localhost:8005
```
- **Multiple headers**: Auth + Client ID
- **Custom port**: 8005
- **Project scope**: Shared configuration

**Example 5: Production FHIR Server with SSL**
```bash
claude mcp add --transport http --scope user --header "Authorization: Bearer prod-token" fhir-production https://fhir.yourhospital.com/api
```
- **HTTPS**: Production server
- **User scope**: Personal access
- **Production auth**: Real bearer token

#### Command Flags Reference

| Flag | Short | Description | Example |
|------|-------|-------------|---------|
| `--transport` | | Protocol type | `--transport http` |
| `--scope` | `-s` | Configuration scope | `-s project` |
| `--env` | `-e` | Environment variable | `-e KEY=value` |
| `--header` | | HTTP header | `--header "Auth: token"` |
| `--` | | Separates command args | `-- python script.py` |

#### Verification Commands

After adding your server, use these commands to verify:

```bash
# List all configured servers
claude mcp list

# Get specific server details
claude mcp get fhir-mcp-server

# Test server connection (in Claude Code)
/mcp

# Remove server if needed
claude mcp remove fhir-mcp-server
```

#### Common Scenarios

**Scenario 1: Development Setup**
```bash
# Local development server
claude mcp add --transport http fhir-dev http://localhost:8004
```

**Scenario 2: Team Project**
```bash
# Shared team configuration
claude mcp add --transport http -s project fhir-team-server http://fhir-server:8004
```

**Scenario 3: Personal Production Access**
```bash
# Personal production access
claude mcp add --transport http -s user --header "Authorization: Bearer $(cat ~/.fhir-token)" fhir-prod https://api.hospital.com/fhir
```

**Scenario 4: Self-Managed Server**
```bash
# Claude starts and manages the server
claude mcp add -e FHIR_MCP_FHIR__BASE_URL=https://hapi.fhir.org/baseR4 fhir-local -- python -m fhir_mcp_server
```

### Step 4: Verify MCP Server Connection

After adding the server:

1. **List configured servers**:
   ```bash
   claude mcp list
   ```

2. **Get server details**:
   ```bash
   claude mcp get fhir-mcp-server
   ```

3. **Check MCP status in Claude Code**:
   Use the `/mcp` command within Claude Code to see server status

### Step 5: Using MCP Tools Directly

Once configured, you can use natural language to access FHIR tools:

```
Can you get the FHIR server capabilities using the MCP tools?
```

```
Please search for patients named "John" using the FHIR MCP server.
```

```
Can you get comprehensive patient data for patient ID "597179"?
```

#### Advanced MCP Features

**Using MCP Resources with @ mentions:**
```
@fhir-mcp-server:patient://597179
```

**Using MCP Prompts as slash commands:**
```
/mcp__fhir_mcp_server__get_capabilities
```

**Check MCP server status:**
```
/mcp
```

This will show:
- Connection status for all servers
- Available tools and capabilities
- Authentication status (if applicable)

## Part 3: Alternative - Using Code Execution with FHIR MCP Server

### Step 6: Using Claude's Code Execution with FHIR MCP Server

Alternatively, Claude can directly interact with your FHIR MCP Server using code execution. No configuration needed - just ask Claude to run code that connects to your server.

#### Available FHIR MCP Tools

Your server running at `http://localhost:8004` provides these tools:

- **get_capabilities**: Get FHIR server capabilities and connection info
- **search**: Search FHIR resources (Patient, Observation, Medication, etc.)
- **read**: Read specific FHIR resources by ID
- **get_patient_comprehensive_data**: Get complete patient data for analysis
- **get_tool_config**: Get tool configuration for AI agents

#### Basic Code Examples

**Simple Health Check:**
```python
import requests
response = requests.get("http://localhost:8004/health")
print(response.json())
```

**Get Server Capabilities:**
```python
import requests
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_capabilities",
        "arguments": {}
    }
}
response = requests.post("http://localhost:8004/rpc", json=payload)
print(response.json())
```

**Search for Patients:**
```python
import requests
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search",
        "arguments": {
            "type": "Patient",
            "searchParam": {"name": "John"}
        }
    }
}
response = requests.post("http://localhost:8004/rpc", json=payload)
print(response.json())
```

**Read Specific Patient:**
```python
import requests
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "read",
        "arguments": {
            "type": "Patient",
            "id": "597179"
        }
    }
}
response = requests.post("http://localhost:8004/rpc", json=payload)
print(response.json())
```

#### Enhanced Client Example with User-Friendly Output

For a better testing experience, here's an enhanced client example with formatted output:

```python
import requests
import json
from typing import Dict, Any
import re
from html import unescape

def format_html_content(html_content: str) -> str:
    """Convert HTML content to a more readable format"""
    if not html_content:
        return ""
    
    # Remove HTML tags but preserve the structure
    html_content = unescape(html_content)
    
    # Extract patient name from hapiHeaderText
    name_match = re.search(r'<div class="hapiHeaderText">([^<]+)<b>([^<]+)</b>', html_content)
    if name_match:
        first_name = name_match.group(1).strip()
        last_name = name_match.group(2).strip()
        formatted = f"👤 Patient: {first_name} {last_name}\n"
    else:
        formatted = "👤 Patient Information:\n"
    
    # Extract table rows with property information
    table_pattern = r'<tr><td>([^<]+)</td><td>([^<]+)</td></tr>'
    matches = re.findall(table_pattern, html_content)
    
    for label, value in matches:
        # Clean up the value by removing HTML tags
        clean_value = re.sub(r'<[^>]+>', ' ', value)
        clean_value = re.sub(r'\s+', ' ', clean_value).strip()
        
        # Add appropriate emojis for common fields
        emoji = ""
        if "address" in label.lower():
            emoji = "🏠"
        elif "date of birth" in label.lower() or "birth" in label.lower():
            emoji = "🎂"
        elif "phone" in label.lower():
            emoji = "📞"
        elif "email" in label.lower():
            emoji = "📧"
        elif "gender" in label.lower():
            emoji = "⚧️"
        
        formatted += f"  {emoji} {label}: {clean_value}\n"
    
    return formatted

def format_fhir_response_data(data: Dict[Any, Any]) -> str:
    """Format FHIR response data for better readability"""
    formatted_lines = []
    
    def format_value(key: str, value: Any, indent: int = 0) -> None:
        prefix = "  " * indent
        
        if key == "div" and isinstance(value, str) and value.startswith("<div"):
            # Special handling for HTML narrative content
            formatted_lines.append(f"{prefix}📄 Narrative Content:")
            html_formatted = format_html_content(value)
            for line in html_formatted.split('\n'):
                if line.strip():
                    formatted_lines.append(f"{prefix}  {line}")
        elif key == "resourceType":
            formatted_lines.append(f"{prefix}📋 Resource Type: {value}")
        elif key == "id":
            formatted_lines.append(f"{prefix}🔑 ID: {value}")
        elif key == "status":
            status_emoji = "✅" if value == "active" else "⏸️"
            formatted_lines.append(f"{prefix}{status_emoji} Status: {value}")
        elif isinstance(value, dict):
            formatted_lines.append(f"{prefix}📁 {key}:")
            for sub_key, sub_value in value.items():
                format_value(sub_key, sub_value, indent + 1)
        elif isinstance(value, list):
            formatted_lines.append(f"{prefix}📋 {key}:")
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    formatted_lines.append(f"{prefix}  [{i}]:")
                    for sub_key, sub_value in item.items():
                        format_value(sub_key, sub_value, indent + 2)
                else:
                    formatted_lines.append(f"{prefix}  - {item}")
        else:
            formatted_lines.append(f"{prefix}{key}: {value}")
    
    if isinstance(data, dict):
        for key, value in data.items():
            format_value(key, value)
    else:
        formatted_lines.append(str(data))
    
    return '\n'.join(formatted_lines)

def print_response(title: str, response: requests.Response) -> None:
    """Print response in a user-friendly format"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Success!")
    else:
        print("❌ Failed!")
    
    try:
        data = response.json()
        print(f"\nResponse Data:")
        
        # Check if this looks like a FHIR response with patient data
        if isinstance(data, dict) and any(key in data for key in ['resourceType', 'entry', 'result']):
            formatted_data = format_fhir_response_data(data)
            print(formatted_data)
        else:
            # Fallback to pretty JSON for other responses
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
    except json.JSONDecodeError:
        print(f"\nRaw Response: {response.text}")
    except Exception as e:
        print(f"\nError parsing response: {e}")
    
    print(f"{'='*60}\n")

# Usage Examples:

# 1. Health Check
response = requests.get("http://localhost:8004/health")
print_response("Health Check", response)

# 2. Get Server Capabilities
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_capabilities",
        "arguments": {}
    }
}
response = requests.post("http://localhost:8004/rpc", json=payload)
print_response("Get Server Capabilities", response)

# 3. Search for Patients
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "search",
        "arguments": {
            "type": "Patient",
            "searchParam": {"name": "John"}
        }
    }
}
response = requests.post("http://localhost:8004/rpc", json=payload)
print_response("Search for Patients named 'John'", response)

# 4. Read Specific Patient
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "read",
        "arguments": {
            "type": "Patient",
            "id": "597179"
        }
    }
}
response = requests.post("http://localhost:8004/rpc", json=payload)
print_response("Read Patient by ID (597179)", response)
```

#### Interactive Patient Testing Example

For testing multiple patients interactively:

```python
def select_patient_id() -> str:
    """Interactive patient selection menu"""
    patients = {
        1: ("597179", "Serena Mustermann"),
        2: ("597217", "Ed Tan"),
        3: ("597213", "Grishma Methaila"),
        4: ("597173", "Sowmya Mellatur Sreedhar"),
        5: ("597220", "Dillon Thompson")
    }
    
    print("📋 Available Patients:")
    print("=" * 40)
    for serial, (patient_id, name) in patients.items():
        print(f"{serial}. {name} (ID: {patient_id})")
    print("0. 🚪 Exit")
    print("=" * 40)
    
    while True:
        try:
            choice = input("\n👆 Select a patient (1-5) or 0 to exit: ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("👋 Exiting patient testing...")
                return "exit"
            elif choice_num in patients:
                selected_id, selected_name = patients[choice_num]
                print(f"✅ Selected: {selected_name} (ID: {selected_id})\n")
                return selected_id
            else:
                print("❌ Invalid choice. Please select a number between 0-5.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\n🚫 Operation cancelled by user.")
            return "exit"

# Interactive patient testing loop
print("🔄 Patient Testing Loop")
print("You can now test multiple patients. Enter 0 when you want to exit.\n")

while True:
    selected_patient_id = select_patient_id()
    
    if selected_patient_id == "exit":
        break
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "read",
            "arguments": {
                "type": "Patient",
                "id": selected_patient_id
            }
        }
    }
    response = requests.post("http://localhost:8004/rpc", json=payload)
    print_response(f"Read Patient by ID ({selected_patient_id})", response)
    
    print("🔄 Ready for next patient selection...\n")

print("🎉 All tests completed!")
```

#### Expected Output Format

With the enhanced formatting, instead of raw JSON, you'll see output like:

```
============================================================
🔍 Read Patient by ID (597179)
============================================================
Status Code: 200
✅ Success!

Response Data:
📋 Resource Type: Patient
🔑 ID: 597179
✅ Status: active
📄 Narrative Content:
  👤 Patient: Serena Mustermann
    🏠 Address: Sket near DLF Avenue Delhi New Delhi India
    🎂 Date of birth: 01 January 1990
📁 name:
  [0]:
    family: Mustermann
    given: Serena
📁 telecom:
  [0]:
    system: phone
    value: +91-9876543210
============================================================
```



### Step 7: Complete Example Client

A complete, enhanced client example is available in the repository:
- **File**: `fhir_mcp_client_examples/basic-client-test.py`
- **Features**: 
  - User-friendly formatted output
  - HTML content parsing for FHIR narrative
  - Interactive patient selection menu
  - Loop testing functionality
  - Proper error handling

To run the complete example:
```bash
cd fhir_mcp_client_examples
python basic-client-test.py
```

### Step 8: How to Use with Claude

Simply ask Claude to run code that interacts with your FHIR server. For example:

```
Can you write and run Python code to check if my FHIR MCP server at localhost:8004 is healthy?
```

```
Please search for patients with the name "Smith" using my FHIR MCP server and show the results.
```

```
Can you get comprehensive patient data for patient ID "123" from my FHIR server and analyze it?
```

```
Can you run the enhanced client code to test my FHIR server with better formatted output?
```

### Step 9: Verify FHIR Server Connection

Test the connection by asking Claude:

```
Can you run code to check my FHIR MCP server status and show me what capabilities are available?
```

Claude will execute Python code to:
- Check server health at `http://localhost:8004/health`
- Query available tools and capabilities
- Test the MCP connection
- Display server information and FHIR endpoint details

## Part 4: Using FHIR MCP Server from Claude AI Chat

### Step 10: Get Server Capabilities

Start by checking the FHIR server capabilities:

```
Can you get the FHIR server capabilities using the get_capabilities tool?
```

Claude will use the `get_capabilities` tool and return information about:
- FHIR server software
- FHIR version (R4)
- Supported formats
- Server status
- Connection details

### Step 11: Search for Patients

To search for patients, use natural language requests:

```
Can you search for patients with the name "John" using the FHIR search tool?
```

Claude will use the `search` tool with parameters like:
- **type**: "Patient"
- **searchParam**: {"name": "John"}

### Step 12: Retrieve Specific Patient Data

To get a specific patient by ID:

```
Can you retrieve patient data for patient ID "example-patient-id" using the read tool?
```

Claude will use the `read` tool with:
- **type**: "Patient"
- **id**: "example-patient-id"

### Step 13: Get Comprehensive Patient Data

For AI-powered patient assessment, use the comprehensive data tool:

```
Can you get comprehensive patient data for patient ID "123" for clinical analysis?
```

Claude will use the `get_patient_comprehensive_data` tool to gather:
- Patient demographics
- Active conditions
- Recent observations
- Current medications
- Recent encounters

## Common Usage Examples

### Example 1: Patient Search and Analysis

```
I need to find patients with diabetes and analyze their recent lab results. Can you help me search for patients with diabetes and then get their comprehensive data?
```

### Example 2: Medication Review

```
Can you search for patients on a specific medication like "metformin" and review their current medication list?
```

### Example 3: Vital Signs Analysis

```
Please find patient ID "456" and analyze their recent vital signs and observations for any concerning trends.
```

### Example 4: Condition Monitoring

```
Can you search for patients with hypertension and check their recent blood pressure readings?
```

## Advanced Configuration Options

### Custom FHIR Server

To connect to a different FHIR server, update the environment variables:

```env
FHIR_MCP_FHIR__BASE_URL=https://your-fhir-server.com/fhir
FHIR_MCP_FHIR__ACCESS_TOKEN=your_bearer_token_here
```

### Authentication

For FHIR servers requiring authentication:

```env
FHIR_MCP_FHIR__ACCESS_TOKEN=Bearer_your_token_here
```

### Debug Mode

To enable debug logging:

```bash
python -m fhir_mcp_server --log-level DEBUG
```

## Troubleshooting

### Common Issues and Solutions

1. **Connection Refused**
   - Verify the FHIR MCP Server is running on the correct port
   - Check firewall settings
   - Ensure the server URL `http://localhost:8004` is accessible

2. **FHIR Authentication Errors**
   - Verify the FHIR server URL is accessible
   - Check if access token is required and properly configured
   - Test FHIR server access directly with curl

3. **Code Execution Errors**
   - Check Python syntax in your requests to Claude
   - Verify JSON-RPC format in payload
   - Check server logs for detailed error messages

4. **No Data Returned**
   - Check if the FHIR server has the requested data
   - Verify search parameters are correct
   - Test with known patient IDs

### Checking Server Logs

To view server logs for troubleshooting:

```bash
# If running with Docker
docker logs fhir-mcp-server

# If running manually
python -m fhir_mcp_server --log-level DEBUG
```

### Testing Server Endpoints

You can test the server directly:

```bash
# Health check
curl http://localhost:8004/health

# Server info
curl http://localhost:8004/info

# MCP capabilities test
curl -X POST http://localhost:8004/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_capabilities",
      "arguments": {}
    }
  }'
```

## Security Considerations

- Always use HTTPS in production environments
- Secure your FHIR server access tokens
- Limit network access to the MCP server
- Monitor access logs for unusual activity
- Keep dependencies updated

## Best Practices

1. **Start Simple**: Begin with basic patient searches before complex analyses
2. **Verify Data**: Always verify patient data before making clinical decisions
3. **Error Handling**: Be prepared to handle cases where data is not available
4. **Performance**: Use specific search parameters to limit result sets
5. **Privacy**: Ensure compliance with healthcare data privacy regulations

## Next Steps

Once you have the FHIR MCP Server working with Claude AI, you can:

1. Integrate with your organization's FHIR server
2. Develop custom healthcare AI workflows
3. Create automated patient monitoring systems
4. Build clinical decision support tools
5. Implement population health analytics

For more advanced features and deployment options, refer to the main [README.md](../README.md) and other documentation in the `docs/` directory.
