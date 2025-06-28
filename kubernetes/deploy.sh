#!/bin/bash

# Healthcare AI Kubernetes Deployment Script
# This script deploys the Healthcare AI system to local Kubernetes
# Updated to use centralized configuration system

set -e

echo "🚀 Starting Healthcare AI Kubernetes Deployment..."

# Parse command line arguments
ENVIRONMENT="production"
GENERATE_CONFIG="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --generate-config)
            GENERATE_CONFIG="true"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (development|staging|production, default: production)"
            echo "  --generate-config        Generate ConfigMap from centralized config"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🎯 Using environment: $ENVIRONMENT"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if Kubernetes is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster is not running. Please start Docker Desktop Kubernetes."
    exit 1
fi

echo "✅ Kubernetes cluster is running"

# Determine the correct project root directory at the beginning
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Generate ConfigMap from centralized configuration if requested
if [ "$GENERATE_CONFIG" = "true" ]; then
    echo "⚙️  Generating ConfigMap from centralized configuration..."
    cd "$PROJECT_ROOT"
    if [ -f "scripts/generate-k8s-configmap.py" ]; then
        python scripts/generate-k8s-configmap.py --environment "$ENVIRONMENT" --output "kubernetes/manifests/01-configmap-generated.yaml"
        echo "✅ ConfigMap generated: kubernetes/manifests/01-configmap-generated.yaml"
        echo "📝 You can review and use this instead of the default configmap."
    else
        echo "⚠️  ConfigMap generator not found. Using default configmap."
    fi
    cd "$SCRIPT_DIR"
else
    echo "📋 Using existing ConfigMap. Use --generate-config to generate from centralized config."
fi

# Enable Kubernetes ingress (for Docker Desktop)
echo "🔧 Enabling NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller to be ready
echo "⏳ Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

# Build Docker images first
echo "🔨 Building Docker images..."

echo "   Script directory: $SCRIPT_DIR"
echo "   Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

# Updated build command to include all services
echo "   Building all services..."
docker-compose -f docker/docker-compose.config.yml build

# Tag images for Kubernetes
echo "   Tagging images for Kubernetes..."
docker tag crewai-healthcare-agent:latest healthcare-ai/crewai-healthcare-agent:latest
docker tag autogen-healthcare-agent:latest healthcare-ai/autogen-healthcare-agent:latest
docker tag agent-backend:latest healthcare-ai/agent-backend:latest
docker tag fhir-mcp-server:latest healthcare-ai/fhir-mcp-server:latest
docker tag fhir-proxy:latest healthcare-ai/fhir-proxy:latest
docker tag healthcare-ui:latest healthcare-ai/healthcare-ui:latest

echo "✅ Docker images built and tagged"

# Return to kubernetes directory for manifest operations
cd "$SCRIPT_DIR"

# Create namespace
echo "🏗️  Creating namespace..."
kubectl apply -f manifests/00-namespace.yaml

# Apply ConfigMaps and Secrets
echo "⚙️  Applying configurations..."
if [ -f "manifests/01-configmap-generated.yaml" ] && [ "$GENERATE_CONFIG" = "true" ]; then
    echo "   Using generated ConfigMap..."
    kubectl apply -f manifests/01-configmap-generated.yaml
else
    echo "   Using default ConfigMap..."
    kubectl apply -f manifests/01-configmap.yaml
fi

# Create secrets - you should update these with real values
echo "🔐 Creating secrets..."
echo "⚠️  Note: Using default secrets. Update manifests/02-secrets.yaml with your real API keys!"
kubectl apply -f manifests/02-secrets.yaml

# Apply PersistentVolumes
echo "💾 Creating persistent volumes..."
kubectl apply -f manifests/03-persistent-volumes.yaml

# Wait for PVs to be available
echo "⏳ Waiting for persistent volumes..."
sleep 5

# Deploy databases first
echo "🗄️  Deploying databases..."
kubectl apply -f manifests/04-database.yaml
kubectl apply -f manifests/05-redis.yaml

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n healthcare-ai --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n healthcare-ai --timeout=120s

# Deploy applications
echo "🤖 Deploying healthcare agents and services..."
kubectl apply -f manifests/06-healthcare-agents.yaml

# Deploy FHIR proxy (NEW)
echo "🔗 Deploying FHIR proxy..."
kubectl apply -f manifests/11-fhir-proxy.yaml

# Deploy UI
echo "🌐 Deploying UI..."
kubectl apply -f manifests/07-healthcare-ui.yaml

# Deploy monitoring
echo "📊 Deploying monitoring stack..."
kubectl apply -f manifests/08-monitoring.yaml

# Deploy ELK stack
echo "📋 Deploying logging stack..."
kubectl apply -f manifests/09-elk-stack.yaml

# Wait for all deployments to be ready
echo "⏳ Waiting for all deployments to be ready..."
kubectl wait --for=condition=ready pod -l app=crewai-healthcare-agent -n healthcare-ai --timeout=180s
kubectl wait --for=condition=ready pod -l app=autogen-healthcare-agent -n healthcare-ai --timeout=180s
kubectl wait --for=condition=ready pod -l app=agent-backend -n healthcare-ai --timeout=180s
kubectl wait --for=condition=ready pod -l app=fhir-mcp-server -n healthcare-ai --timeout=180s
kubectl wait --for=condition=ready pod -l app=fhir-proxy -n healthcare-ai --timeout=180s
kubectl wait --for=condition=ready pod -l app=healthcare-ui -n healthcare-ai --timeout=180s

echo "✅ Healthcare AI system deployed successfully!"

# Display access information
echo ""
echo "🎉 Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Access URLs:"
echo "   Healthcare UI:     http://localhost:30080"
echo "   FHIR MCP Server:   http://localhost:30084"
echo "   FHIR Proxy:        http://localhost:30083"
echo "   Agent Backend:     http://localhost:30082"
echo "   CrewAI Agent:      http://localhost:30000"
echo "   AutoGen Agent:     http://localhost:30001"
echo "   Prometheus:        http://localhost:30090"
echo "   Grafana:          http://localhost:30300 (admin/admin)"
echo "   Kibana:           http://localhost:30561"
echo ""
echo "🔍 Useful Commands:"
echo "   View all pods:     kubectl get pods -n healthcare-ai"
echo "   View services:     kubectl get services -n healthcare-ai"
echo "   View configmaps:   kubectl get configmaps -n healthcare-ai"
echo "   View logs:         kubectl logs -f deployment/healthcare-ui -n healthcare-ai"
echo "   Port forward:      kubectl port-forward service/healthcare-ui-service 3030:80 -n healthcare-ai"
echo ""
echo "🧪 Testing the deployment:"
echo "   Health checks:     curl http://localhost:30084/"
echo "   UI status:         curl http://localhost:30080/"
echo ""
echo "⚙️  Configuration:"
echo "   Environment:       $ENVIRONMENT"
echo "   ConfigMap source:  $([ -f "manifests/01-configmap-generated.yaml" ] && [ "$GENERATE_CONFIG" = "true" ] && echo "Generated from centralized config" || echo "Default static config")"
echo ""
echo "🗑️  To clean up:"
echo "   ./cleanup.sh"
echo "   or: kubectl delete namespace healthcare-ai"
echo "" 