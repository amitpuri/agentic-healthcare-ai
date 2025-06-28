# Healthcare AI Configuration System Improvements

## Overview
This document outlines the comprehensive configuration improvements implemented for the Healthcare AI application, addressing the need for better management of endpoints, ports, keys, and secrets across different environments.

## Key Improvements

### 1. Centralized Configuration Management

**Problem**: Configuration scattered across multiple files and hardcoded values
**Solution**: Unified configuration system with hierarchical overrides

```yaml
# config/base.yaml - Base configuration
application:
  name: "healthcare-ai"
  version: "1.0.0"

network:
  host: "localhost"
  domain: ""
  protocol: "http"
  external_host: "${EXTERNAL_HOST}"

services:
  crewai-agent:
    port: 8000
    path: "/"
    health_endpoint: "/health"
```

### 2. Dynamic Network Configuration

**Problem**: Hardcoded localhost URLs throughout the codebase
**Solution**: Configurable network settings with environment-specific overrides

#### Network Configuration Features:
- **Configurable Host**: Set network host via `NETWORK_HOST` environment variable
- **Protocol Support**: Switch between HTTP/HTTPS via `NETWORK_PROTOCOL`
- **External Access**: Configure external host for public access via `EXTERNAL_HOST`
- **Domain Support**: Use subdomain routing for services via `DOMAIN_NAME`

#### Examples:

**Development (Default)**:
```bash
NETWORK_HOST=localhost
NETWORK_PROTOCOL=http
```

**Custom Local Network**:
```bash
NETWORK_HOST=192.168.1.100
NETWORK_PROTOCOL=http
```

**Production with Domain**:
```bash
NETWORK_HOST=api.mycompany.com
NETWORK_PROTOCOL=https
EXTERNAL_HOST=api.mycompany.com
DOMAIN_NAME=mycompany.com
```

**Production with Load Balancer**:
```bash
NETWORK_HOST=my-load-balancer.com
NETWORK_PROTOCOL=https
EXTERNAL_HOST=my-load-balancer.com
```

### 3. Environment-Specific Configurations

#### Development (`config/environments/development.yaml`)
```yaml
environment: development
network:
  host: "localhost"
  protocol: "http"
  external_host: "localhost"

features:
  mock_data: true
  debug_mode: true
  hot_reload: true
```

#### Staging (`config/environments/staging.yaml`)
```yaml
environment: staging
network:
  host: "${STAGING_HOST}"
  domain: "${STAGING_DOMAIN}"
  protocol: "https"
  external_host: "${STAGING_HOST}"

features:
  mock_data: true
  debug_mode: false
  audit_logging: true
```

#### Production (`config/environments/production.yaml`)
```yaml
environment: production
network:
  host: "${EXTERNAL_HOST}"
  domain: "${DOMAIN_NAME}"
  protocol: "https"
  external_host: "${EXTERNAL_HOST}"

security:
  rate_limiting:
    enabled: true
  cors:
    allow_origins: ["${ALLOWED_ORIGINS}"]
```

### 4. Service URL Generation

**Problem**: Manual URL construction and maintenance
**Solution**: Automatic URL generation based on network configuration

```python
# Before (hardcoded)
url = "http://localhost:8000/health"

# After (dynamic)
from config.network_config import get_service_url
url = get_service_url("crewai-agent", 8000, "/health")
```

#### URL Generation Strategies:

1. **Development**: `http://localhost:8000`
2. **Custom Host**: `http://myserver.local:8000`
3. **Domain-based**: `https://crewai.mycompany.com`
4. **External with Port**: `https://api.mycompany.com:8000`

### 5. Docker Integration

**Enhanced Docker Compose Configuration**:
```yaml
services:
  crewai-healthcare-agent:
    environment:
      - NETWORK_HOST=${NETWORK_HOST:-localhost}
      - NETWORK_PROTOCOL=${NETWORK_PROTOCOL:-http}
      - EXTERNAL_HOST=${EXTERNAL_HOST:-localhost}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
```

**Usage Examples**:
```bash
# Development
NETWORK_HOST=localhost docker-compose up

# Custom network
NETWORK_HOST=192.168.1.100 docker-compose -f docker/docker-compose.config.yml up

# Production
ENVIRONMENT=production EXTERNAL_HOST=myapp.com docker-compose -f docker/docker-compose.config.yml up
```

### 6. Frontend Configuration

