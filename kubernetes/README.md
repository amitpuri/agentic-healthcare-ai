# Healthcare AI Kubernetes Deployment

## 🚀 Complete Kubernetes Deployment Guide

This directory contains Kubernetes manifests and deployment scripts for the Healthcare AI Agent system, designed for local Docker Desktop Kubernetes. **Updated with centralized configuration management system.**

## 📋 Prerequisites

### Required Software
- **Docker Desktop** with Kubernetes enabled
- **kubectl** CLI tool installed
- **Git** for cloning the repository
- **Python 3.8+** for configuration generation
- At least **8GB RAM** available for containers
- **12GB free disk space** for persistent volumes (increased for new services)

### Enable Kubernetes in Docker Desktop
1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"
5. Wait for Kubernetes to start (green status)

### Verify Setup
```bash
# Check Docker is running
docker version

# Check Kubernetes is running
kubectl cluster-info

# Check kubectl version
kubectl version --client
```

## 🏗️ Architecture Overview

The Kubernetes deployment includes:

- **Healthcare Agents**: CrewAI and AutoGen frameworks (2 pods)
- **Agent Backend**: Core AI coordination service (1 pod)
- **FHIR MCP Server**: Patient data access via Model Context Protocol (1 pod)
- **FHIR Proxy**: CORS-enabled FHIR access (1 pod)
- **Frontend**: React UI with Nginx (2 replicas)
- **Database**: PostgreSQL with persistent storage
- **Cache**: Redis with persistent storage
- **Monitoring**: Prometheus + Grafana
- **Logging**: Elasticsearch + Kibana
- **Networking**: Services, Ingress, NodePorts
- **Configuration**: Centralized config management with environment support

## 🔧 New Features - Centralized Configuration

### Dynamic Configuration System
The deployment now uses a centralized configuration system that:
- ✅ **Eliminates hardcoded localhost URLs**
- ✅ **Supports multiple environments** (development, staging, production)
- ✅ **Dynamic URL generation** based on network settings
- ✅ **Environment-specific overrides**
- ✅ **Kubernetes-native ConfigMap integration**

### Configuration Generator
Generate environment-specific ConfigMaps:
```bash
# Generate production ConfigMap
python ../scripts/generate-k8s-configmap.py --environment production --output manifests/01-configmap-generated.yaml

# Generate development ConfigMap
python ../scripts/generate-k8s-configmap.py --environment development --output manifests/01-configmap-dev.yaml
```

## 📁 File Structure

```
kubernetes/
├── manifests/
│   ├── 00-namespace.yaml          # Namespace creation
│   ├── 01-configmap.yaml          # Default configuration maps
│   ├── 02-secrets.yaml            # Secrets (API keys, passwords)
│   ├── 03-persistent-volumes.yaml # Storage volumes
│   ├── 04-database.yaml           # PostgreSQL deployment
│   ├── 05-redis.yaml              # Redis cache deployment
│   ├── 06-healthcare-agents.yaml  # AI agents + backend + MCP server
│   ├── 07-healthcare-ui.yaml      # React UI deployment
│   ├── 08-monitoring.yaml         # Prometheus/Grafana
│   ├── 09-elk-stack.yaml          # Elasticsearch/Kibana
│   ├── 11-fhir-proxy.yaml         # FHIR proxy service
│   └── configmap-generator.yaml   # ConfigMap generation guide
├── deploy.sh                      # Automated deployment script (updated)
├── cleanup.sh                     # Cleanup script
├── port-forward.sh                # Port forwarding manager (Linux/macOS)
├── port-forward.ps1               # Port forwarding manager (Windows)
└── README.md                      # This file
```

## 🚀 Quick Deployment

### Option 1: Automated Deployment with Dynamic Config (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd agentic-healthcare-ai/kubernetes

# Make scripts executable
chmod +x deploy.sh cleanup.sh port-forward.sh

# Run automated deployment with config generation
./deploy.sh --environment production --generate-config

# Start port forwarding for services
./port-forward.sh start
```

### Option 2: Standard Deployment
```bash
# Run standard deployment with static config
./deploy.sh

# Start essential services only
./port-forward.sh start-essential
```

### Option 3: Manual Step-by-Step Deployment

#### Step 1: Update Secrets
```bash
# Edit the secrets file with your real API keys
nano manifests/02-secrets.yaml

# Base64 encode your secrets:
echo -n "your-openai-api-key" | base64
echo -n "your-password" | base64
```

#### Step 2: Generate ConfigMap (Optional)
```bash
# Generate environment-specific configuration
cd ..
python scripts/generate-k8s-configmap.py --environment production --output kubernetes/manifests/01-configmap-generated.yaml
cd kubernetes
```

#### Step 3: Build Docker Images
```bash
# Build images from the root directory
cd ..
docker-compose -f docker/docker-compose.config.yml build

