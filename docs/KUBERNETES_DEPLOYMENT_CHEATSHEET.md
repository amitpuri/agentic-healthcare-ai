# Kubernetes Deployment Cheatsheet

This guide provides streamlined, step-by-step instructions for deploying and managing the Healthcare AI system on Kubernetes. **Updated with centralized configuration system and new services.**

---

## 🎯 Quick Reference

### New Services Added
- **FHIR MCP Server** (port 8004) - Patient data access via Model Context Protocol
- **Agent Backend** (port 8002) - AI coordination service
- **Dynamic Configuration** - Environment-based configuration generation

### NodePort Services (External Access)
| Service | Internal Port | External Port | URL |
|---------|---------------|---------------|-----|
| Healthcare UI | 80 | 30080 | http://localhost:30080 |
| FHIR MCP Server | 8004 | 30084 | http://localhost:30084 |
| FHIR Proxy | 8003 | 30083 | http://localhost:30083 |
| Agent Backend | 8002 | 30082 | http://localhost:30082 |
| CrewAI Agent | 8000 | 30000 | http://localhost:30000 |
| AutoGen Agent | 8001 | 30001 | http://localhost:30001 |

---

## 🚀 Workflow 1: Quick Deployment (Recommended)

### Method A: Automated Deployment with Dynamic Config
```bash
# Navigate to kubernetes directory
cd kubernetes

# Deploy with environment-specific configuration
./deploy.sh --environment production --generate-config

# Start port forwarding for all services
./port-forward.sh start
```

### Method B: Standard Deployment
```bash
# Navigate to kubernetes directory
cd kubernetes

# Standard deployment with static config
./deploy.sh

# Start essential services only
./port-forward.sh start-essential
```

---

## 🔧 Workflow 2: Manual Step-by-Step Deployment

### Step 1: Prerequisites
- Docker Desktop with Kubernetes enabled
- kubectl CLI installed
- Python 3.8+ (for config generation)
- At least 8GB RAM and 12GB disk space

### Step 2: Generate Configuration (Optional but Recommended)
```bash
# Generate environment-specific ConfigMap
python ../scripts/generate-k8s-configmap.py --environment production --output manifests/01-configmap-generated.yaml

# Review generated configuration
cat manifests/01-configmap-generated.yaml
```

### Step 3: Build All Docker Images
```bash
# Build all services using centralized docker-compose
cd ..
docker-compose -f docker/docker-compose.config.yml build

# Tag images for Kubernetes
docker tag healthcare-ai-crewai-fhir-agent healthcare-ai/crewai-healthcare-agent:latest
docker tag healthcare-ai-autogen-fhir-agent healthcare-ai/autogen-healthcare-agent:latest
docker tag healthcare-ai-agent-backend healthcare-ai/agent-backend:latest
docker tag healthcare-ai-fhir-mcp-server healthcare-ai/fhir-mcp-server:latest
docker tag healthcare-ai-fhir-proxy healthcare-ai/fhir-proxy:latest
docker tag healthcare-ai-ui healthcare-ai/healthcare-ui:latest

cd kubernetes
```

### Step 4: Deploy Resources in Order
```bash
# 1. Create namespace
kubectl apply -f manifests/00-namespace.yaml

# 2. Apply configuration (use generated or default)
kubectl apply -f manifests/01-configmap-generated.yaml  # or 01-configmap.yaml
kubectl apply -f manifests/02-secrets.yaml

# 3. Create storage
kubectl apply -f manifests/03-persistent-volumes.yaml

# 4. Deploy databases
kubectl apply -f manifests/04-database.yaml
kubectl apply -f manifests/05-redis.yaml

# 5. Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres -n healthcare-ai --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n healthcare-ai --timeout=120s

# 6. Deploy applications
kubectl apply -f manifests/06-healthcare-agents.yaml
kubectl apply -f manifests/11-fhir-proxy.yaml
kubectl apply -f manifests/07-healthcare-ui.yaml

# 7. Deploy monitoring
kubectl apply -f manifests/08-monitoring.yaml
kubectl apply -f manifests/09-elk-stack.yaml

# 8. Wait for all deployments
kubectl wait --for=condition=ready pod -l app=healthcare-ui -n healthcare-ai --timeout=180s
```

---

## 🌐 Workflow 3: Port Forwarding & Access

### Automated Port Forwarding (Recommended)