**Dynamic Environment Variables in React**:
```typescript
// Before
const apiUrl = 'http://localhost:8000';

// After
const networkHost = process.env.REACT_APP_NETWORK_HOST || 'localhost';
const networkProtocol = process.env.REACT_APP_NETWORK_PROTOCOL || 'http';
const apiUrl = `${networkProtocol}://${networkHost}:8000`;
```

**Build-time Configuration**:
```dockerfile
# Dockerfile for UI
ARG NETWORK_HOST=localhost
ARG NETWORK_PROTOCOL=http
ENV REACT_APP_NETWORK_HOST=$NETWORK_HOST
ENV REACT_APP_NETWORK_PROTOCOL=$NETWORK_PROTOCOL
```

## Configuration Files Structure

```
config/
├── base.yaml                    # Base configuration
├── config_manager.py           # Configuration management logic  
├── network_config.py           # Network configuration helper
├── secrets.py                  # Secrets management
└── environments/
    ├── development.yaml         # Development overrides
    ├── staging.yaml            # Staging overrides
    └── production.yaml         # Production overrides

scripts/
└── setup-config.py            # Interactive configuration setup

docker/
└── docker-compose.config.yml  # Docker with config integration
```

## Usage Guide

### 1. Quick Setup
```bash
# Interactive configuration
python scripts/setup-config.py

# Or use environment variables
export NETWORK_HOST="myserver.local"
export NETWORK_PROTOCOL="https"
export EXTERNAL_HOST="api.mycompany.com"
```

### 2. Development
```bash
# Default localhost
docker-compose -f docker/docker-compose.config.yml up

# Custom development host
NETWORK_HOST=192.168.1.100 docker-compose -f docker/docker-compose.config.yml up
```

### 3. Production Deployment
```bash
# With domain-based routing
ENVIRONMENT=production \
EXTERNAL_HOST=api.mycompany.com \
DOMAIN_NAME=mycompany.com \
docker-compose -f docker/docker-compose.config.yml up

# With load balancer
ENVIRONMENT=production \
EXTERNAL_HOST=my-lb.com \
NETWORK_PROTOCOL=https \
docker-compose -f docker/docker-compose.config.yml up
```

### 4. Testing Different Configurations
```bash
# Test with different hosts
python -c "
from config.network_config import NetworkConfig
nc = NetworkConfig()
print('Host:', nc.host)
print('Protocol:', nc.protocol)
print('API URL:', nc.get_api_base_url('crewai-agent'))
"
```

## Benefits

1. **Flexibility**: Easily adapt to different environments and deployment scenarios
2. **Maintainability**: Single source of truth for configuration
3. **Security**: Proper secrets management with environment-specific overrides
4. **Scalability**: Support for various deployment patterns (localhost, custom networks, domains, load balancers)
5. **Developer Experience**: Simple setup with sensible defaults
6. **Production Ready**: Comprehensive configuration for enterprise deployments

## Migration Guide

### From Hardcoded URLs

**Before**:
```typescript
const apiUrl = 'http://localhost:8000';
```

**After**:
```typescript
import { get_api_base_url } from '../config/network_config';
const apiUrl = get_api_base_url('crewai-agent');
```

### Environment Variables

**Add to your `.env` file**:
```bash
# Network Configuration
NETWORK_HOST=localhost
NETWORK_PROTOCOL=http
EXTERNAL_HOST=localhost

# For React app
REACT_APP_NETWORK_HOST=localhost
REACT_APP_NETWORK_PROTOCOL=http
```

### Docker Compose Updates

**Update your compose files**:
```yaml
environment:
  - NETWORK_HOST=${NETWORK_HOST:-localhost}
  - NETWORK_PROTOCOL=${NETWORK_PROTOCOL:-http}
  - EXTERNAL_HOST=${EXTERNAL_HOST:-localhost}
```

## Advanced Features

### 1. Health Check URL Generation
```python
from config.network_config import get_health_check_url
health_url = get_health_check_url('crewai-agent')
```

### 2. Environment URL Discovery
```python
from config.network_config import NetworkConfig
nc = NetworkConfig()
all_urls = nc.get_environment_urls()
print(all_urls)  # {'crewai-agent': 'http://localhost:8000', ...}
```

### 3. Configuration Validation
```python
from config.network_config import NetworkConfig
nc = NetworkConfig()
validation = nc.validate_configuration()
if not validation['valid']:
    print("Configuration issues:", validation['issues'])
```

This improved configuration system provides a robust foundation for managing the Healthcare AI application across different environments while maintaining flexibility and security. 