# Tag for Kubernetes
docker tag healthcare-ai-crewai-fhir-agent healthcare-ai/crewai-healthcare-agent:latest
docker tag healthcare-ai-autogen-fhir-agent healthcare-ai/autogen-healthcare-agent:latest
docker tag healthcare-ai-agent-backend healthcare-ai/agent-backend:latest
docker tag healthcare-ai-fhir-mcp-server healthcare-ai/fhir-mcp-server:latest
docker tag healthcare-ai-fhir-proxy healthcare-ai/fhir-proxy:latest
docker tag healthcare-ai-ui healthcare-ai/healthcare-ui:latest
```

#### Step 4: Deploy Resources
```bash
cd kubernetes

# Create namespace and configurations
kubectl apply -f manifests/00-namespace.yaml
kubectl apply -f manifests/01-configmap.yaml  # or 01-configmap-generated.yaml
kubectl apply -f manifests/02-secrets.yaml

# Create storage
kubectl apply -f manifests/03-persistent-volumes.yaml

# Deploy databases
kubectl apply -f manifests/04-database.yaml
kubectl apply -f manifests/05-redis.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n healthcare-ai --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n healthcare-ai --timeout=120s

# Deploy applications
kubectl apply -f manifests/06-healthcare-agents.yaml
kubectl apply -f manifests/11-fhir-proxy.yaml
kubectl apply -f manifests/07-healthcare-ui.yaml

# Deploy monitoring and logging
kubectl apply -f manifests/08-monitoring.yaml
kubectl apply -f manifests/09-elk-stack.yaml
```

## 🌐 Access URLs

After deployment, access the services via these URLs:

| Service | URL | NodePort | Description |
|---------|-----|----------|-------------|
| **Healthcare UI** | http://localhost:30080 | 30080 | Main application interface |
| **FHIR MCP Server** | http://localhost:30084 | 30084 | Patient data access (MCP) |
| **FHIR Proxy** | http://localhost:30083 | 30083 | CORS-enabled FHIR access |
| **Agent Backend** | http://localhost:30082 | 30082 | AI coordination service |
| **CrewAI Agent** | http://localhost:30000 | 30000 | Team-based AI agent |
| **AutoGen Agent** | http://localhost:30001 | 30001 | Conversational AI agent |
| **Prometheus** | http://localhost:30090 | 30090 | Metrics collection |
| **Grafana** | http://localhost:30300 | 30300 | Dashboards (admin/admin) |
| **Kibana** | http://localhost:30561 | 30561 | Log analysis |

### Internal Service URLs (Container DNS)
- **FHIR MCP**: http://fhir-mcp-service:8004
- **FHIR Proxy**: http://fhir-proxy-service:8003
- **Agent Backend**: http://agent-backend-service:8002
- **CrewAI**: http://crewai-service:8000
- **AutoGen**: http://autogen-service:8001

## 🔧 Management Commands

### Configuration Management
```bash
# View current configuration
kubectl get configmaps -n healthcare-ai
kubectl describe configmap healthcare-ai-config -n healthcare-ai

# Generate new configuration for different environment
python ../scripts/generate-k8s-configmap.py --environment staging

# Update configuration
kubectl apply -f manifests/01-configmap-generated.yaml
kubectl rollout restart deployment -n healthcare-ai  # Restart all deployments
```

### Viewing Resources
```bash
# View all pods
kubectl get pods -n healthcare-ai

# View services with NodePorts
kubectl get services -n healthcare-ai

# View persistent volumes
kubectl get pv

# View deployments
kubectl get deployments -n healthcare-ai

# View ingress
kubectl get ingress -n healthcare-ai

# View configuration
kubectl get configmaps -n healthcare-ai
kubectl get secrets -n healthcare-ai
```

### Monitoring and Logs
```bash
# View logs for specific service
kubectl logs -f deployment/healthcare-ui -n healthcare-ai
kubectl logs -f deployment/fhir-mcp-server -n healthcare-ai
kubectl logs -f deployment/agent-backend -n healthcare-ai
kubectl logs -f deployment/crewai-healthcare-agent -n healthcare-ai

# View events
kubectl get events -n healthcare-ai --sort-by='.metadata.creationTimestamp'

# Describe pod for troubleshooting
kubectl describe pod <pod-name> -n healthcare-ai
```

### Port Forwarding Scripts (Recommended)

Use the automated port forwarding scripts for easy service access:

#### For Linux/macOS/WSL (Bash)
```bash
# Start essential services (UI + Core Services)
./port-forward.sh start-essential

# Start all services
./port-forward.sh start

# Start specific services
./port-forward.sh start healthcare-ui-service fhir-mcp-service

# Check status
./port-forward.sh status