#### Linux/macOS/WSL:
```bash
# Start all services
./port-forward.sh start

# Start essential services only
./port-forward.sh start-essential

# Check status
./port-forward.sh status

# Stop all
./port-forward.sh stop
```

#### Windows PowerShell:
```powershell
# Start all services
.\port-forward.ps1 start

# Start essential services only
.\port-forward.ps1 start-essential

# Check status
.\port-forward.ps1 status

# Stop all
.\port-forward.ps1 stop
```

### Manual Port Forwarding
If you prefer manual control, run each in a separate terminal:

```bash
# Core Services (Essential)
kubectl port-forward service/healthcare-ui-service 3080:80 -n healthcare-ai
kubectl port-forward service/fhir-mcp-server 8004:8004 -n healthcare-ai
kubectl port-forward service/fhir-proxy 8003:8003 -n healthcare-ai

# AI Agents
kubectl port-forward service/agent-backend 8002:8002 -n healthcare-ai
kubectl port-forward service/crewai-healthcare-agent 8000:8000 -n healthcare-ai
kubectl port-forward service/autogen-healthcare-agent 8001:8001 -n healthcare-ai

# Monitoring
kubectl port-forward service/prometheus-service 9090:9090 -n healthcare-ai
kubectl port-forward service/grafana-service 3000:3000 -n healthcare-ai
kubectl port-forward service/kibana-service 5601:5601 -n healthcare-ai
```

---

## 🧹 Workflow 4: Cleanup

### Quick Cleanup
```bash
./cleanup.sh
```

### Manual Cleanup
```bash
# Delete namespace (removes everything)
kubectl delete namespace healthcare-ai

# Delete persistent volumes
kubectl delete pv --all

# Stop port forwards
./port-forward.sh stop  # or .\port-forward.ps1 stop

# Optional: Remove Docker images
docker rmi healthcare-ai/crewai-healthcare-agent:latest \
           healthcare-ai/autogen-healthcare-agent:latest \
           healthcare-ai/agent-backend:latest \
           healthcare-ai/fhir-mcp-server:latest \
           healthcare-ai/fhir-proxy:latest \
           healthcare-ai/healthcare-ui:latest
```

---

## 🎯 Service Access URLs

### External Access (NodePort)
| Service | URL | Description |
|---------|-----|-------------|
| **Healthcare UI** | http://localhost:30080 | Main application interface |
| **FHIR MCP Server** | http://localhost:30084 | Patient data access (MCP) |
| **FHIR Proxy** | http://localhost:30083 | CORS-enabled FHIR access |
| **Agent Backend** | http://localhost:30082 | AI coordination service |
| **CrewAI Agent** | http://localhost:30000 | Team-based AI agent |
| **AutoGen Agent** | http://localhost:30001 | Conversational AI agent |
| **Prometheus** | http://localhost:30090 | Metrics collection |
| **Grafana** | http://localhost:30300 | Dashboards (admin/admin) |
| **Kibana** | http://localhost:30561 | Log analysis |

### Port Forwarded Access
When using port forwarding scripts, services are available at their original ports:

| Service | URL | Description |
|---------|-----|-------------|
| **Healthcare UI** | http://localhost:3080 | Main application |
| **FHIR MCP Server** | http://localhost:8004 | Patient data access |
| **FHIR Proxy** | http://localhost:8003 | FHIR proxy service |
| **Agent Backend** | http://localhost:8002 | AI coordination |
| **CrewAI Agent** | http://localhost:8000 | CrewAI service |
| **AutoGen Agent** | http://localhost:8001 | AutoGen service |

---

## 🔧 Configuration Management

### Environment-Specific Deployments
```bash
# Development environment
./deploy.sh --environment development --generate-config

# Staging environment
./deploy.sh --environment staging --generate-config

# Production environment
./deploy.sh --environment production --generate-config
```

### Configuration Updates
```bash
# 1. Update config files
nano ../config/environments/production.yaml

# 2. Regenerate ConfigMap
python ../scripts/generate-k8s-configmap.py --environment production --output manifests/01-configmap-updated.yaml

# 3. Apply changes
kubectl apply -f manifests/01-configmap-updated.yaml

# 4. Restart services to pick up new config
kubectl rollout restart deployment -n healthcare-ai
```

### View Current Configuration
```bash
# View ConfigMaps
kubectl get configmaps -n healthcare-ai
kubectl describe configmap healthcare-ai-config -n healthcare-ai

# View environment variables in pods
kubectl exec -it deployment/healthcare-ui -n healthcare-ai -- env | grep NETWORK
```

