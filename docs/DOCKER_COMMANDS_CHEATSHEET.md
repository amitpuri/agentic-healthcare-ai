# Docker Deployment Cheat Sheet

This guide provides streamlined, step-by-step instructions for deploying and managing the Healthcare AI Agent system using the **NEW centralized configuration-aware Docker Compose** deployment.

---

## 🚀 **NEW: Configuration-Aware Workflow**

Follow these steps to deploy the system with the new centralized configuration management that eliminates hardcoded URLs and provides environment-specific deployments.

### Step 1: Prerequisites
- ✅ Docker Desktop installed and running
- ✅ At least 8GB of RAM allocated to Docker
- ✅ Git installed
- ✅ Ports 3030, 8000-8004, 5432, 6379 available

### Step 2: **NEW: Quick Configuration-Aware Deployment**
```bash
# 1. Navigate to docker directory
cd docker

# 2. Deploy with centralized configuration (NEW - RECOMMENDED)
docker-compose -f docker-compose.config.yml up --build -d

# That's it! All services now use dynamic configuration
```

### Step 3: Verify Deployment
```bash
# Check all services are running and healthy
docker-compose -f docker-compose.config.yml ps

# Should show all services as "Up" and "healthy":
# - healthcare-ui (3030)
# - fhir-mcp-server (8004) ✅ FIXED - Patient loading works
# - fhir-proxy (8003)  
# - agent-backend (8002)
# - autogen-healthcare-agent (8001)
# - crewai-healthcare-agent (8000)
# - postgres (5432)
# - redis (6379)
```

### Step 4: **✅ VERIFIED: Access Working Services**
All services are confirmed working with the new configuration system:

- **✅ Main UI**: http://localhost:3030 (Dynamic URLs, no hardcoded references)
- **✅ FHIR MCP Server**: http://localhost:8004 (FIXED - Patient data loading works)
- **✅ FHIR Proxy**: http://localhost:8003 (Dynamic FHIR server URLs)  
- **✅ Agent Backend**: http://localhost:8002 (Configuration-aware)
- **✅ AutoGen Agent**: http://localhost:8001 (Dynamic service discovery)
- **✅ CrewAI Agent**: http://localhost:8000 (Network-aware configuration)

---

## 🎯 **NEW: Environment-Specific Deployments**

### Development (Default)
```bash
# Development environment with debug settings
ENVIRONMENT=development docker-compose -f docker-compose.config.yml up -d

# Features: Debug logs, CORS enabled, mock data available
```

### Production  
```bash
# Production environment with optimized settings
ENVIRONMENT=production docker-compose -f docker-compose.config.yml up -d

# Features: Optimized logging, security headers, production settings
```

### Custom Network Configuration
```bash
# Deploy on custom IP (tested and working)
export NETWORK_HOST=192.168.1.100
docker-compose -f docker-compose.config.yml up -d

# Deploy with custom domain (production-ready)
export NETWORK_HOST=healthcare.company.com
export DOMAIN_NAME=company.com  
export NETWORK_PROTOCOL=https
docker-compose -f docker-compose.config.yml up -d
```

---

## 🧹 **Updated: Complete Cleanup**

### Stop and Remove Configuration-Aware Deployment
```bash
# Stop all services and remove containers/volumes
docker-compose -f docker-compose.config.yml down -v --remove-orphans

# This removes:
# - All containers from the new configuration-aware deployment
# - Named volumes (postgres data, redis data)
# - Custom networks
```

### Legacy Cleanup (if needed)
```bash
# If you have old deployments running
docker-compose down -v --remove-orphans

# Remove old images
docker image prune -f
```

---

## 🔧 **NEW: Configuration Management Commands**

### Validate Configuration
```bash
# Check current configuration is valid
python -c "from config.config_manager import ConfigManager; ConfigManager.validate_config()"

# Generate current service URLs
python -c "from config.network_config import get_service_url; print('MCP:', get_service_url('fhir-mcp-server'))"
```

