#!/bin/bash

# Healthcare AI Kubernetes Port Forward Manager
# Manages port forwarding for all services in the Healthcare AI system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="healthcare-ai"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/.port-forward-pids"

# Service definitions (service_name:local_port:service_port:priority:description)
SERVICES=(
    "healthcare-ui-service:30080:80:9:Healthcare UI (NodePort - No Port Forward Needed)"
    "fhir-mcp-server:8004:8004:1:FHIR MCP Server (Patient Data)"
    "fhir-proxy:8003:8003:2:FHIR Proxy (CORS Handler)"
    "agent-backend:8002:8002:4:Agent Backend (AI Coordination)"
    "crewai-healthcare-agent:8000:8000:5:CrewAI Agent (Team-based AI)"
    "autogen-healthcare-agent:8001:8001:6:AutoGen Agent (Conversational AI)"
    "postgres-service:5432:5432:7:PostgreSQL (Database)"
    "redis-service:6379:6379:8:Redis (Cache)"
)

# Create PID directory if it doesn't exist
mkdir -p "$PID_DIR"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print header
print_header() {
    echo
    print_color "$CYAN" "================================================"
    print_color "$CYAN" "  Healthcare AI Port Forward Manager"
    print_color "$CYAN" "================================================"
    echo
}

# Function to check if kubectl is available and cluster is accessible
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_color "$RED" "❌ kubectl not found. Please install kubectl first."
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        print_color "$RED" "❌ Cannot connect to Kubernetes cluster. Is KIND running?"
        print_color "$YELLOW" "💡 Try: ./kind.exe create cluster --name healthcare-ai"
        exit 1
    fi

    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_color "$RED" "❌ Namespace '$NAMESPACE' not found."
        print_color "$YELLOW" "💡 Try: kubectl apply -f manifests/00-namespace.yaml"
        exit 1
    fi
}

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    if command -v netstat &> /dev/null; then
        # Windows-compatible netstat check
        netstat -an 2>/dev/null | grep -q ":$port.*LISTENING"
    elif command -v ss &> /dev/null; then
        ss -tuln 2>/dev/null | grep -q ":$port "
    else
        # Try to bind to the port as a test
        timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" 2>/dev/null
    fi
}

# Function to get process ID using a port
get_port_pid() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -ti:$port 2>/dev/null | head -1
    elif command -v netstat &> /dev/null; then
        # Windows-compatible netstat to get PID
        netstat -ano 2>/dev/null | grep ":$port.*LISTENING" | awk '{print $5}' | head -1
    else
        echo ""
    fi
}

# Function to start port forward for a service
start_port_forward() {
    local service_name=$1
    local local_port=$2
    local service_port=$3
    local description=$4
    local pid_file="${PID_DIR}/${service_name}.pid"

    # Check if already running
    if [[ -f "$pid_file" ]]; then
        local existing_pid=$(cat "$pid_file")
        if kill -0 "$existing_pid" 2>/dev/null; then
            print_color "$YELLOW" "⚠️  Port forward already running for $service_name (PID: $existing_pid)"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi

    # Check if port is in use by another process
    if is_port_in_use "$local_port"; then
        local port_pid=$(get_port_pid "$local_port")
        
        # If we have a PID, assume it's a working port forward for now
        if [[ "$port_pid" != "" ]]; then
            print_color "$GREEN" "✅ Port $local_port already in use (PID: $port_pid)"
            print_color "$CYAN" "   Assuming existing port forward for $service_name is working"
            print_color "$CYAN" "   Access at: http://localhost:$local_port"
            return 0
        else
            print_color "$YELLOW" "⚠️  Port $local_port appears to be in use but no PID found"
            print_color "$YELLOW" "    This might be a stale connection. Continuing with port forward..."
            # Continue to try starting the port forward
        fi
    fi

    # Check if service exists
    if ! kubectl get service "$service_name" -n "$NAMESPACE" &> /dev/null; then
        print_color "$RED" "❌ Service $service_name not found in namespace $NAMESPACE"
        return 1
    fi

    print_color "$BLUE" "🚀 Starting port forward: $description"
    print_color "$CYAN" "   $service_name:$local_port -> $service_port"

    # Start port forward in background
    kubectl port-forward service/"$service_name" "$local_port:$service_port" -n "$NAMESPACE" &> /dev/null &
    local pid=$!

    # Save PID
    echo "$pid" > "$pid_file"

    # Wait a moment and check if it's still running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        print_color "$GREEN" "✅ Port forward started successfully (PID: $pid)"
        print_color "$CYAN" "   Access at: http://localhost:$local_port"
    else
        print_color "$RED" "❌ Failed to start port forward for $service_name"
        rm -f "$pid_file"
        return 1
    fi
}

# Function to stop port forward for a service
stop_port_forward() {
    local service_name=$1
    local pid_file="${PID_DIR}/${service_name}.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            rm -f "$pid_file"
            print_color "$GREEN" "✅ Stopped port forward for $service_name (PID: $pid)"
        else
            print_color "$YELLOW" "⚠️  Port forward process not found for $service_name"
            rm -f "$pid_file"
        fi
    else
        print_color "$YELLOW" "⚠️  No port forward found for $service_name"
    fi
}

