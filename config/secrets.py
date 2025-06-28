#!/usr/bin/env python3
"""
Secrets Management for Healthcare AI Application
Handles secure storage and retrieval of sensitive configuration
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger(__name__)


class SecretProvider(Enum):
    """Supported secret providers"""
    ENVIRONMENT = "environment"
    FILE = "file"
    KUBERNETES = "kubernetes"
    AZURE_KEYVAULT = "azure_keyvault"
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    GCP_SECRET_MANAGER = "gcp_secret_manager"
    HASHICORP_VAULT = "hashicorp_vault"


@dataclass
class SecretConfig:
    """Configuration for secret providers"""
    provider: SecretProvider
    config: Dict[str, Any]


class SecretsManager:
    """
    Centralized secrets management that supports multiple backends
    """
    
    def __init__(self, provider: SecretProvider = SecretProvider.ENVIRONMENT):
        self.provider = provider
        self._cache = {}
        self._secret_configs = {}
        
        # Initialize provider-specific configuration
        self._init_provider()
    
    def _init_provider(self) -> None:
        """Initialize the selected secret provider"""
        if self.provider == SecretProvider.KUBERNETES:
            self._init_kubernetes()
        elif self.provider == SecretProvider.AZURE_KEYVAULT:
            self._init_azure_keyvault()
        elif self.provider == SecretProvider.AWS_SECRETS_MANAGER:
            self._init_aws_secrets_manager()
        elif self.provider == SecretProvider.GCP_SECRET_MANAGER:
            self._init_gcp_secret_manager()
    
    def _init_kubernetes(self) -> None:
        """Initialize Kubernetes secrets access"""
        self.secret_namespace = os.getenv("KUBERNETES_NAMESPACE", "healthcare-ai")
        self.secret_mount_path = "/var/secrets"
    
    def _init_azure_keyvault(self) -> None:
        """Initialize Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            vault_url = os.getenv("AZURE_KEYVAULT_URL")
            if not vault_url:
                raise ValueError("AZURE_KEYVAULT_URL environment variable required")
            
            credential = DefaultAzureCredential()
            self.azure_client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info("Azure Key Vault client initialized")
            
        except ImportError:
            logger.error("Azure SDK not available. Install with: pip install azure-keyvault-secrets azure-identity")
            raise
    
    def _init_aws_secrets_manager(self) -> None:
        """Initialize AWS Secrets Manager"""
        try:
            import boto3
            
            self.aws_region = os.getenv("AWS_REGION", "us-east-1")
            self.aws_client = boto3.client("secretsmanager", region_name=self.aws_region)
            logger.info("AWS Secrets Manager client initialized")
            
        except ImportError:
            logger.error("AWS SDK not available. Install with: pip install boto3")
            raise
    
    def _init_gcp_secret_manager(self) -> None:
        """Initialize GCP Secret Manager"""
        try:
            from google.cloud import secretmanager
            
            self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
            if not self.gcp_project_id:
                raise ValueError("GCP_PROJECT_ID environment variable required")
            
            self.gcp_client = secretmanager.SecretManagerServiceClient()
            logger.info("GCP Secret Manager client initialized")
            
        except ImportError:
            logger.error("GCP SDK not available. Install with: pip install google-cloud-secret-manager")
            raise
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value using the configured provider
        
        Args:
            secret_name: Name of the secret
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        try:
            value = None
            
            if self.provider == SecretProvider.ENVIRONMENT:
                value = self._get_env_secret(secret_name)
            elif self.provider == SecretProvider.FILE:
                value = self._get_file_secret(secret_name)
            elif self.provider == SecretProvider.KUBERNETES:
                value = self._get_kubernetes_secret(secret_name)
            elif self.provider == SecretProvider.AZURE_KEYVAULT:
                value = self._get_azure_secret(secret_name)
            elif self.provider == SecretProvider.AWS_SECRETS_MANAGER:
                value = self._get_aws_secret(secret_name)
            elif self.provider == SecretProvider.GCP_SECRET_MANAGER:
                value = self._get_gcp_secret(secret_name)
            
            # Cache the value
            if value is not None:
                self._cache[secret_name] = value
                return value
            
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
        
        return default
    
    def _get_env_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from environment variables"""
        return os.getenv(secret_name)
    
    def _get_file_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from file system"""
        secret_file = Path(f"/var/secrets/{secret_name}")
        if secret_file.exists():
            return secret_file.read_text().strip()
        return None
    
    def _get_kubernetes_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Kubernetes secret mount"""
        secret_file = Path(self.secret_mount_path) / secret_name
        if secret_file.exists():
            return secret_file.read_text().strip()
        return None
    
    def _get_azure_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        try:
            secret = self.azure_client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.warning(f"Failed to get Azure secret {secret_name}: {e}")
            return None
    
    def _get_aws_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            response = self.aws_client.get_secret_value(SecretId=secret_name)
            return response.get("SecretString")
        except Exception as e:
            logger.warning(f"Failed to get AWS secret {secret_name}: {e}")
            return None
    
    def _get_gcp_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from GCP Secret Manager"""
        try:
            name = f"projects/{self.gcp_project_id}/secrets/{secret_name}/versions/latest"
            response = self.gcp_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.warning(f"Failed to get GCP secret {secret_name}: {e}")
            return None
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Set a secret value (provider dependent)
        
        Args:
            secret_name: Name of the secret
            secret_value: Value to store
            
        Returns:
            True if successful
        """
        try:
            if self.provider == SecretProvider.AZURE_KEYVAULT:
                self.azure_client.set_secret(secret_name, secret_value)
                return True
            elif self.provider == SecretProvider.AWS_SECRETS_MANAGER:
                self.aws_client.create_secret(Name=secret_name, SecretString=secret_value)
                return True
            elif self.provider == SecretProvider.GCP_SECRET_MANAGER:
                parent = f"projects/{self.gcp_project_id}"
                self.gcp_client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_name,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
                self.gcp_client.add_secret_version(
                    request={
                        "parent": f"{parent}/secrets/{secret_name}",
                        "payload": {"data": secret_value.encode("UTF-8")},
                    }
                )
                return True
            else:
                logger.warning(f"Setting secrets not supported for provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set secret {secret_name}: {e}")
            return False
    
    def generate_secret(self, secret_name: str, length: int = 32) -> str:
        """
        Generate a secure random secret
        
        Args:
            secret_name: Name for the secret
            length: Length of the secret
            
        Returns:
            Generated secret value
        """
        secret_value = secrets.token_urlsafe(length)
        
        # Try to store it
        if self.set_secret(secret_name, secret_value):
            logger.info(f"Generated and stored secret: {secret_name}")
        else:
            logger.warning(f"Generated secret {secret_name} but could not store")
        
        return secret_value
    
    def get_database_password(self) -> str:
        """Get database password with fallback"""
        return self.get_secret("DATABASE_PASSWORD") or \
               self.get_secret("POSTGRES_PASSWORD") or \
               "postgres"
    
    def get_redis_password(self) -> str:
        """Get Redis password with fallback"""
        return self.get_secret("REDIS_PASSWORD") or ""
    
    def get_openai_api_key(self) -> str:
        """Get OpenAI API key"""
        return self.get_secret("OPENAI_API_KEY") or \
               self.get_secret("OPENAI_API_KEY_TEST") or ""
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        return self.get_secret("JWT_SECRET_KEY") or \
               self.generate_secret("JWT_SECRET_KEY", 64)
    
    def get_encryption_key(self) -> str:
        """Get encryption key"""
        return self.get_secret("ENCRYPTION_KEY") or \
               self.generate_secret("ENCRYPTION_KEY", 32)
    
    def get_fhir_credentials(self) -> Dict[str, str]:
        """Get FHIR server credentials"""
        return {
            "client_id": self.get_secret("FHIR_CLIENT_ID", "healthcare_ai_agent"),
            "client_secret": self.get_secret("FHIR_CLIENT_SECRET", ""),
            "access_token": self.get_secret("FHIR_ACCESS_TOKEN", "")
        }
    
    def get_cloud_credentials(self, provider: str) -> Dict[str, str]:
        """Get cloud provider credentials"""
        if provider.lower() == "gcp":
            return {
                "project_id": self.get_secret("GCP_PROJECT_ID", ""),
                "service_account_key": self.get_secret("GCP_SA_KEY", "")
            }
        elif provider.lower() == "aws":
            return {
                "access_key_id": self.get_secret("AWS_ACCESS_KEY_ID", ""),
                "secret_access_key": self.get_secret("AWS_SECRET_ACCESS_KEY", ""),
                "region": self.get_secret("AWS_REGION", "us-east-1")
            }
        elif provider.lower() == "azure":
            return {
                "subscription_id": self.get_secret("AZURE_SUBSCRIPTION_ID", ""),
                "client_id": self.get_secret("AZURE_CLIENT_ID", ""),
                "client_secret": self.get_secret("AZURE_CLIENT_SECRET", ""),
                "tenant_id": self.get_secret("AZURE_TENANT_ID", "")
            }
        else:
            return {}
    
    def validate_required_secrets(self, required_secrets: list) -> bool:
        """
        Validate that all required secrets are available
        
        Args:
            required_secrets: List of required secret names
            
        Returns:
            True if all secrets are available
        """
        missing_secrets = []
        
        for secret_name in required_secrets:
            if not self.get_secret(secret_name):
                missing_secrets.append(secret_name)
        
        if missing_secrets:
            logger.error(f"Missing required secrets: {missing_secrets}")
            return False
        
        return True
    
    def export_secrets_template(self, output_path: str = "secrets.env.template") -> None:
        """Export a template for required secrets"""
        secrets_template = [
            "# Secrets Template for Healthcare AI Application",
            "# Copy this file to secrets.env and fill in the values",
            "",
            "# Core API Keys",
            "OPENAI_API_KEY=your_openai_api_key_here",
            "",
            "# Database Credentials",
            "DATABASE_PASSWORD=your_secure_database_password",
            "POSTGRES_PASSWORD=your_secure_database_password",
            "",
            "# Redis Credentials",
            "REDIS_PASSWORD=your_redis_password",
            "",
            "# FHIR Server Credentials",
            "FHIR_CLIENT_ID=healthcare_ai_agent",
            "FHIR_CLIENT_SECRET=your_fhir_client_secret",
            "FHIR_ACCESS_TOKEN=your_fhir_access_token",
            "",
            "# Security Keys",
            "JWT_SECRET_KEY=your_jwt_secret_key_min_64_chars",
            "ENCRYPTION_KEY=your_32_character_encryption_key",
            "",
            "# Monitoring",
            "GRAFANA_PASSWORD=your_grafana_admin_password",
            "",
            "# Cloud Provider Credentials (Optional)",
            "# Google Cloud Platform",
            "GCP_PROJECT_ID=your_gcp_project_id",
            "GCP_SA_KEY=your_service_account_key_json",
            "",
            "# Amazon Web Services",
            "AWS_ACCESS_KEY_ID=your_aws_access_key_id",
            "AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key",
            "",
            "# Microsoft Azure",
            "AZURE_SUBSCRIPTION_ID=your_azure_subscription_id",
            "AZURE_CLIENT_ID=your_azure_client_id",
            "AZURE_CLIENT_SECRET=your_azure_client_secret",
            "AZURE_TENANT_ID=your_azure_tenant_id",
            "",
            "# Email Configuration (Optional)",
            "SMTP_USERNAME=your_email@example.com",
            "SMTP_PASSWORD=your_email_password",
        ]
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(secrets_template))
        
        logger.info(f"Secrets template exported to: {output_path}")


# Global secrets manager instance
secrets_manager = SecretsManager()


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret value"""
    return secrets_manager.get_secret(secret_name, default)


def get_database_password() -> str:
    """Get database password"""
    return secrets_manager.get_database_password()


def get_openai_api_key() -> str:
    """Get OpenAI API key"""
    return secrets_manager.get_openai_api_key()


def get_jwt_secret() -> str:
    """Get JWT secret"""
    return secrets_manager.get_jwt_secret() 