---

## 🔍 Management & Troubleshooting

### Viewing Resources
```bash
# View all pods with status
kubectl get pods -n healthcare-ai -o wide

# View services with ports
kubectl get services -n healthcare-ai

# View deployments with replica status
kubectl get deployments -n healthcare-ai

# View persistent volumes
kubectl get pv

# View configuration
kubectl get configmaps -n healthcare-ai
kubectl get secrets -n healthcare-ai
```

### Viewing Logs
```bash
# View logs for specific services
kubectl logs -f deployment/healthcare-ui -n healthcare-ai
kubectl logs -f deployment/fhir-mcp-server -n healthcare-ai
kubectl logs -f deployment/agent-backend -n healthcare-ai
kubectl logs -f deployment/crewai-healthcare-agent -n healthcare-ai
kubectl logs -f deployment/autogen-healthcare-agent -n healthcare-ai

# View logs for all pods with a label
kubectl logs -l app=fhir-mcp-server -n healthcare-ai --all-containers=true
```

### Health Checks & Testing
```bash
# Test core services
curl http://localhost:30084/         # FHIR MCP Server
curl http://localhost:30083/health   # FHIR Proxy
curl http://localhost:30082/health   # Agent Backend
curl http://localhost:30080/         # Healthcare UI

# Test AI agents
curl http://localhost:30000/health   # CrewAI Agent
curl http://localhost:30001/health   # AutoGen Agent
```

### Troubleshooting Common Issues

#### Services Not Starting
```bash
# Check pod status and events
kubectl describe pod <pod-name> -n healthcare-ai

# Check logs for errors
kubectl logs <pod-name> -n healthcare-ai

# Check configuration
kubectl get configmap healthcare-ai-config -n healthcare-ai -o yaml
```

#### Port Conflicts
```bash
# Check what's using a port
netstat -tulpn | grep :30080

# Use different ports if needed
kubectl port-forward service/healthcare-ui-service 3081:80 -n healthcare-ai
```

#### Configuration Issues
```bash
# Verify configuration generation
python ../scripts/generate-k8s-configmap.py --environment production

# Check environment variables in running pods
kubectl exec -it deployment/healthcare-ui -n healthcare-ai -- printenv | grep -E "(NETWORK|FHIR|REACT_APP)"
```

---

## 🚀 Advanced Operations

### Scaling Services
```bash
# Scale UI replicas
kubectl scale deployment healthcare-ui --replicas=3 -n healthcare-ai

# Scale AI agents
kubectl scale deployment crewai-healthcare-agent --replicas=2 -n healthcare-ai
kubectl scale deployment autogen-healthcare-agent --replicas=2 -n healthcare-ai
```

### Rolling Updates
```bash
# Update an image
docker build -t healthcare-ai/healthcare-ui:v2 ../ui/

# Rolling update
kubectl set image deployment/healthcare-ui healthcare-ui=healthcare-ai/healthcare-ui:v2 -n healthcare-ai

# Check rollout status
kubectl rollout status deployment/healthcare-ui -n healthcare-ai

# Rollback if needed
kubectl rollout undo deployment/healthcare-ui -n healthcare-ai
```

### Resource Monitoring
```bash
# Check resource usage
kubectl top pods -n healthcare-ai
kubectl top nodes

# Check resource limits
kubectl describe deployment healthcare-ui -n healthcare-ai
```

---

## 💡 Best Practices

1. **Always use the automated deployment scripts** when possible
2. **Generate environment-specific configurations** for different deployment targets
3. **Monitor logs and metrics** through Grafana and Kibana
4. **Use port forwarding scripts** for consistent service access
5. **Test health endpoints** after deployment
6. **Keep configuration files** in version control
7. **Document any custom modifications** to the deployment

---

## 🆘 Quick Commands Reference

```bash
# One-line deployment
./deploy.sh --environment production --generate-config && ./port-forward.sh start

# One-line status check
kubectl get pods,services,deployments -n healthcare-ai

# One-line cleanup
./cleanup.sh && ./port-forward.sh stop

# One-line health check
curl -s http://localhost:30084/ && curl -s http://localhost:30083/health && curl -s http://localhost:30080/

# One-line log viewing
kubectl logs -l app=healthcare-ui -n healthcare-ai --tail=50
``` 