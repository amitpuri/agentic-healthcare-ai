#!/usr/bin/env python3
"""
Configuration Manager for Healthcare AI Application
Handles loading, validation, and merging of configuration files
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class ServiceConfig:
    """Configuration for a single service"""
    name: str
    port: int
    path: str = "/"
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    replicas: int = 1
    
    @property
    def url(self) -> str:
        return f"http://{self.name}:{self.port}{self.path}"


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class ConfigManager:
    """
    Central configuration manager that handles:
    - Loading base configuration
    - Environment-specific overrides
    - Environment variable substitution
    - Configuration validation
    """
    
    def __init__(self, 
                 config_dir: str = "config",
                 environment: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config = None
        self._services = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """Load and merge all configuration files"""
        if self._config is None:
            self._config = self._load_and_merge_configs()
        return self._config
    
    def _load_and_merge_configs(self) -> Dict[str, Any]:
        """Load base config and merge with environment-specific overrides"""
        try:
            # Load base configuration
            base_config = self._load_yaml_file(self.config_dir / "base.yaml")
            
            # Load environment-specific configuration
            env_config_path = self.config_dir / "environments" / f"{self.environment}.yaml"
            env_config = {}
            
            if env_config_path.exists():
                env_config = self._load_yaml_file(env_config_path)
                logger.info(f"Loaded environment config for: {self.environment}")
            else:
                logger.warning(f"No environment config found for: {self.environment}")
            
            # Merge configurations (environment overrides base)
            merged_config = self._deep_merge(base_config, env_config)
            
            # Substitute environment variables
            merged_config = self._substitute_env_vars(merged_config)
            
            # Validate configuration
            self._validate_config(merged_config)
            
            return merged_config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file with error handling"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {file_path}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables"""
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            default_value = ""
            
            # Handle default values like ${VAR:default}
            if ":" in env_var:
                env_var, default_value = env_var.split(":", 1)
            
            return os.getenv(env_var, default_value)
        else:
            return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration"""
        required_sections = ["application", "services", "security"]
        
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate services have required fields
        if "services" in config:
            for service_name, service_config in config["services"].items():
                if not isinstance(service_config, dict):
                    continue
                    
                required_fields = ["name", "port"]
                for field in required_fields:
                    if field not in service_config:
                        logger.warning(f"Service {service_name} missing field: {field}")
    
    def get_service_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a specific service"""
        if service_name not in self._services:
            config = self.load_config()
            
            if "services" not in config or service_name not in config["services"]:
                raise ConfigurationError(f"Service configuration not found: {service_name}")
            
            service_data = config["services"][service_name]
            self._services[service_name] = ServiceConfig(**service_data)
            
        return self._services[service_name]
    
    def get_service_url(self, service_name: str, external: bool = False) -> str:
        """Get service URL (internal or external)"""
        config = self.load_config()
        
        # Check for environment-specific service URLs first
        service_urls = config.get("service_urls", {})
        url_key = f"{service_name.replace('-', '_')}_api"
        
        if url_key in service_urls:
            return service_urls[url_key]
        
        # Get network configuration
        network_config = config.get("network", {})
        host = network_config.get("host", "localhost")
        protocol = network_config.get("protocol", "http")
        external_host = network_config.get("external_host")
        domain = network_config.get("domain", "")
        
        # Get service configuration
        service_config = self.get_service_config(service_name)
        
        if external and external_host:
            # Use external host for external access
            if domain:
                return f"{protocol}://{service_name}.{domain}{service_config.path}"
            else:
                return f"{protocol}://{external_host}:{service_config.port}{service_config.path}"
        elif external and self.environment != "development":
            # In non-development environments, use service discovery
            return f"{protocol}://{service_config.name}-service:{service_config.port}{service_config.path}"
        else:
            # Use configured host (localhost for development)
            return f"{protocol}://{host}:{service_config.port}{service_config.path}"
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        config = self.load_config()
        db_config = config.get("database", {})
        
        # Try to get from environment first
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        # Get network configuration for host
        network_config = config.get("network", {})
        default_host = network_config.get("host", "localhost")
        
        # Build from configuration
        host = db_config.get("host", default_host)
        port = db_config.get("port", 5432)
        name = db_config.get("name", "healthcare_ai")
        username = db_config.get("username", "postgres")
        password = os.getenv("DATABASE_PASSWORD", "postgres")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{name}"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        config = self.load_config()
        redis_config = config.get("redis", {})
        
        # Try to get from environment first
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return redis_url
        
        # Get network configuration for host
        network_config = config.get("network", {})
        default_host = network_config.get("host", "localhost")
        
        # Build from configuration
        host = redis_config.get("host", default_host)
        port = redis_config.get("port", 6379)
        db = redis_config.get("db", 0)
        password = os.getenv("REDIS_PASSWORD", "")
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"
    
    def get_fhir_config(self) -> Dict[str, Any]:
        """Get FHIR configuration"""
        config = self.load_config()
        return config.get("fhir", {})
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        config = self.load_config()
        return config.get("features", {})
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.get_feature_flags().get(feature, False)
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        config = self.load_config()
        return config.get("security", {})
    
    def export_env_file(self, output_path: str = ".env") -> None:
        """Export configuration as environment file"""
        config = self.load_config()
        
        env_vars = []
        env_vars.append(f"# Generated environment file for {self.environment}")
        env_vars.append(f"# Generated on: {os.popen('date').read().strip()}")
        env_vars.append("")
        
        # Application settings
        env_vars.append("# Application Configuration")
        env_vars.append(f"ENVIRONMENT={self.environment}")
        env_vars.append(f"APP_NAME={config.get('application', {}).get('name', 'healthcare-ai')}")
        env_vars.append("")
        
        # Network Configuration
        network_config = config.get("network", {})
        env_vars.append("# Network Configuration")
        env_vars.append(f"NETWORK_HOST={network_config.get('host', 'localhost')}")
        env_vars.append(f"NETWORK_PROTOCOL={network_config.get('protocol', 'http')}")
        env_vars.append(f"EXTERNAL_HOST={network_config.get('external_host', '')}")
        env_vars.append(f"DOMAIN_NAME={network_config.get('domain', '')}")
        env_vars.append("")
        
        # Service URLs
        env_vars.append("# Service URLs")
        for service_name in config.get("services", {}):
            url = self.get_service_url(service_name)
            env_var_name = f"{service_name.upper().replace('-', '_')}_URL"
            env_vars.append(f"{env_var_name}={url}")
        env_vars.append("")
        
        # Database
        env_vars.append("# Database Configuration")
        env_vars.append(f"DATABASE_URL={self.get_database_url()}")
        env_vars.append("")
        
        # Redis
        env_vars.append("# Redis Configuration")
        env_vars.append(f"REDIS_URL={self.get_redis_url()}")
        env_vars.append("")
        
        # FHIR
        fhir_config = self.get_fhir_config()
        env_vars.append("# FHIR Configuration")
        env_vars.append(f"FHIR_BASE_URL={fhir_config.get('base_url', '')}")
        env_vars.append(f"FHIR_CLIENT_ID={fhir_config.get('client_id', '')}")
        env_vars.append("")
        
        # Feature flags
        env_vars.append("# Feature Flags")
        for feature, enabled in self.get_feature_flags().items():
            env_var_name = f"ENABLE_{feature.upper()}"
            env_vars.append(f"{env_var_name}={str(enabled).lower()}")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(env_vars))
        
        logger.info(f"Environment file exported to: {output_path}")


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> Dict[str, Any]:
    """Get the current configuration"""
    return config_manager.load_config()


def get_service_url(service_name: str, external: bool = False) -> str:
    """Get URL for a service"""
    return config_manager.get_service_url(service_name, external)


def get_database_url() -> str:
    """Get database URL"""
    return config_manager.get_database_url()


def get_redis_url() -> str:
    """Get Redis URL"""
    return config_manager.get_redis_url()


def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled"""
    return config_manager.is_feature_enabled(feature) 