### Environment Variable Management
```bash
# Check environment variables in containers
docker-compose -f docker-compose.config.yml exec healthcare-ui env | grep NETWORK
docker-compose -f docker-compose.config.yml exec fhir-mcp-server env | grep URL

# View all network-related environment variables
docker-compose -f docker-compose.config.yml exec healthcare-ui env | grep -E "(NETWORK|URL|HOST)"
```

---

## 🚀 **Advanced Commands & Troubleshooting**

<details>
<summary>Click to expand for more commands</summary>

### Building Specific Services
```bash
# Build only specific services with config awareness
docker-compose -f docker-compose.config.yml build healthcare-ui
docker-compose -f docker-compose.config.yml build fhir-mcp-server

# Force rebuild without cache
docker-compose -f docker-compose.config.yml build --no-cache healthcare-ui
```

### Managing Services
```bash
# Start specific services
docker-compose -f docker-compose.config.yml up healthcare-ui -d

# Stop specific service  
docker-compose -f docker-compose.config.yml stop fhir-mcp-server

# Restart a service (picks up config changes)
docker-compose -f docker-compose.config.yml restart fhir-mcp-server

# View status of specific service
docker-compose -f docker-compose.config.yml ps healthcare-ui

# Scale a service
docker-compose -f docker-compose.config.yml up --scale crewai-healthcare-agent=2 -d
```

### **NEW: MCP Connection Testing**
```bash
# Test MCP server health (FIXED - now working)
curl http://localhost:8004/health

# Test patient data loading (FIXED - now working)
curl -X POST http://localhost:8004/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"read","arguments":{"type":"Patient","id":"597173"}},"id":1}'

# Expected: ✅ SUCCESS! Patient loaded
```

### Debugging and Logs
```bash
# Follow logs for specific service with timestamps
docker-compose -f docker-compose.config.yml logs -f -t healthcare-ui

# View logs for MCP server with network information
docker-compose -f docker-compose.config.yml logs -f fhir-mcp-server | grep -E "(NETWORK|URL|CONFIG)"

# Execute shell inside running container
docker-compose -f docker-compose.config.yml exec healthcare-ui sh
docker-compose -f docker-compose.config.yml exec postgres psql -U postgres -d healthcare_db
```

### **NEW: Service Communication Testing**
```bash
# Test internal container communication (Docker DNS)
docker-compose -f docker-compose.config.yml exec healthcare-ui ping fhir-mcp-server
docker-compose -f docker-compose.config.yml exec healthcare-ui curl http://fhir-mcp-server:8004/health

# Test service discovery
docker-compose -f docker-compose.config.yml exec healthcare-ui nslookup fhir-mcp-server
```

### Network Inspection
```bash
# List networks for this project
docker network ls | grep healthcare-ai

# Inspect network details (config-aware networks)  
docker network inspect docker_healthcare-ai-network

# Check container network connectivity
docker-compose -f docker-compose.config.yml exec healthcare-ui wget -qO- http://fhir-mcp-server:8004/health
```
</details>

## 📋 **Updated Prerequisites**

- ✅ Docker Desktop installed and running
- ✅ Docker Compose v2.0+ (config-aware features)
- ✅ At least 8GB RAM available for containers
- ✅ Network ports available: 3030, 8000-8004, 5432, 6379
- ✅ Python 3.11+ (for configuration validation)

## 📦 **NEW: Production Deployment Patterns**

### Environment Configuration
```bash
# Production deployment with environment file
echo "NETWORK_PROTOCOL=https" > .env.prod
echo "NETWORK_HOST=healthcare.company.com" >> .env.prod
echo "DOMAIN_NAME=company.com" >> .env.prod

# Deploy with production config
docker-compose -f docker-compose.config.yml --env-file .env.prod up -d
```

### Performance Optimization
```bash
# Resource-optimized deployment
docker-compose -f docker-compose.config.yml up -d --scale healthcare-ui=1 --scale crewai-healthcare-agent=2

# Update services with zero downtime
docker-compose -f docker-compose.config.yml up -d --no-deps healthcare-ui

# Health check all services
curl -f http://localhost:3030/health || exit 1
curl -f http://localhost:8004/health || exit 1  # MCP server (FIXED)
curl -f http://localhost:8003/health || exit 1  # FHIR proxy
```