# Function to show status of all port forwards
show_status() {
    print_header
    print_color "$BLUE" "📊 Port Forward Status:"
    echo

    local any_running=false
    
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        local pid_file="${PID_DIR}/${service_name}.pid"
        
        printf "%-25s %-6s " "$service_name" "$local_port"
        
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                print_color "$GREEN" "✅ RUNNING (PID: $pid)"
                any_running=true
            else
                print_color "$RED" "❌ STOPPED (stale PID file)"
                rm -f "$pid_file"
            fi
        else
            if is_port_in_use "$local_port"; then
                local port_pid=$(get_port_pid "$local_port")
                print_color "$YELLOW" "⚠️  PORT IN USE (PID: $port_pid)"
            else
                print_color "$RED" "❌ STOPPED"
            fi
        fi
    done

    echo
    if $any_running; then
        print_color "$GREEN" "🌐 Access URLs:"
        for service_def in "${SERVICES[@]}"; do
            IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
            local pid_file="${PID_DIR}/${service_name}.pid"
            
            if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
                printf "   %-25s http://localhost:%s\n" "$description:" "$local_port"
            fi
        done
    else
        print_color "$YELLOW" "💡 No port forwards currently running. Use '$0 start' to begin."
    fi
    echo
}

# Function to start essential services only
start_essential() {
    print_header
    print_color "$BLUE" "🚀 Starting essential port forwards..."
    echo

    # Sort services by priority and start only essential ones (priority 1-2)
    local essential_services=()
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        if [[ $priority -le 2 ]]; then
            essential_services+=("$service_def")
        fi
    done

    # Sort by priority
    IFS=$'\n' essential_services=($(sort -t: -k4 -n <<<"${essential_services[*]}"))
    unset IFS

    for service_def in "${essential_services[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        start_port_forward "$service_name" "$local_port" "$service_port" "$description"
        echo
    done

    print_color "$GREEN" "✅ Essential services started!"
    print_color "$CYAN" "   Main UI: http://localhost:30080 (NodePort)"
    print_color "$CYAN" "   MCP Server: http://localhost:8004/rpc"
    print_color "$CYAN" "   FHIR Proxy: http://localhost:8003"
}

# Function to start all services
start_all() {
    print_header
    print_color "$BLUE" "🚀 Starting all port forwards..."
    echo

    # Sort services by priority
    local sorted_services=()
    IFS=$'\n' sorted_services=($(sort -t: -k4 -n <<<"${SERVICES[*]}"))
    unset IFS

    for service_def in "${sorted_services[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        start_port_forward "$service_name" "$local_port" "$service_port" "$description"
        echo
    done

    print_color "$GREEN" "✅ All services started!"
}

# Function to stop all port forwards
stop_all() {
    print_header
    print_color "$BLUE" "🛑 Stopping all port forwards..."
    echo

    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        stop_port_forward "$service_name"
    done

    # Clean up any remaining kubectl port-forward processes
    pkill -f "kubectl port-forward" 2>/dev/null || true
    
    # Clean up PID directory
    rm -rf "$PID_DIR"
    mkdir -p "$PID_DIR"

    print_color "$GREEN" "✅ All port forwards stopped!"
    echo
}

# Function to restart all port forwards
restart_all() {
    print_color "$BLUE" "🔄 Restarting all port forwards..."
    stop_all
    sleep 2
    start_all
}

# Function to show help
show_help() {
    print_header
    print_color "$BLUE" "📖 Usage: $0 [command]"
    echo
    print_color "$CYAN" "Commands:"
    echo "  start         Start essential services (MCP + FHIR Proxy)"
    echo "  start-all     Start all available services"
    echo "  stop          Stop all port forwards"
    echo "  restart       Restart all port forwards"
    echo "  status        Show current status of all port forwards"
    echo "  help          Show this help message"
    echo
    print_color "$CYAN" "Examples:"
    echo "  $0 start      # Start essential services"
    echo "  $0 status     # Check what's running"
    echo "  $0 stop       # Stop everything"
    echo
    print_color "$CYAN" "Essential Services:"
    echo "  • Healthcare UI (http://localhost:30080) - Main application (NodePort)"
    echo "  • FHIR MCP Server (http://localhost:8004/rpc) - Patient data access"
    echo "  • FHIR Proxy (http://localhost:8003) - CORS handler for FHIR"
    echo
    print_color "$CYAN" "All Services:"
    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        printf "  • %-25s (http://localhost:%s)\n" "$description" "$local_port"
    done
    echo
}

# Function to test connectivity
test_services() {
    print_header
    print_color "$BLUE" "🧪 Testing service connectivity..."
    echo

    for service_def in "${SERVICES[@]}"; do
        IFS=':' read -r service_name local_port service_port priority description <<< "$service_def"
        local pid_file="${PID_DIR}/${service_name}.pid"
        
        if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            printf "%-25s " "$description:"
            if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://localhost:$local_port" | grep -q "200\|302\|401"; then
                print_color "$GREEN" "✅ RESPONDING"
            else
                print_color "$YELLOW" "⚠️  NO RESPONSE"
            fi
        fi
    done
    echo
}

# Main script logic
main() {
    case "${1:-help}" in
        "start")
            check_kubectl
            start_essential
            ;;
        "start-all")
            check_kubectl
            start_all
            ;;
        "stop")
            stop_all
            ;;
        "restart")
            check_kubectl
            restart_all
            ;;
        "status")
            show_status
            ;;
        "test")
            test_services
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_color "$RED" "❌ Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 