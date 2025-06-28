#!/usr/bin/env python3
"""
Network Configuration Helper for Healthcare AI Application
Centralizes host, protocol, and URL management
"""

import os
from typing import Dict, Any, Optional
from .config_manager import ConfigManager

class NetworkConfig:
    """
    Network configuration helper that provides standardized
    host, protocol, and URL management across all services
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self._config = None
        
    def _get_config(self) -> Dict[str, Any]:
        """Get configuration, cached"""
        if self._config is None:
            self._config = self.config_manager.load_config()
        return self._config
    
    @property
    def host(self) -> str:
        """Get the primary host"""
        config = self._get_config()
        network_config = config.get("network", {})
        
        # Check environment variable override first
        env_host = os.getenv("NETWORK_HOST")
        if env_host:
            return env_host
            
        return network_config.get("host", "localhost")
    
    @property
    def external_host(self) -> str:
        """Get the external host for public access"""
        config = self._get_config()
        network_config = config.get("network", {})
        
        # Check environment variable override first
        env_external_host = os.getenv("EXTERNAL_HOST")
        if env_external_host:
            return env_external_host
            
        return network_config.get("external_host", self.host)
    
    @property
    def protocol(self) -> str:
        """Get the protocol (http/https)"""
        config = self._get_config()
        network_config = config.get("network", {})
        
        # Check environment variable override first
        env_protocol = os.getenv("NETWORK_PROTOCOL")
        if env_protocol:
            return env_protocol
            
        return network_config.get("protocol", "http")
    
    @property
    def domain(self) -> str:
        """Get the domain name for subdomain-based services"""
        config = self._get_config()
        network_config = config.get("network", {})
        
        # Check environment variable override first
        env_domain = os.getenv("DOMAIN_NAME")
        if env_domain:
            return env_domain
            
        return network_config.get("domain", "")
    
    def get_service_url(self, service_name: str, port: int, path: str = "/", external: bool = False) -> str:
        """
        Generate service URL based on network configuration
        
        Args:
            service_name: Name of the service
            port: Service port
            path: Service path (default: "/")
            external: Whether to use external host/domain
            
        Returns:
            Complete service URL
        """
        if external and self.domain:
            # Use subdomain format: service.domain.com
            return f"{self.protocol}://{service_name}.{self.domain}{path}"
        elif external:
            # Use external host with port
            return f"{self.protocol}://{self.external_host}:{port}{path}"
        else:
            # Use internal/development host
            return f"{self.protocol}://{self.host}:{port}{path}"
    
    def get_database_host(self) -> str:
        """Get database host"""
        config = self._get_config()
        db_config = config.get("database", {})
        
        # Check for specific database host override
        db_host = db_config.get("host")
        if db_host:
            return db_host
            
        # Fall back to network host
        return self.host
    
    def get_redis_host(self) -> str:
        """Get Redis host"""
        config = self._get_config()
        redis_config = config.get("redis", {})
        
        # Check for specific Redis host override
        redis_host = redis_config.get("host")
        if redis_host:
            return redis_host
            
        # Fall back to network host
        return self.host
    
    def get_ui_base_url(self, external: bool = False) -> str:
        """Get UI base URL"""
        config = self._get_config()
        ui_service = config.get("services", {}).get("ui", {})
        port = ui_service.get("port", 3030)
        
        return self.get_service_url("ui", port, "/", external)
    
    def get_api_base_url(self, service: str, external: bool = False) -> str:
        """
        Get API base URL for a specific service
        
        Args:
            service: Service name (e.g., 'crewai-agent', 'autogen-agent')
            external: Whether to use external host
            
        Returns:
            API base URL
        """
        config = self._get_config()
        service_config = config.get("services", {}).get(service, {})
        
        if not service_config:
            raise ValueError(f"Service '{service}' not found in configuration")
        
        port = service_config.get("port")
        path = service_config.get("path", "/")
        
        return self.get_service_url(service, port, path, external)
    
    def get_health_check_url(self, service: str, external: bool = False) -> str:
        """
        Get health check URL for a service
        
        Args:
            service: Service name
            external: Whether to use external host
            
        Returns:
            Health check URL
        """
        config = self._get_config()
        service_config = config.get("services", {}).get(service, {})
        
        if not service_config:
            raise ValueError(f"Service '{service}' not found in configuration")
        
        port = service_config.get("port")
        health_endpoint = service_config.get("health_endpoint", "/health")
        
        return self.get_service_url(service, port, health_endpoint, external)
    
    def get_environment_urls(self) -> Dict[str, str]:
        """
        Get all service URLs for the current environment
        
        Returns:
            Dictionary mapping service names to URLs
        """
        config = self._get_config()
        services = config.get("services", {})
        urls = {}
        
        for service_name, service_config in services.items():
            if isinstance(service_config, dict) and "port" in service_config:
                port = service_config["port"]
                path = service_config.get("path", "/")
                urls[service_name] = self.get_service_url(service_name, port, path)
        
        return urls
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate network configuration
        
        Returns:
            Validation results with any errors or warnings
        """
        issues = []
        warnings = []
        
        # Validate host
        if not self.host:
            issues.append("Network host is not configured")
        
        # Validate protocol
        if self.protocol not in ["http", "https"]:
            issues.append(f"Invalid protocol: {self.protocol}. Must be 'http' or 'https'")
        
        # Validate external configuration
        if self.external_host == "localhost" and self.protocol == "https":
            warnings.append("Using HTTPS with localhost may cause certificate issues")
        
        # Validate domain configuration
        if self.domain and not self.external_host:
            warnings.append("Domain specified but external_host not configured")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "configuration": {
                "host": self.host,
                "external_host": self.external_host,
                "protocol": self.protocol,
                "domain": self.domain
            }
        }


# Global network configuration instance
network_config = NetworkConfig()


def get_service_url(service_name: str, port: int, path: str = "/", external: bool = False) -> str:
    """Get service URL using global network configuration"""
    return network_config.get_service_url(service_name, port, path, external)


def get_api_base_url(service: str, external: bool = False) -> str:
    """Get API base URL using global network configuration"""
    return network_config.get_api_base_url(service, external)


def get_host() -> str:
    """Get the configured host"""
    return network_config.host


def get_external_host() -> str:
    """Get the configured external host"""
    return network_config.external_host


def get_protocol() -> str:
    """Get the configured protocol"""
    return network_config.protocol 