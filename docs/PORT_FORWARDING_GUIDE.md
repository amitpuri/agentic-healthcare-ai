# Port Forwarding Guide

This guide explains how to use the automated port forwarding scripts to access Healthcare AI services running in Kubernetes.

## 📋 Overview

The port forwarding scripts (`port-forward.sh` for Linux/macOS and `port-forward.ps1` for Windows) provide an easy way to access Kubernetes services from your local machine. They manage multiple kubectl port-forward processes and provide status monitoring.

## 🚀 Quick Start

### Linux/macOS/WSL
```bash
# Start essential services (UI + FHIR Proxy)
./port-forward.sh start

# Check what's running
./port-forward.sh status

# Access the main application
open http://localhost:3080
```

### Windows PowerShell
```powershell
# Start essential services (UI + FHIR Proxy)
.\port-forward.ps1 start

# Check what's running
.\port-forward.ps1 status

# Access the main application
Start-Process "http://localhost:3080"
```

## 📚 Available Commands

| Command | Description |
|---------|-------------|
| `start` | Start essential services (UI + FHIR Proxy) |
| `start-all` | Start all available services |
| `stop` | Stop all port forwards |
| `restart` | Restart all port forwards |
| `status` | Show current status of all port forwards |
| `test` | Test connectivity to running services |
| `help` | Show help message |

## 🌐 Service Ports

### Essential Services (Priority 1-2)
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Healthcare UI | 3080 | http://localhost:3080 | Main application interface |
| FHIR Proxy | 8003 | http://localhost:8003 | CORS handler for FHIR requests |

### Additional Services (Priority 3+)
| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Prometheus | 9090 | http://localhost:9090 | Metrics collection and monitoring |
| Grafana | 3000 | http://localhost:3000 | Dashboards and visualizations |
| Kibana | 5601 | http://localhost:5601 | Log analysis and search |
| Elasticsearch | 9200 | http://localhost:9200 | Search engine (API access) |
| PostgreSQL | 5432 | localhost:5432 | Database (direct connection) |
| Redis | 6379 | localhost:6379 | Cache (direct connection) |

## 🔧 Usage Examples

### Scenario 1: Development Work
Start only essential services for development:

```bash
# Linux/macOS/WSL
./port-forward.sh start

# Windows PowerShell
.\port-forward.ps1 start
```

This starts:
- Healthcare UI on port 3080
- FHIR Proxy on port 8003

### Scenario 2: Full Monitoring Setup
Start all services for comprehensive monitoring:

```bash
# Linux/macOS/WSL
./port-forward.sh start-all

# Windows PowerShell
.\port-forward.ps1 start-all
```

This starts all 8 services listed above.

### Scenario 3: Check What's Running
```bash
# Linux/macOS/WSL
./port-forward.sh status

# Windows PowerShell
.\port-forward.ps1 status
```

Example output:
```
================================================
  Healthcare AI Port Forward Manager
================================================

📊 Port Forward Status:

healthcare-ui-service     3080   ✅ RUNNING (PID: 12345)
fhir-proxy               8003   ✅ RUNNING (PID: 12346)
prometheus-service       9090   ❌ STOPPED
grafana-service          3000   ❌ STOPPED
kibana-service           5601   ❌ STOPPED
elasticsearch-service    9200   ❌ STOPPED
postgres-service         5432   ❌ STOPPED
redis-service           6379   ❌ STOPPED

🌐 Access URLs:
   Healthcare UI (Main Application): http://localhost:3080
   FHIR Proxy (CORS Handler):        http://localhost:8003
```

### Scenario 4: Test Service Connectivity
```bash
# Linux/macOS/WSL
./port-forward.sh test

# Windows PowerShell
.\port-forward.ps1 test
```

This tests HTTP connectivity to all running services.

## 🛠️ Troubleshooting

### Port Already in Use
If you see "Port already in use" warnings:

1. Check if port forwards are already running:
   ```bash
   ./port-forward.sh status
   ```

2. If shown as "PORT IN USE" but not managed by the script, find the process:
   ```bash
   # Linux/macOS
   lsof -i :3080
   
   # Windows
   netstat -ano | findstr :3080
   ```

3. Kill the conflicting process or use `./port-forward.sh stop` to clean up

### Services Not Responding
If services show as running but don't respond:

1. Check if Kubernetes services are healthy:
   ```bash
   kubectl get pods -n healthcare-ai
   kubectl get services -n healthcare-ai
   ```

2. Restart the port forwards:
   ```bash
   ./port-forward.sh restart
   ```

3. Check Kubernetes logs:
   ```bash
   kubectl logs -f deployment/healthcare-ui -n healthcare-ai
   ```

### Script Permission Issues (Linux/macOS)
```bash
# Make script executable
chmod +x port-forward.sh

# Run with bash if needed
bash port-forward.sh start
```

### PowerShell Execution Policy (Windows)
If you get execution policy errors:

```powershell
# Check current policy
Get-ExecutionPolicy

# Allow local scripts (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run directly
powershell -ExecutionPolicy Bypass -File .\port-forward.ps1 start
```

## 🔄 Advanced Usage

### Background Process Management
The scripts automatically manage background processes:

- **Linux/macOS**: Uses background processes with PID tracking
- **Windows**: Uses PowerShell Jobs with job ID tracking

### Cleanup on Exit
The scripts handle cleanup:

- Store process/job IDs in `.port-forward-pids/` directory
- Clean up stale PID files automatically
- Kill orphaned processes when stopping

### Priority-Based Starting
Services are started in priority order:

1. **Priority 1**: Healthcare UI (essential)
2. **Priority 2**: FHIR Proxy (essential)
3. **Priority 3-8**: Monitoring and database services

## 🚨 Important Notes

### Network Requirements
- Ensure Kubernetes cluster is running and accessible
- Verify all required services are deployed in `healthcare-ai` namespace
- Check that services have the expected names (as defined in Kubernetes manifests)

### Resource Usage
- Each port forward uses minimal resources
- Multiple port forwards can impact system performance
- Use `start` instead of `start-all` if you only need essential services

### Security Considerations
- Port forwards expose Kubernetes services to localhost only
- No external network access is provided
- Database credentials are still required for direct database connections

## 📞 Getting Help

Run the help command for built-in assistance:

```bash
# Linux/macOS/WSL
./port-forward.sh help

# Windows PowerShell
.\port-forward.ps1 help
```

For more detailed troubleshooting, see the main [README.md](README.md) file. 