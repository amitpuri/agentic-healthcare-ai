#!/bin/bash

# Healthcare AI Docker Cleanup Script
# This script cleans up the Docker deployment and optionally removes all data

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

show_help() {
    echo "Healthcare AI Docker Cleanup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -a, --all           Remove everything including volumes and data"
    echo "  -v, --volumes       Remove named volumes only"
    echo "  -i, --images        Remove built images"
    echo "  -n, --network       Remove networks"
    echo "  -f, --force         Force removal without confirmation"
    echo "  -q, --quiet         Quiet mode (less verbose output)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Basic cleanup (containers only)"
    echo "  $0 -a               # Full cleanup (everything)"
    echo "  $0 -v               # Remove volumes only"
    echo "  $0 -i               # Remove images only"
    echo ""
}

confirm_action() {
    local message="$1"
    local force_flag="$2"
    
    if [ "$force_flag" = true ]; then
        return 0
    fi
    
    echo -e "${YELLOW}WARNING: $message${NC}"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled."
        exit 0
    fi
}

stop_services() {
    log_info "Stopping all services..."
    
    if docker-compose ps | grep -q "Up"; then
        docker-compose down
        log_success "Services stopped!"
    else
        log_info "No running services found."
    fi
}

remove_containers() {
    log_info "Removing containers..."
    
    # Remove containers with docker-compose
    docker-compose down --remove-orphans
    
    # Remove any remaining healthcare-ai related containers
    local containers=$(docker ps -aq --filter "name=healthcare-ai" --filter "name=crewai" --filter "name=autogen")
    if [ ! -z "$containers" ]; then
        docker rm -f $containers
        log_success "Additional containers removed!"
    fi
    
    log_success "Containers removed!"
}

remove_volumes() {
    log_info "Removing volumes..."
    
    # Remove named volumes
    docker-compose down -v
    
    # Remove specific volumes by name pattern
    local volumes=$(docker volume ls -q --filter "name=healthcare" --filter "name=crewai" --filter "name=autogen")
    if [ ! -z "$volumes" ]; then
        docker volume rm $volumes 2>/dev/null || true
        log_success "Named volumes removed!"
    fi
    
    # Remove local data directories
    if [ -d "./volumes" ]; then
        log_warning "Removing local volume data..."
        rm -rf ./volumes/*
        log_success "Local volume data removed!"
    fi
    
    log_success "Volumes cleaned up!"
}

remove_images() {
    log_info "Removing built images..."
    
    # Remove specific images
    local images=(
        "crewai-healthcare-agent"
        "autogen-healthcare-agent"
        "healthcare-ui"
    )
    
    for image in "${images[@]}"; do
        if docker images | grep -q "$image"; then
            docker rmi "$image:latest" 2>/dev/null || true
            log_info "Removed image: $image"
        fi
    done
    
    # Remove dangling images
    local dangling=$(docker images -f "dangling=true" -q)
    if [ ! -z "$dangling" ]; then
        docker rmi $dangling 2>/dev/null || true
        log_success "Dangling images removed!"
    fi
    
    log_success "Images removed!"
}

remove_networks() {
    log_info "Removing networks..."
    
    # Remove compose networks
    docker-compose down
    
    # Remove specific networks
    local networks=$(docker network ls --filter "name=healthcare" --format "{{.Name}}")
    if [ ! -z "$networks" ]; then
        echo "$networks" | xargs docker network rm 2>/dev/null || true
        log_success "Networks removed!"
    fi
    
    log_success "Networks cleaned up!"
}

cleanup_logs() {
    log_info "Cleaning up log files..."
    
    if [ -d "./logs" ]; then
        rm -rf ./logs/*
        log_success "Log files removed!"
    fi
    
    if [ -d "./volumes" ]; then
        find ./volumes -name "*.log" -type f -delete 2>/dev/null || true
        log_success "Volume log files removed!"
    fi
}

docker_system_prune() {
    log_info "Running Docker system prune..."
    
    # Remove unused data
    docker system prune -f --volumes
    
    log_success "Docker system pruned!"
}

show_disk_usage() {
    log_info "Docker disk usage:"
    docker system df
    echo ""
    
    if [ -d "./volumes" ]; then
        log_info "Local volumes disk usage:"
        du -sh ./volumes/* 2>/dev/null || echo "No volume data found"
        echo ""
    fi
}

main() {
    local all_flag=false
    local volumes_flag=false
    local images_flag=false
    local network_flag=false
    local force_flag=false
    local quiet_flag=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--all)
                all_flag=true
                shift
                ;;
            -v|--volumes)
                volumes_flag=true
                shift
                ;;
            -i|--images)
                images_flag=true
                shift
                ;;
            -n|--network)
                network_flag=true
                shift
                ;;
            -f|--force)
                force_flag=true
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
    
    # Show current usage before cleanup
    if [ "$quiet_flag" = false ]; then
        show_disk_usage
    fi
    
    # Start cleanup based on flags
    log_info "Starting Healthcare AI Docker cleanup..."
    echo ""
    
    if [ "$all_flag" = true ]; then
        confirm_action "This will remove ALL containers, volumes, images, networks, and data!" "$force_flag"
        
        stop_services
        remove_containers
        remove_volumes
        remove_images
        remove_networks
        cleanup_logs
        docker_system_prune
        
        log_success "Complete cleanup finished! 🧹"
        
    elif [ "$volumes_flag" = true ]; then
        confirm_action "This will remove all volumes and persistent data!" "$force_flag"
        
        stop_services
        remove_volumes
        cleanup_logs
        
        log_success "Volume cleanup finished! 🗑️"
        
    elif [ "$images_flag" = true ]; then
        confirm_action "This will remove all built images!" "$force_flag"
        
        remove_images
        
        log_success "Image cleanup finished! 🖼️"
        
    elif [ "$network_flag" = true ]; then
        confirm_action "This will remove all networks!" "$force_flag"
        
        stop_services
        remove_networks
        
        log_success "Network cleanup finished! 🌐"
        
    else
        # Default cleanup - containers only
        confirm_action "This will stop and remove all containers!" "$force_flag"
        
        stop_services
        remove_containers
        
        log_success "Basic cleanup finished! 🚀"
        
        log_info "To remove volumes/data, use: $0 --volumes"
        log_info "To remove images, use: $0 --images"
        log_info "To remove everything, use: $0 --all"
    fi
    
    # Show usage after cleanup
    if [ "$quiet_flag" = false ]; then
        echo ""
        log_info "Disk usage after cleanup:"
        show_disk_usage
    fi
    
    log_info "Cleanup completed successfully! ✨"
}

# Run main function with all arguments
main "$@" 