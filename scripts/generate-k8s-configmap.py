#!/usr/bin/env python3
"""
Kubernetes ConfigMap Generator for Healthcare AI

This script generates Kubernetes ConfigMaps using the centralized configuration system.
It creates environment-specific ConfigMaps for Kubernetes deployment.

Usage:
    python generate-k8s-configmap.py --environment production
    python generate-k8s-configmap.py --environment development --output custom-configmap.yaml
"""

import argparse
import sys
import os
import yaml
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.append(str(Path(__file__).parent.parent))

from config.config_manager import ConfigManager
from config.network_config import NetworkConfig

def generate_configmap(environment: str, output_file: str = None):
    """Generate Kubernetes ConfigMap from centralized configuration"""
    
    # Initialize configuration manager
    config_manager = ConfigManager(environment=environment)
    config = config_manager.load_config()
    
    # Initialize network configuration
    network_config = NetworkConfig(config_manager=config_manager)
    
    # Generate ConfigMap data
    configmap_data = {
        # Environment Configuration
        'ENVIRONMENT': environment,
        
        # Network Configuration
        'NETWORK_HOST': network_config.host,
        'NETWORK_PROTOCOL': network_config.protocol,
        'EXTERNAL_HOST': network_config.external_host,
        'DOMAIN_NAME': network_config.domain or '',
        
        # Service URLs - External (NodePort) - Use localhost for Kubernetes
        'HEALTHCARE_UI_URL': "http://localhost:30080",
        'FHIR_MCP_URL': "http://localhost:30084",
        'FHIR_PROXY_URL': "http://localhost:30083",
        'AGENT_BACKEND_URL': "http://localhost:30082",
        'CREWAI_API_URL': "http://localhost:30000",
        'AUTOGEN_API_URL': "http://localhost:30001",
        
        # Internal Service URLs (Container DNS)
        'FHIR_MCP_INTERNAL_URL': 'http://fhir-mcp-service:8004',
        'FHIR_PROXY_INTERNAL_URL': 'http://fhir-proxy-service:8003',
        'AGENT_BACKEND_INTERNAL_URL': 'http://agent-backend-service:8002',
        'CREWAI_INTERNAL_URL': 'http://crewai-service:8000',
        'AUTOGEN_INTERNAL_URL': 'http://autogen-service:8001',
        
        # FHIR Configuration
        'FHIR_BASE_URL': config.get('fhir', {}).get('base_url', 'https://r4.smarthealthit.org'),
        
        # Database Configuration
        'POSTGRES_DB': config.get('database', {}).get('name', 'healthcare_ai'),
        'POSTGRES_USER': config.get('database', {}).get('user', 'healthcare_user'),
        
        # Redis Configuration
        'REDIS_HOST': 'redis-service',
        'REDIS_PORT': '6379',
        
        # Elasticsearch Configuration
        'ELASTICSEARCH_HOSTS': 'http://elasticsearch-service:9200',
        
        # Environment
        'NODE_ENV': 'production' if environment == 'production' else 'development',
        
        # Legacy Service URLs (for backward compatibility)
        'CREWAI_SERVICE_URL': 'http://crewai-service:8000',
        'AUTOGEN_SERVICE_URL': 'http://autogen-service:8001',
    }
    
    # Create ConfigMap YAML
    configmap = {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': 'healthcare-ai-config',
            'namespace': 'healthcare-ai',
            'labels': {
                'app': 'healthcare-ai-system',
                'environment': environment
            }
        },
        'data': configmap_data
    }
    
    # Create Prometheus ConfigMap
    prometheus_configmap = {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': 'prometheus-config',
            'namespace': 'healthcare-ai',
            'labels': {
                'app': 'prometheus'
            }
        },
        'data': {
            'prometheus.yml': """global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'healthcare-agents'
    static_configs:
      - targets: ['crewai-service:8000', 'autogen-service:8001', 'agent-backend-service:8002']
      
  - job_name: 'healthcare-services'
    static_configs:
      - targets: ['fhir-mcp-service:8004', 'fhir-proxy-service:8003']
      
  - job_name: 'healthcare-ui'
    static_configs:
      - targets: ['healthcare-ui-service:80']"""
        }
    }
    
    # Combine both ConfigMaps
    all_configmaps = [configmap, prometheus_configmap]
    
    # Generate YAML output
    yaml_output = ""
    for i, cm in enumerate(all_configmaps):
        if i > 0:
            yaml_output += "\n---\n"
        yaml_output += yaml.dump(cm, default_flow_style=False, allow_unicode=True)
    
    # Write to file or stdout
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(yaml_output)
        print(f"ConfigMap generated: {output_path}")
    else:
        print(yaml_output)

def main():
    parser = argparse.ArgumentParser(description='Generate Kubernetes ConfigMap from centralized configuration')
    parser.add_argument('--environment', '-e', 
                       choices=['development', 'staging', 'production'],
                       default='production',
                       help='Environment to generate ConfigMap for (default: production)')
    parser.add_argument('--output', '-o',
                       help='Output file path (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        generate_configmap(args.environment, args.output)
    except Exception as e:
        print(f"Error generating ConfigMap: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main() 