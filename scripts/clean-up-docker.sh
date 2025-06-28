#!/bin/bash

echo "⚠️  WARNING: This script will perform aggressive Docker cleanup operations:"
echo "   - Remove all stopped containers"
echo "   - Remove all unused images"
echo "   - Remove all unused volumes"
echo "   - Remove all unused networks"
echo "   - Remove all build cache"
echo ""
echo "🔍 Checking for Kubernetes containers..."

# Check if there are Kubernetes/kind containers
k8s_containers=$(docker ps -a --filter "name=kind\|k8s\|kube" --format "table {{.Names}}" 2>/dev/null | tail -n +2 || true)
if [ ! -z "$k8s_containers" ]; then
    echo ""
    echo "⚠️  KUBERNETES CONTAINERS DETECTED:"
    echo "$k8s_containers"
    echo ""
    echo "❗ WARNING: This will also remove Kubernetes/kind containers!"
    echo "   Consider running 'kubectl delete' commands or '../kubernetes/cleanup.sh' first"
fi

echo ""
echo "This operation is IRREVERSIBLE and will DELETE data!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Operation cancelled."
    echo "💡 For Kubernetes-only cleanup, use: ./kubernetes/cleanup.sh"
    exit 0
fi

echo "Proceeding with Docker cleanup..."
docker system prune -af --volumes && docker system df

echo ""
echo "💡 Note: If you have Kubernetes running, you may want to run:"
echo "   ./kubernetes/cleanup.sh (for K8s resources)"
echo "   kind delete cluster (for kind clusters)"