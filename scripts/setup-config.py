#!/usr/bin/env python3
"""
Healthcare AI Configuration Setup Script
Helps users configure the application for their environment
"""

import os
import sys
import yaml
import argparse
import getpass
from pathlib import Path
from typing import Dict, Any

# Add config directory to path
sys.path.append(str(Path(__file__).parent.parent / "config"))

from config_manager import ConfigManager, Environment
from secrets import SecretsManager, SecretProvider


class ConfigSetup:
    """Interactive configuration setup"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        (self.config_dir / "environments").mkdir(exist_ok=True)
        
    def run_setup(self, environment: str, interactive: bool = True):
        """Run the configuration setup process"""
        print(f"🏥 Healthcare AI Configuration Setup")
        print(f"Environment: {environment}")
        print("-" * 50)
        
        # Initialize managers
        config_manager = ConfigManager(environment=environment)
        secrets_manager = SecretsManager()
        
        if interactive:
            # Interactive setup
            self._interactive_setup(environment, config_manager, secrets_manager)
        else:
            # Non-interactive setup with defaults
            self._default_setup(environment, config_manager, secrets_manager)
        
        # Generate final configuration files
        self._generate_config_files(environment, config_manager, secrets_manager)
        
        print("\n✅ Configuration setup complete!")
        print("\nNext steps:")
        print("1. Review the generated .env file")
        print("2. Update any placeholder values")
        print("3. Run: docker-compose up -d")
        
    def _interactive_setup(self, environment: str, config_manager: ConfigManager, secrets_manager: SecretsManager):
        """Interactive configuration setup"""
        print("\n📋 Let's configure your Healthcare AI system...\n")
        
        # Basic configuration
        app_name = input(f"Application name [{config_manager.load_config().get('application', {}).get('name', 'healthcare-ai')}]: ").strip()
        if not app_name:
            app_name = "healthcare-ai"
        
        # Network configuration
        print("\n🌐 Network Configuration")
        if environment == "development":
            network_host = input("Network host [localhost]: ").strip() or "localhost"
            protocol = "http"
        else:
            network_host = input("External host/domain (e.g., myapp.com): ").strip()
            protocol = input("Protocol [https]: ").strip() or "https"
        
        # FHIR Configuration
        print("\n🔗 FHIR Server Configuration")
        fhir_providers = {
            "1": "HAPI FHIR (Public)",
            "2": "SMART Health IT",
            "3": "Custom FHIR Server"
        }
        
        print("Available FHIR servers:")
        for key, name in fhir_providers.items():
            print(f"  {key}. {name}")
        
        fhir_choice = input("Select FHIR server [1]: ").strip() or "1"
        
        if fhir_choice == "1":
            fhir_base_url = "http://localhost:8080/fhir"
            fhir_client_id = "healthcare_ai_agent"
        elif fhir_choice == "2":
            fhir_base_url = "https://r4.smarthealthit.org"
            fhir_client_id = "healthcare_ai_agent"
        else:
            fhir_base_url = input("FHIR Base URL: ").strip()
            fhir_client_id = input("FHIR Client ID: ").strip()
        
        # API Keys
        print("\n🔑 API Configuration")
        openai_key = getpass.getpass("OpenAI API Key (hidden): ").strip()
        
        # Database Configuration
        print("\n💾 Database Configuration")
        if environment == "development":
            db_password = input("Database password [postgres]: ").strip() or "postgres"
        else:
            db_password = getpass.getpass("Database password (hidden): ").strip()
        
        # Redis Configuration
        print("\n📊 Redis Configuration")
        if environment == "development":
            redis_password = input("Redis password [leave empty]: ").strip()
        else:
            redis_password = getpass.getpass("Redis password (hidden): ").strip()
        
        # Feature Configuration
        print("\n🎛️  Feature Configuration")
        features = {
            "clinical_decision_support": self._ask_yes_no("Enable Clinical Decision Support", True),
            "drug_interaction_checking": self._ask_yes_no("Enable Drug Interaction Checking", True),
            "risk_scoring": self._ask_yes_no("Enable Risk Scoring", True),
            "audit_logging": self._ask_yes_no("Enable Audit Logging", environment != "development"),
            "mock_data": self._ask_yes_no("Enable Mock Data", environment == "development")
        }
        
        # Cloud Provider (optional)
        print("\n☁️  Cloud Provider Configuration (Optional)")
        cloud_providers = {
            "1": "None",
            "2": "Google Cloud Platform",
            "3": "Amazon Web Services", 
            "4": "Microsoft Azure"
        }
        
        print("Cloud providers:")
        for key, name in cloud_providers.items():
            print(f"  {key}. {name}")
        
        cloud_choice = input("Select cloud provider [1]: ").strip() or "1"
        cloud_config = {}
        
        if cloud_choice == "2":  # GCP
            cloud_config["gcp"] = {
                "project_id": input("GCP Project ID: ").strip(),
                "region": input("GCP Region [us-central1]: ").strip() or "us-central1"
            }
        elif cloud_choice == "3":  # AWS
            cloud_config["aws"] = {
                "region": input("AWS Region [us-east-1]: ").strip() or "us-east-1",
                "account_id": input("AWS Account ID: ").strip()
            }
        elif cloud_choice == "4":  # Azure
            cloud_config["azure"] = {
                "subscription_id": input("Azure Subscription ID: ").strip(),
                "location": input("Azure Location [eastus]: ").strip() or "eastus"
            }
        
        # Store configuration
        self.config_data = {
            "app_name": app_name,
            "network_host": network_host,
            "protocol": protocol,
            "fhir_base_url": fhir_base_url,
            "fhir_client_id": fhir_client_id,
            "openai_key": openai_key,
            "db_password": db_password,
            "redis_password": redis_password,
            "features": features,
            "cloud_config": cloud_config
        }
        
    def _default_setup(self, environment: str, config_manager: ConfigManager, secrets_manager: SecretsManager):
        """Non-interactive setup with defaults"""
        print("Setting up with default configuration...")
        
        self.config_data = {
            "app_name": "healthcare-ai",
            "network_host": "localhost" if environment == "development" else os.getenv("EXTERNAL_HOST", ""),
            "protocol": "http" if environment == "development" else "https",
            "fhir_base_url": "http://localhost:8080/fhir",
            "fhir_client_id": "healthcare_ai_agent",
            "openai_key": os.getenv("OPENAI_API_KEY", ""),
            "db_password": "postgres" if environment == "development" else os.getenv("DATABASE_PASSWORD", ""),
            "redis_password": "" if environment == "development" else os.getenv("REDIS_PASSWORD", ""),
            "features": {
                "clinical_decision_support": True,
                "drug_interaction_checking": True,
                "risk_scoring": True,
                "audit_logging": environment != "development",
                "mock_data": environment == "development"
            },
            "cloud_config": {}
        }
    
    def _ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{question} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        
        return response in ["y", "yes", "true", "1"]
    
    def _generate_config_files(self, environment: str, config_manager: ConfigManager, secrets_manager: SecretsManager):
        """Generate configuration files"""
        print("\n📄 Generating configuration files...")
        
        # Create environment file
        env_vars = self._generate_env_vars(environment)
        env_file_path = Path(".env")
        
        with open(env_file_path, "w") as f:
            f.write("\n".join(env_vars))
        
        print(f"✅ Generated: {env_file_path}")
        
        # Create docker-compose override if needed
        if environment == "development":
            self._create_docker_override()
        
        # Create Kubernetes manifests if needed
        if environment in ["staging", "production"]:
            self._create_kubernetes_manifests(environment)
        
        # Export secrets template
        secrets_manager.export_secrets_template()
        print("✅ Generated: secrets.env.template")
        
    def _generate_env_vars(self, environment: str) -> list:
        """Generate environment variables list"""
        env_vars = [
            f"# Healthcare AI Environment Configuration",
            f"# Environment: {environment}",
            f"# Generated: {os.popen('date').read().strip()}",
            "",
            "# Application Configuration",
            f"ENVIRONMENT={environment}",
            f"APP_NAME={self.config_data['app_name']}",
            "",
            "# Network Configuration",
            f"NETWORK_HOST={self.config_data['network_host']}",
            f"NETWORK_PROTOCOL={self.config_data['protocol']}",
            f"EXTERNAL_HOST={self.config_data['network_host']}",
            "",
            "# Service URLs (Generated dynamically)",
            f"CREWAI_API_URL={self.config_data['protocol']}://{self.config_data['network_host']}:8000",
            f"AUTOGEN_API_URL={self.config_data['protocol']}://{self.config_data['network_host']}:8001",
            f"AGENT_BACKEND_URL={self.config_data['protocol']}://{self.config_data['network_host']}:8002",
            f"FHIR_PROXY_URL={self.config_data['protocol']}://{self.config_data['network_host']}:8003",
            f"FHIR_MCP_URL={self.config_data['protocol']}://{self.config_data['network_host']}:8004",
            f"UI_URL={self.config_data['protocol']}://{self.config_data['network_host']}:3030",
            "",
            "# FHIR Configuration",
            f"FHIR_BASE_URL={self.config_data['fhir_base_url']}",
            f"FHIR_CLIENT_ID={self.config_data['fhir_client_id']}",
            "FHIR_CLIENT_SECRET=",
            "",
            "# Database Configuration", 
            f"DATABASE_PASSWORD={self.config_data['db_password']}",
            f"DATABASE_URL=postgresql://postgres:${{DATABASE_PASSWORD}}@{self.config_data['network_host']}:5432/healthcare_ai",
            "",
            "# Redis Configuration",
            f"REDIS_PASSWORD={self.config_data['redis_password']}",
            f"REDIS_URL=redis://:{self.config_data['redis_password']}@{self.config_data['network_host']}:6379/0" if self.config_data['redis_password'] else f"REDIS_URL=redis://{self.config_data['network_host']}:6379/0",
            "",
            "# API Keys",
            f"OPENAI_API_KEY={self.config_data['openai_key']}",
            "",
            "# Security",
            "JWT_SECRET_KEY=your_jwt_secret_key_here",
            "ENCRYPTION_KEY=your_32_character_encryption_key",
            "",
            "# Feature Flags"
        ]
        
        for feature, enabled in self.config_data['features'].items():
            env_var_name = f"ENABLE_{feature.upper()}"
            env_vars.append(f"{env_var_name}={str(enabled).lower()}")
        
        env_vars.extend([
            "",
            "# Performance Configuration", 
            "MAX_WORKERS=4",
            "REQUEST_TIMEOUT=300",
            "",
            "# Logging Configuration",
            f"LOG_LEVEL={'DEBUG' if environment == 'development' else 'INFO'}",
            f"LOG_FORMAT={'pretty' if environment == 'development' else 'json'}",
            ""
        ])
        
        return env_vars
    
    def _create_docker_override(self):
        """Create docker-compose override for development"""
        override_content = {
            "version": "3.8",
            "services": {
                "crewai-healthcare-agent": {
                    "ports": ["8000:8000"],
                    "environment": ["DEBUG=true"]
                },
                "autogen-healthcare-agent": {
                    "ports": ["8001:8001"], 
                    "environment": ["DEBUG=true"]
                },
                "healthcare-ui": {
                    "ports": ["3030:80"],
                    "environment": ["REACT_APP_ENABLE_MOCK_DATA=true"]
                }
            }
        }
        
        override_path = Path("docker-compose.override.yml")
        with open(override_path, "w") as f:
            yaml.dump(override_content, f, default_flow_style=False)
        
        print(f"✅ Generated: {override_path}")
    
    def _create_kubernetes_manifests(self, environment: str):
        """Create Kubernetes manifests for the environment"""
        k8s_dir = Path("kubernetes") / "manifests" / environment
        k8s_dir.mkdir(parents=True, exist_ok=True)
        
        # Create namespace
        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": f"healthcare-ai-{environment}",
                "labels": {
                    "environment": environment,
                    "app": "healthcare-ai"
                }
            }
        }
        
        with open(k8s_dir / "00-namespace.yaml", "w") as f:
            yaml.dump(namespace_manifest, f, default_flow_style=False)
        
        print(f"✅ Generated: kubernetes/manifests/{environment}/")

    def _write_dev_env_config(self, environment):
        """Write development-specific environment configuration"""
        config_content = f"""        # Network configuration
        network:
          host: "localhost"
          protocol: "http"
          external_host: "localhost"

        # Development-specific FHIR settings
        fhir:
          enable_test_data: true
          mock_endpoints: true
          timeout: 30
          max_retries: 3

        # Development database configuration
        database:
          pool_size: 5
          max_overflow: 10
          echo: true

        # Development features
        features:
          mock_data: true
          debug_mode: true
          hot_reload: true
          test_fixtures: true
          advanced_analytics: false
          audit_logging: false

        # Development logging
        logging:
          level: "DEBUG"
          format: "pretty"
          audit_enabled: false
          structured_logging: false

        # Development resources (minimal for local dev)
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"

        # Development scaling
        scaling:
          replicas: 1
          auto_scaling: false
          min_replicas: 1
          max_replicas: 1

        # Development monitoring (optional)
        monitoring:
          metrics_enabled: false
          tracing_enabled: false
          log_aggregation: false
          alerting: false

        # Development security (relaxed for local dev)
        security:
          cors:
            allow_origins: ["*"]
            allow_credentials: true
          rate_limiting:
            enabled: false
          jwt:
            expire_minutes: 1440  # 24 hours

        # Email configuration (disabled for development)
        email:
          enabled: false"""
        
        return config_content

    def _write_prod_env_config(self, environment):
        """Write production-specific environment configuration"""
        config_content = f"""        # Network configuration for production
        network:
          host: "${{EXTERNAL_HOST}}"
          domain: "${{DOMAIN_NAME}}"
          protocol: "https"
          external_host: "${{EXTERNAL_HOST}}"

        # Production FHIR settings
        fhir:
          enable_test_data: false
          mock_endpoints: false
          timeout: 60
          max_retries: 5

        # Production database configuration
        database:
          pool_size: 20
          max_overflow: 30
          echo: false

        # Production features
        features:
          mock_data: false
          debug_mode: false
          hot_reload: false
          test_fixtures: false
          advanced_analytics: true
          audit_logging: true

        # Production logging
        logging:
          level: "INFO"
          format: "json"
          audit_enabled: true
          structured_logging: true

        # Production resources
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

        # Production scaling
        scaling:
          replicas: 3
          auto_scaling: true
          min_replicas: 2
          max_replicas: 10

        # Production monitoring
        monitoring:
          metrics_enabled: true
          tracing_enabled: true
          log_aggregation: true
          alerting: true

        # Production security
        security:
          cors:
            allow_origins: ["${{ALLOWED_ORIGINS}}"]
            allow_credentials: true
          rate_limiting:
            enabled: true
            requests_per_minute: 1000
          jwt:
            expire_minutes: 480  # 8 hours

        # Email configuration
        email:
          enabled: true
          provider: "${{EMAIL_PROVIDER}}"
          smtp_host: "${{SMTP_HOST}}"
          smtp_port: 587
          use_tls: true"""
        
        return config_content


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Healthcare AI Configuration Setup")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="development",
        help="Target environment"
    )
    parser.add_argument(
        "--non-interactive", "-n",
        action="store_true",
        help="Run setup without prompts"
    )
    
    args = parser.parse_args()
    
    setup = ConfigSetup()
    setup.run_setup(args.environment, interactive=not args.non_interactive)


if __name__ == "__main__":
    main() 