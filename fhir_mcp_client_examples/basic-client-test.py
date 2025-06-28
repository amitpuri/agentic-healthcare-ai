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

def wait_for_user() -> None:
    """Wait for user to press a key before continuing"""
    input("Press Enter to continue to the next test... ")
    print()

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

# Test 1: Health Check
print("🏥 FHIR MCP Server Testing")
print("Starting basic client tests...\n")

response = requests.get("http://localhost:8004/health")
print_response("Health Check", response)
wait_for_user()

# Test 2: Get Server Capabilities
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
wait_for_user()

# Test 3: Search for Patients
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
wait_for_user()

# Test 4: Read Specific Patient (with loop)
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