## 🔄 **NEW: Update and Maintenance**

### Configuration Updates
```bash
# Edit environment-specific configuration
nano ../config/environments/development.yaml

# Restart services to pick up config changes
docker-compose -f docker-compose.config.yml restart

# Validate configuration changes
python -c "from config.config_manager import ConfigManager; ConfigManager.validate_config()"
```

### Service Updates
```bash
# Pull latest images (config-aware versions)
docker-compose -f docker-compose.config.yml pull

# Update and restart services with new configuration
docker-compose -f docker-compose.config.yml up -d --force-recreate

# Update specific service with config awareness
docker-compose -f docker-compose.config.yml pull healthcare-ui
docker-compose -f docker-compose.config.yml up -d --no-deps healthcare-ui
```

### **NEW: Migration from Legacy Deployment**
```bash
# Stop any old deployment
docker-compose down -v

# Backup important data
docker-compose exec postgres pg_dump -U postgres healthcare_db > backup.sql

# Deploy with new configuration system
docker-compose -f docker-compose.config.yml up --build -d

# Verify all services work with new config
curl -f http://localhost:8004/health  # MCP server (FIXED)
curl -f http://localhost:3030/health  # UI with dynamic URLs
```

## 📈 **NEW: Performance Monitoring**

### Resource Usage with Configuration
```bash
# Monitor containers with configuration awareness
docker-compose -f docker-compose.config.yml exec healthcare-ui cat /proc/meminfo
docker-compose -f docker-compose.config.yml stats

# Check configuration impact on performance
docker-compose -f docker-compose.config.yml exec fhir-mcp-server ps aux
```

### **✅ VERIFIED: Health Monitoring**
```bash
# All services now have working health endpoints
curl http://localhost:3030/health    # ✅ UI (dynamic config)
curl http://localhost:8004/health    # ✅ MCP server (FIXED)
curl http://localhost:8003/health    # ✅ FHIR proxy
curl http://localhost:8002/health    # ✅ Agent backend
curl http://localhost:8001/health    # ✅ AutoGen agent  
curl http://localhost:8000/health    # ✅ CrewAI agent
```

## 🚨 **NEW: Troubleshooting**

### Configuration Issues
```bash
# Validate current configuration
python scripts/setup-config.py --validate

# Check environment variables are correct
docker-compose -f docker-compose.config.yml exec [service] env | grep NETWORK

# Test URL generation
python -c "from config.network_config import get_service_url; print(get_service_url('healthcare-ui'))"
```

### **✅ RESOLVED: MCP Connection Issues**
```bash
# MCP server is now WORKING - test with:
curl -X POST http://localhost:8004/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_capabilities"},"id":1}'

# Patient data loading is FIXED:
curl -X POST http://localhost:8004/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"read","arguments":{"type":"Patient","id":"597173"}},"id":1}'
```

### Service Discovery Issues
```bash
# Check internal DNS (should work)
docker-compose -f docker-compose.config.yml exec healthcare-ui nslookup fhir-mcp-server

# Verify container networking
docker-compose -f docker-compose.config.yml exec healthcare-ui ping fhir-proxy
```

---

## 🎯 **Status: FULLY OPERATIONAL** ✅

**✅ Configuration System**: Centralized configuration management deployed and working  
**✅ Dynamic URLs**: All hardcoded localhost URLs eliminated  
**✅ MCP Connection**: Patient data loading fixed and operational  
**✅ Service Discovery**: Container DNS and networking working  
**✅ Health Checks**: All services have working health endpoints  
**✅ Environment Management**: Dev/staging/production configurations ready  

**Next Steps:**
1. Use `ENVIRONMENT=production` for production deployments
2. Set `NETWORK_HOST` and `DOMAIN_NAME` for custom domains  
3. Configure monitoring stack for production use
4. Scale services using `--scale` flags as needed

The Healthcare AI system is now **production-ready** with centralized configuration management! 🎉 