# Stop all
./port-forward.sh stop
```

#### For Windows (PowerShell)
```powershell
# Start essential services
.\port-forward.ps1 start-essential

# Start all services
.\port-forward.ps1 start

# Check status
.\port-forward.ps1 status

# Stop all
.\port-forward.ps1 stop
```

## 🧪 Testing the Deployment

### Health Checks
```bash
# Test core services
curl http://localhost:30084/     # FHIR MCP Server
curl http://localhost:30083/health    # FHIR Proxy
curl http://localhost:30082/health    # Agent Backend
curl http://localhost:30080/     # Healthcare UI

# Test AI agents
curl http://localhost:30000/health    # CrewAI Agent
curl http://localhost:30001/health    # AutoGen Agent
```

### Configuration Testing
```bash
# Test configuration system
kubectl exec -it deployment/healthcare-ui -n healthcare-ai -- env | grep NETWORK
kubectl exec -it deployment/fhir-mcp-server -n healthcare-ai -- env | grep FHIR
```

## 🔧 Troubleshooting

### Common Issues

1. **Services not starting**: Check ConfigMap and environment variables
   ```bash
   kubectl describe pod <pod-name> -n healthcare-ai
   kubectl logs <pod-name> -n healthcare-ai
   ```

2. **Port conflicts**: Use different NodePorts or stop conflicting services
   ```bash
   netstat -tulpn | grep :30080
   ```

3. **Configuration issues**: Verify ConfigMap generation
   ```bash
   python ../scripts/generate-k8s-configmap.py --environment production
   ```

4. **Image pull errors**: Ensure Docker images are built and tagged correctly
   ```bash
   docker images | grep healthcare-ai
   ```

### Debugging Configuration
```bash
# Check if configuration is loaded correctly
kubectl exec -it deployment/healthcare-ui -n healthcare-ai -- printenv | grep -E "(NETWORK|FHIR|REACT_APP)"

# View full ConfigMap
kubectl get configmap healthcare-ai-config -n healthcare-ai -o yaml
```

## 🗑️ Cleanup

### Full Cleanup
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
./port-forward.sh stop
```

## 📚 Environment-Specific Deployments

### Development Environment
```bash
./deploy.sh --environment development --generate-config
```

### Staging Environment
```bash
./deploy.sh --environment staging --generate-config
```

### Production Environment
```bash
./deploy.sh --environment production --generate-config
```

Each environment will have appropriate configuration overrides as defined in the centralized config system.

## 🔄 Configuration Updates

When updating the centralized configuration:

1. **Update config files**: Modify `config/environments/*.yaml`
2. **Regenerate ConfigMap**: `python scripts/generate-k8s-configmap.py --environment production --output kubernetes/manifests/01-configmap-generated.yaml`
3. **Apply changes**: `kubectl apply -f manifests/01-configmap-generated.yaml`
4. **Restart services**: `kubectl rollout restart deployment -n healthcare-ai`

This ensures all services pick up the new configuration without manual intervention.

## 🔐 Security Considerations

### Update Secrets
Before production deployment, update these secrets:

```bash
# Create secrets securely
kubectl create secret generic healthcare-ai-secrets \
  --from-literal=OPENAI_API_KEY="your-real-api-key" \
  --from-literal=DATABASE_PASSWORD="strong-password" \
  --from-literal=REDIS_PASSWORD="strong-redis-password" \
  --from-literal=FHIR_CLIENT_ID="your-fhir-client-id" \
  --from-literal=FHIR_CLIENT_SECRET="your-fhir-client-secret" \
  --from-literal=GRAFANA_PASSWORD="strong-grafana-password" \
  --namespace=healthcare-ai
```

### Network Policies (Optional)
```bash
# Apply network policies for additional security
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: healthcare-ai-netpol
  namespace: healthcare-ai
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: healthcare-ai
  egress:
  - to: []
EOF
```

## 📊 Monitoring and Alerting

### Prometheus Metrics
Access Prometheus at http://localhost:30090 to query metrics:

```promql
# CPU usage by pod
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes

# HTTP request rate
rate(http_requests_total[5m])
```

### Grafana Dashboards
1. Access Grafana at http://localhost:30300
2. Login with admin/admin
3. Import dashboard templates from monitoring/grafana/dashboards/

### Log Analysis with Kibana
1. Access Kibana at http://localhost:30561
2. Create index pattern: `healthcare-ai-logs-*`
3. Explore logs from all services

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build images
      run: docker-compose build
      
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f kubernetes/manifests/
        kubectl rollout restart deployment/healthcare-ui -n healthcare-ai
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Helm Charts](https://helm.sh/) (for advanced deployments)

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review pod logs: `kubectl logs <pod-name> -n healthcare-ai`
3. Check resource usage: `kubectl top pods -n healthcare-ai`
4. Verify network connectivity between services

---

**Happy Deploying! 🚀** 