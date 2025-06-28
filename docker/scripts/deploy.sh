#!/bin/bash

# Healthcare AI Docker Deployment Script
# This script deploys the complete healthcare AI system using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
LOG_DIR="./logs"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning "Please edit .env file with your configuration before running again."
            exit 1
        else
            log_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed!"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$LOG_DIR"
    mkdir -p "./volumes/postgres-data"
    mkdir -p "./volumes/redis-data"
    mkdir -p "./volumes/elasticsearch-data"
    mkdir -p "./volumes/prometheus-data"
    mkdir -p "./volumes/grafana-data"
    mkdir -p "./volumes/crewai-logs"
    mkdir -p "./volumes/crewai-data"
    mkdir -p "./volumes/autogen-logs"
    mkdir -p "./volumes/autogen-data"
    mkdir -p "./services/nginx/ssl"
    
    log_success "Directories created!"
}

generate_ssl_certificates() {
    log_info "Checking SSL certificates..."
    
    if [ ! -f "./services/nginx/ssl/cert.pem" ] || [ ! -f "./services/nginx/ssl/key.pem" ]; then
        log_info "Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ./services/nginx/ssl/key.pem \
            -out ./services/nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        log_success "SSL certificates generated!"
    else
        log_info "SSL certificates already exist."
    fi
}

cleanup_old_deployment() {
    log_info "Cleaning up old deployment..."
    
    if docker-compose ps | grep -q "Up"; then
        log_info "Stopping existing services..."
        docker-compose down
    fi
    
    # Remove orphaned containers
    docker-compose down --remove-orphans
    
    log_success "Cleanup completed!"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build images with no cache to ensure latest code
    docker-compose build --no-cache
    
    log_success "Images built successfully!"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Start services in detached mode
    docker-compose up -d
    
    log_success "Services deployed!"
}

wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    # Wait for critical services
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check if all services are running
        if docker-compose ps | grep -q "Exit"; then
            log_error "Some services failed to start. Check logs:"
            docker-compose logs
            exit 1
        fi
        
        # Check database health
        if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            log_success "Database is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy within timeout."
            docker-compose logs
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
}

show_status() {
    log_info "Deployment Status:"
    echo ""
    docker-compose ps
    echo ""
    
    log_info "Access URLs:"
    echo "  🌐 Main UI: http://localhost:3030"
    echo "  🤖 CrewAI API: http://localhost:8000"
    echo "  🤖 Autogen API: http://localhost:8001"
    echo "  📊 Grafana: http://localhost:3000 (admin/admin)"
    echo "  📈 Prometheus: http://localhost:9090"
    echo "  🔍 Kibana: http://localhost:5601"
    echo "  🔍 Elasticsearch: http://localhost:9200"
    echo "  🔧 Load Balancer: http://localhost:80"
    echo ""
    
    log_info "Useful Commands:"
    echo "  📋 View logs: docker-compose logs -f [service_name]"
    echo "  🛑 Stop all: docker-compose down"
    echo "  🗑️  Full cleanup: docker-compose down -v"
    echo "  🔄 Restart service: docker-compose restart [service_name]"
    echo ""
}

show_help() {
    echo "Healthcare AI Docker Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -c, --cleanup       Cleanup before deployment"
    echo "  -b, --build         Force rebuild of images"
    echo "  -n, --no-wait       Don't wait for service health checks"
    echo "  -q, --quiet         Quiet mode (less verbose output)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Standard deployment"
    echo "  $0 -c               # Cleanup and deploy"
    echo "  $0 -b               # Force rebuild and deploy"
    echo ""
}

main() {
    local cleanup_flag=false
    local build_flag=false
    local wait_flag=true
    local quiet_flag=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--cleanup)
                cleanup_flag=true
                shift
                ;;
            -b|--build)
                build_flag=true
                shift
                ;;
            -n|--no-wait)
                wait_flag=false
                shift
                ;;
            -q|--quiet)
                quiet_flag=true
                shift
                ;;
            *)
                log_error "Unknown option $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Start deployment
    log_info "Starting Healthcare AI Docker Deployment..."
    echo ""
    
    check_prerequisites
    create_directories
    generate_ssl_certificates
    
    if [ "$cleanup_flag" = true ]; then
        cleanup_old_deployment
    fi
    
    if [ "$build_flag" = true ]; then
        build_images
    fi
    
    deploy_services
    
    if [ "$wait_flag" = true ]; then
        wait_for_services
    fi
    
    show_status
    
    log_success "Healthcare AI system deployed successfully! 🎉"
}

# Run main function with all arguments
main "$@" 