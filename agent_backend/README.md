# Real AI Agent Backend

This backend service provides real integration with AutoGen and CrewAI frameworks, featuring comprehensive LLM communication tracking for healthcare AI agents.

## Features

### 🤖 **Multi-Framework Support**
- **AutoGen**: Multi-agent conversational AI with group chat management
- **CrewAI**: Specialized agent crews with role-based collaboration
- **Real-time LLM Communication Tracking**: Monitor every interaction

### 📊 **Comprehensive Tracking**
- Token usage and cost estimation
- Response times and performance metrics
- Message-level conversation logging
- Agent execution lifecycle tracking
- Function calls and tool usage monitoring

### 🏥 **Healthcare Integration**
- FHIR R4 server integration
- Patient data retrieval and analysis
- Clinical decision support tools
- Drug interaction checking
- Risk assessment calculations

## Quick Start

### 1. Environment Setup

Create a `.env` file in the `agent_backend` directory:

```bash
# Required Configuration
OPENAI_API_KEY=your_openai_api_key_here
FHIR_SERVER_URL=https://hapi.fhir.org/baseR4

# Optional Configuration
WEBHOOK_URL=http://localhost:3000/webhook
LOG_LEVEL=INFO
```

### 2. Install Dependencies

```bash
cd agent_backend
pip install -r requirements.txt
```

### 3. Run the Service

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode  
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Docker Deployment

```bash
# Build and run with Docker Compose
cd docker
docker-compose -f docker-compose.agents.yml up -d

# Check service status
docker-compose -f docker-compose.agents.yml ps
```

## API Endpoints

### Health & Status
- `GET /api/health` - Service health check
- `GET /api/communications/stats` - Communication statistics

### AutoGen Integration
- `POST /api/autogen/comprehensive` - Comprehensive patient assessment
- `POST /api/autogen/emergency` - Emergency assessment with triage
- `POST /api/autogen/medication_review` - Medication reconciliation
- `POST /api/autogen/execute-task` - Execute single agent task

### CrewAI Integration  
- `POST /api/crewai/comprehensive` - Crew-based comprehensive assessment
- `POST /api/crewai/emergency` - Emergency crew assessment
- `POST /api/crewai/medication_review` - Medication review crew
- `POST /api/crewai/execute-task` - Execute single agent task

### Communication Tracking
- `GET /api/communications` - Get all LLM communications
- `GET /api/communications/{id}` - Get specific communication
- `GET /api/export/communications` - Export communication data

### Scenario Management
- `GET /api/scenarios` - Get all scenarios
- `GET /api/scenarios/{id}` - Get specific scenario
- `DELETE /api/scenarios/{id}` - Delete scenario

## Usage Examples

### 1. Execute AutoGen Comprehensive Assessment

```bash
curl -X POST "http://localhost:8000/api/autogen/comprehensive" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "patient_id": "597173",
    "scenario_config": {
      "type": "comprehensive",
      "patient_id": "597173", 
      "patient_name": "John Doe"
    },
    "agent_config": {
      "model": "gpt-4",
      "temperature": 0.1,
      "track_communications": true
    }
  }'
```

### 2. Execute CrewAI Emergency Assessment

```bash
curl -X POST "http://localhost:8000/api/crewai/emergency" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "patient_id": "597173",
    "scenario_config": {
      "type": "emergency",
      "patient_id": "597173",
      "patient_name": "John Doe",
      "chief_complaint": "Chest pain with shortness of breath",
      "urgency_level": "emergent"
    }
  }'
```

### 3. Get Communication Statistics

```bash
curl -X GET "http://localhost:8000/api/communications/stats" \
  -H "Authorization: Bearer your_api_key"
```

## Real Agent Console Integration

The React frontend includes a **Real Agent Console** that integrates with this backend:

### Features:
- ✅ **Live Scenario Execution**: Start real AutoGen/CrewAI scenarios
- ✅ **Real-time Communication Tracking**: Monitor LLM interactions
- ✅ **Performance Metrics**: Token usage, costs, response times  
- ✅ **Agent Status Monitoring**: Track agent execution states
- ✅ **Framework Switching**: Toggle between AutoGen and CrewAI
- ✅ **Configuration Management**: Set API keys and model parameters

### Access:
Navigate to `/real-agents` in the React application to use the real agent console.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │    │   FastAPI        │    │   AI Frameworks │
│                 │    │   Backend        │    │                 │
│ Real Agent      │◄──►│                  │◄──►│ AutoGen         │
│ Console         │    │ LLM Tracker      │    │ CrewAI          │
│                 │    │ Communication    │    │                 │
│ Agent Comm      │    │ Manager          │    │ OpenAI API      │
│ History         │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   FHIR Server    │
                       │   Patient Data   │
                       └──────────────────┘
```

## Communication Tracking Details

### Tracked Metrics:
- **Input/Output Tokens**: Precise token counting for cost management
- **Response Times**: End-to-end latency measurement  
- **Cost Estimation**: Real-time cost calculation based on model pricing
- **Function Calls**: Tool usage and function call monitoring
- **Error Handling**: Comprehensive error logging and recovery

### Data Structure:
```python
LLMCommunication {
    id: str
    agent_id: str
    agent_name: str
    framework: AutoGen | CrewAI
    provider: OpenAI | Azure | Anthropic
    model: str
    session_start: datetime
    session_end: datetime
    messages: List[LLMMessage]
    total_tokens: int
    cost_estimate: float
    response_time_ms: int
    final_response: str
    confidence_score: float
    function_calls_made: List[str]
    tools_used: List[str]
}
```

## Configuration Options

### Model Configuration:
```python
AgentConfig {
    model: "gpt-4" | "gpt-3.5-turbo" | "gpt-4-turbo"
    temperature: 0.0 - 1.0
    max_tokens: int
    track_communications: bool
}
```

### Scenario Types:
- **Comprehensive**: Full patient assessment with all agent specialties
- **Emergency**: Rapid triage and emergency assessment
- **Medication Review**: Focus on medication interactions and optimization

## Monitoring & Observability

### Health Checks:
- Service availability monitoring
- Database connectivity checks  
- FHIR server integration status
- Active agent session tracking

### Logging:
- Structured JSON logging
- Request/response tracking
- Error monitoring and alerting
- Performance metrics collection

## Security Considerations

### API Security:
- API key authentication
- Rate limiting protection
- Input validation and sanitization
- CORS configuration

### Data Privacy:
- Patient data encryption in transit
- Secure FHIR server communication
- Communication data anonymization options
- Audit trail maintenance

## Troubleshooting

### Common Issues:

1. **OpenAI API Key Not Working**:
   - Verify API key is correct and has sufficient credits
   - Check rate limits and usage quotas

2. **FHIR Server Connection Issues**:
   - Verify FHIR server URL accessibility
   - Check authentication tokens if required

3. **Agent Framework Errors**:
   - Ensure AutoGen/CrewAI dependencies are installed
   - Check Python path configuration

4. **Communication Tracking Not Working**:
   - Verify agent wrappers are applied correctly
   - Check tracker initialization

### Logs Location:
- Development: Console output
- Docker: `/app/logs/` volume
- Production: Configured log aggregation system

## Development

### Running Tests:
```bash
pytest tests/ -v --cov=main
```

### Code Quality:
```bash
black main.py
flake8 main.py
mypy main.py
```

### Contributing:
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

This project is licensed under the MIT License. See LICENSE file for details. 