# Healthcare AI Agent Deployment Guide

This guide provides complete instructions for deploying the Healthcare AI Agent system using the new centralized configuration management system. The system now features dynamic URL generation, environment-specific configurations, and resolved MCP connection issues.

## 🚀 Quick Start Options

### Option 1: Docker Compose with Centralized Config (Recommended)
```bash
# Use the new configuration-aware deployment
cd docker
# Change .env environment variables, as per your deployment
cp ../env.template ../.env
docker-compose -f docker-compose.config.yml up --build -d
```

### Option 2: Kubernetes (Production Ready)
```bash
cd kubernetes
./deploy.sh
```

## 📁 Project Structure

```
agentic-healthcare-ai/
├── config/                     # 🔧 NEW: Centralized Configuration
│   ├── base.yaml              # Base configuration with network settings
│   ├── environments/          # Environment-specific overrides
│   │   ├── development.yaml   # Development settings
│   │   ├── staging.yaml       # Staging configuration
│   │   └── production.yaml    # Production settings
│   ├── config_manager.py      # Configuration management with URL generation
│   ├── network_config.py      # Network configuration helper
│   └── secrets.py            # Secrets management
├── docker/                     # 🐳 Complete Docker Compose deployment
│   ├── docker-compose.config.yml  # NEW: Config-aware deployment
│   ├── docker-compose.simple.yml  # Simplified deployment
│   ├── docker-compose.yml     # Legacy main compose file
│   └── services/              # Service configurations
├── ui/                        # React frontend with dynamic URLs
├── shared/                    # Shared libraries with config integration
└── [agents and services]      # All services now config-aware
```

## 🔧 **NEW: Centralized Configuration System**

### Key Features
- ✅ **Dynamic URL Generation**: No more hardcoded localhost URLs
- ✅ **Environment-Specific Overrides**: Easy dev/staging/prod management
- ✅ **Network-Aware Configuration**: Adapts to different deployment scenarios
- ✅ **Secure Secrets Management**: Multiple backends supported
- ✅ **Docker Integration**: Environment variables passed to all services

### Network Configuration

The system now uses dynamic network configuration:

```yaml
# config/base.yaml
network:
  host: "localhost"           # Default host
  protocol: "http"           # http or https
  external_host: "localhost" # External/public host
  domain_name: ""            # Domain for subdomain routing

services:
  fhir-mcp-server:
    port: 8004
    health_endpoint: "/health"
  healthcare-ui:
    port: 3030
    path: "/"
```

### Environment Variables

Set these in your environment or `.env` file:
```bash
# Network Configuration
NETWORK_HOST=localhost
NETWORK_PROTOCOL=http
EXTERNAL_HOST=localhost
DOMAIN_NAME=""

# Service-specific (optional overrides)
FHIR_MCP_URL=http://localhost:8004
HEALTHCARE_UI_URL=http://localhost:3030
```

## 🐳 Docker Compose Deployment

### **NEW: Configuration-Aware Deployment**

```bash
cd docker

# Deploy with centralized configuration
docker-compose -f docker-compose.config.yml up --build -d

# Check all services are healthy
docker-compose -f docker-compose.config.yml ps

# View service logs
docker-compose -f docker-compose.config.yml logs -f [service_name]
```

### **Fixed Services Included**
- **Healthcare AI Agents**: CrewAI (8000) + Autogen (8001) ✅
- **Frontend UI**: React app with dynamic URLs (3030) ✅ 
- **FHIR MCP Server**: **FIXED** - Patient data loading now works (8004) ✅
- **FHIR Proxy**: Lightweight FHIR proxy (8003) ✅
- **Agent Backend**: Backend API (8002) ✅
- **Database**: PostgreSQL with sample data (5432) ✅
- **Cache**: Redis (6379) ✅

### **Resolved Issues**
- ✅ **MCP Connection Fixed**: Patient data loading now works correctly
- ✅ **Docker Build Context**: All services build successfully
- ✅ **Dependency Conflicts**: AI framework versions resolved
- ✅ **Health Checks**: All services have working health endpoints
- ✅ **Dynamic URLs**: No more hardcoded localhost references

## ☸️ Kubernetes Deployment

Kubernetes deployment now uses the centralized configuration system via ConfigMaps:

```bash
cd kubernetes

# Generate ConfigMaps from centralized config
kubectl apply -f manifests/configmap-generator.yaml

# Deploy everything
./deploy.sh

# Check configuration
kubectl get configmap -n healthcare-ai
kubectl describe configmap app-config -n healthcare-ai
```

## 🌐 Access URLs (Development)

With the new dynamic configuration system:

### Default Development URLs
- **Main UI**: http://localhost:3030
- **FHIR MCP Server**: http://localhost:8004 (✅ **FIXED**)
- **FHIR Proxy**: http://localhost:8003
- **Agent Backend**: http://localhost:8002
- **AutoGen Agent**: http://localhost:8001
- **CrewAI Agent**: http://localhost:8000

### Custom Network Configuration
For custom deployments, set environment variables:
```bash
# Deploy on custom IP
export NETWORK_HOST=192.168.1.100
docker-compose -f docker-compose.config.yml up -d

# Deploy with domain
export NETWORK_HOST=healthcare.local
export DOMAIN_NAME=healthcare.local
docker-compose -f docker-compose.config.yml up -d
```

## 🔧 **MCP Connection Resolution**

The FHIR MCP Server had connectivity issues that have been **completely resolved**:

### **Previous Issue:**
```
❌ Failed to load patient 597173: MCP error: Failed to read Patient/597173
```

### **Resolution:**
- ✅ Fixed FHIR client search result handling (list vs dict responses)
- ✅ Implemented dual endpoint support (`/` and `/rpc`)
- ✅ Added proper CORS headers for browser requests
- ✅ Corrected JSON-RPC protocol implementation

### **Verification:**
```bash
# Test MCP connection
curl -X POST http://localhost:8004/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"read","arguments":{"type":"Patient","id":"597173"}},"id":1}'

# Expected successful response:
# ✅ SUCCESS! Patient loaded: Resource Type: Patient, ID: 597173
```

## ⚙️ Configuration Management

### Environment-Specific Configuration

```bash
# Development (default)
ENVIRONMENT=development docker-compose -f docker-compose.config.yml up -d

# Staging
ENVIRONMENT=staging docker-compose -f docker-compose.config.yml up -d

# Production
ENVIRONMENT=production docker-compose -f docker-compose.config.yml up -d
```

### Configuration Validation

The system now validates configuration on startup:
```bash
# Validate configuration
python -m config.config_manager validate

# Generate URLs for current environment
python -m config.network_config urls
```

## 🔧 Development Workflow

### **NEW: Configuration-Aware Development**
```bash
cd docker

# Development with hot reload and debug settings
ENVIRONMENT=development docker-compose -f docker-compose.config.yml up -d

# Edit configuration
nano ../config/environments/development.yaml

# Restart services to pick up config changes
docker-compose -f docker-compose.config.yml restart

# View service logs with network info
docker-compose -f docker-compose.config.yml logs -f fhir-mcp-server
```

### Debug and Testing
```bash
# Test MCP functionality
docker-compose -f docker-compose.config.yml exec healthcare-ui curl http://fhir-mcp-server:8004/health

# Check configuration in containers
docker-compose -f docker-compose.config.yml exec fhir-mcp-server env | grep NETWORK

# Validate service connectivity
docker-compose -f docker-compose.config.yml exec healthcare-ui ping fhir-mcp-server
```

## 🔄 Migration from Legacy Deployment

If you're migrating from the old hardcoded system:

```bash
# Stop old deployment
docker-compose down -v

# Backup any important data
docker-compose exec postgres pg_dump -U postgres healthcare_db > backup.sql

# Deploy with new configuration system
docker-compose -f docker-compose.config.yml up --build -d

# Verify MCP connection works
curl -f http://localhost:8004/health
```

## 🚨 Troubleshooting

### MCP Connection Issues
```bash
# Check MCP server health
curl http://localhost:8004/health

# Test patient data loading
curl -X POST http://localhost:8004/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_capabilities"},"id":1}'
```

### Configuration Issues
```bash
# Validate current configuration
python scripts/setup-config.py --validate

# Check environment variables in containers
docker-compose -f docker-compose.config.yml exec [service] env | grep NETWORK
```

### Service Discovery Issues
```bash
# Check internal DNS resolution
docker-compose -f docker-compose.config.yml exec healthcare-ui nslookup fhir-mcp-server

# Verify all services are running
docker-compose -f docker-compose.config.yml ps
```

## 📈 Production Considerations

### Security
- Set `NETWORK_PROTOCOL=https` for production
- Configure proper domain names via `DOMAIN_NAME`
- Use external secrets management for sensitive data

### Performance
- Enable monitoring stack with Prometheus/Grafana
- Configure resource limits in compose file
- Use production-optimized environment settings

### High Availability
- Deploy with Kubernetes for auto-scaling
- Use external databases for persistence
- Configure health checks and restart policies

---

**Note**: This deployment guide reflects the latest improvements including centralized configuration management, resolved MCP connectivity issues, and production-ready deployment options. 
