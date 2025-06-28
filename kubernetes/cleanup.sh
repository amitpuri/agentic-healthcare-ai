#!/bin/bash

# Healthcare AI Kubernetes Cleanup Script
# This script removes all Healthcare AI resources from Kubernetes

set -e

echo "🧹 Starting Healthcare AI Kubernetes Cleanup..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed."
    exit 1
fi

# Check if namespace exists
if kubectl get namespace healthcare-ai &> /dev/null; then
    echo "🗑️  Deleting Healthcare AI namespace and all resources..."
    kubectl delete namespace healthcare-ai
    
    echo "⏳ Waiting for namespace deletion..."
    kubectl wait --for=delete namespace/healthcare-ai --timeout=120s
    
    echo "✅ Healthcare AI namespace deleted"
else
    echo "ℹ️  Healthcare AI namespace not found"
fi

# Remove persistent volumes (if using local storage)
echo "🗑️  Removing persistent volumes..."
kubectl delete pv postgres-pv redis-pv elasticsearch-pv prometheus-pv grafana-pv --ignore-not-found=true

# Remove any leftover ingress resources
echo "🗑️  Cleaning up ingress resources..."
kubectl delete ingress --all --all-namespaces --selector=app=healthcare-ai --ignore-not-found=true

# Optional: Remove NGINX Ingress Controller (uncomment if you want to remove it)
# echo "🗑️  Removing NGINX Ingress Controller..."
# kubectl delete -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Clean up Docker images (optional)
read -p "🐳 Do you want to remove Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing Docker images..."
    docker rmi healthcare-ai/crewai-healthcare-agent:latest --force 2>/dev/null || true
    docker rmi healthcare-ai/autogen-healthcare-agent:latest --force 2>/dev/null || true
    docker rmi healthcare-ai/healthcare-ui:latest --force 2>/dev/null || true
    docker rmi healthcare-ai-crewai-healthcare-agent --force 2>/dev/null || true
    docker rmi healthcare-ai-autogen-healthcare-agent --force 2>/dev/null || true
    docker rmi healthcare-ai-healthcare-ui --force 2>/dev/null || true
    echo "✅ Docker images removed"
fi

# Clean up host directories (optional)
read -p "📁 Do you want to remove persistent data directories? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing persistent data directories..."
    sudo rm -rf /tmp/postgres-data /tmp/redis-data /tmp/elasticsearch-data /tmp/prometheus-data /tmp/grafana-data 2>/dev/null || true
    echo "✅ Persistent data directories removed"
fi

echo ""
echo "🎉 Cleanup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ All Healthcare AI resources have been removed from Kubernetes"
echo ""
echo "🔍 Verify cleanup:"
echo "   kubectl get pods -n healthcare-ai"
echo "   kubectl get pv | grep healthcare"
echo "   docker images | grep healthcare-ai"
echo "" 