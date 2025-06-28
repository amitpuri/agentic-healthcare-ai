# Healthcare AI Kubernetes Port Forward Manager (PowerShell)
# Manages port forwarding for all services in the Healthcare AI system

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Configuration
$NAMESPACE = "healthcare-ai"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PID_DIR = Join-Path $SCRIPT_DIR ".port-forward-pids"

# Service definitions
$SERVICES = @(
    @{Name="healthcare-ui-service"; LocalPort=3080; ServicePort=80; Priority=1; Description="Healthcare UI (Main Application)"}
    @{Name="fhir-mcp-server"; LocalPort=8004; ServicePort=8004; Priority=2; Description="FHIR MCP Server (Patient Data)"}
    @{Name="fhir-proxy"; LocalPort=8003; ServicePort=8003; Priority=3; Description="FHIR Proxy (CORS Handler)"}
    @{Name="agent-backend"; LocalPort=8002; ServicePort=8002; Priority=4; Description="Agent Backend (AI Coordination)"}
    @{Name="crewai-healthcare-agent"; LocalPort=8000; ServicePort=8000; Priority=5; Description="CrewAI Agent (Team-based AI)"}
    @{Name="autogen-healthcare-agent"; LocalPort=8001; ServicePort=8001; Priority=6; Description="AutoGen Agent (Conversational AI)"}
    @{Name="prometheus-service"; LocalPort=9090; ServicePort=9090; Priority=7; Description="Prometheus (Metrics)"}
    @{Name="grafana-service"; LocalPort=3000; ServicePort=3000; Priority=8; Description="Grafana (Dashboards)"}
    @{Name="kibana-service"; LocalPort=5601; ServicePort=5601; Priority=9; Description="Kibana (Log Analysis)"}
    @{Name="elasticsearch-service"; LocalPort=9200; ServicePort=9200; Priority=10; Description="Elasticsearch (Search Engine)"}
    @{Name="postgres-service"; LocalPort=5432; ServicePort=5432; Priority=11; Description="PostgreSQL (Database)"}
    @{Name="redis-service"; LocalPort=6379; ServicePort=6379; Priority=12; Description="Redis (Cache)"}
)

# Create PID directory if it doesn't exist
if (-not (Test-Path $PID_DIR)) {
    New-Item -ItemType Directory -Path $PID_DIR -Force | Out-Null
}

# Function to print colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to print header
function Write-Header {
    Write-Host ""
    Write-ColorOutput "================================================" "Cyan"
    Write-ColorOutput "  Healthcare AI Port Forward Manager" "Cyan"
    Write-ColorOutput "================================================" "Cyan"
    Write-Host ""
}

# Function to check if kubectl is available and cluster is accessible
function Test-KubectlAccess {
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "❌ kubectl not found. Please install kubectl first." "Red"
        exit 1
    }

    try {
        kubectl cluster-info 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Cluster not accessible"
        }
    }
    catch {
        Write-ColorOutput "❌ Cannot connect to Kubernetes cluster. Is KIND running?" "Red"
        Write-ColorOutput "💡 Try: .\kind.exe create cluster --name healthcare-ai" "Yellow"
        exit 1
    }

    try {
        kubectl get namespace $NAMESPACE 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Namespace not found"
        }
    }
    catch {
        Write-ColorOutput "❌ Namespace '$NAMESPACE' not found." "Red"
        Write-ColorOutput "💡 Try: kubectl apply -f manifests/00-namespace.yaml" "Yellow"
        exit 1
    }
}

# Function to check if port is in use
function Test-PortInUse {
    param([int]$Port)
    
    try {
        $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
        $endpoints = $listener.GetActiveTcpListeners()
        return $endpoints | Where-Object { $_.Port -eq $Port }
    }
    catch {
        return $false
    }
}

# Function to get process using a port
function Get-PortProcess {
    param([int]$Port)
    
    try {
        $result = netstat -ano | Select-String ":$Port "
        if ($result) {
            $pid = ($result -split '\s+')[-1]
            return $pid
        }
    }
    catch {
        return $null
    }
    return $null
}

# Function to start port forward for a service
function StartPortForward {
    param(
        [string]$ServiceName,
        [int]$LocalPort,
        [int]$ServicePort,
        [string]$Description
    )
    
    $pidFile = Join-Path $PID_DIR "$ServiceName.pid"
    
    # Check if already running
    if (Test-Path $pidFile) {
        $existingPid = Get-Content $pidFile
        try {
            $process = Get-Process -Id $existingPid -ErrorAction Stop
            Write-ColorOutput "⚠️  Port forward already running for $ServiceName (PID: $existingPid)" "Yellow"
            return $true
        }
        catch {
            Remove-Item $pidFile -ErrorAction SilentlyContinue
        }
    }
    
    # Check if port is in use
    if (Test-PortInUse -Port $LocalPort) {
        $portPid = Get-PortProcess -Port $LocalPort
        Write-ColorOutput "⚠️  Port $LocalPort already in use by PID: $portPid" "Yellow"
        Write-ColorOutput "    This might be an existing port forward. Use 'status' to check." "Yellow"
        return $false
    }
    
    # Check if service exists
    try {
        kubectl get service $ServiceName -n $NAMESPACE 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Service not found"
        }
    }
    catch {
        Write-ColorOutput "❌ Service $ServiceName not found in namespace $NAMESPACE" "Red"
        return $false
    }
    
    Write-ColorOutput "🚀 Starting port forward: $Description" "Blue"
    Write-ColorOutput "   $ServiceName`:$LocalPort -> $ServicePort" "Cyan"
    
    # Start port forward in background
    $job = Start-Job -ScriptBlock {
        param($ServiceName, $LocalPort, $ServicePort, $Namespace)
        kubectl port-forward "service/$ServiceName" "$LocalPort`:$ServicePort" -n $Namespace
    } -ArgumentList $ServiceName, $LocalPort, $ServicePort, $NAMESPACE
    
    # Save job ID as PID
    $job.Id | Out-File $pidFile
    
    # Wait a moment and check if it's still running
    Start-Sleep 2
    $runningJob = Get-Job -Id $job.Id -ErrorAction SilentlyContinue
    if ($runningJob -and $runningJob.State -eq "Running") {
        Write-ColorOutput "✅ Port forward started successfully (Job ID: $($job.Id))" "Green"
        Write-ColorOutput "   Access at: http://localhost:$LocalPort" "Cyan"
        return $true
    }
    else {
        Write-ColorOutput "❌ Failed to start port forward for $ServiceName" "Red"
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        return $false
    }
}

# Function to stop port forward for a service
function StopPortForward {
    param([string]$ServiceName)
    
    $pidFile = Join-Path $PID_DIR "$ServiceName.pid"
    
    if (Test-Path $pidFile) {
        $jobId = Get-Content $pidFile
        try {
            $job = Get-Job -Id $jobId -ErrorAction Stop
            Stop-Job -Job $job -PassThru | Remove-Job
            Remove-Item $pidFile
            Write-ColorOutput "✅ Stopped port forward for $ServiceName (Job ID: $jobId)" "Green"
        }
        catch {
            Write-ColorOutput "⚠️  Port forward job not found for $ServiceName" "Yellow"
            Remove-Item $pidFile -ErrorAction SilentlyContinue
        }
    }
    else {
        Write-ColorOutput "⚠️  No port forward found for $ServiceName" "Yellow"
    }
}

# Function to show status of all port forwards
function ShowStatus {
    Write-Header
    Write-ColorOutput "📊 Port Forward Status:" "Blue"
    Write-Host ""
    
    $anyRunning = $false
    
    foreach ($service in $SERVICES) {
        $pidFile = Join-Path $PID_DIR "$($service.Name).pid"
        
        Write-Host ("{0,-25} {1,-6} " -f $service.Name, $service.LocalPort) -NoNewline
        
        if (Test-Path $pidFile) {
            $jobId = Get-Content $pidFile
            if ($jobId -and $jobId.Trim() -ne "") {
                try {
                    $job = Get-Job -Id $jobId -ErrorAction Stop
                if ($job.State -eq "Running") {
                    Write-ColorOutput "✅ RUNNING (Job ID: $jobId)" "Green"
                    $anyRunning = $true
                }
                else {
                    Write-ColorOutput "❌ STOPPED (stale job)" "Red"
                    Remove-Item $pidFile -ErrorAction SilentlyContinue
                }
                }
                catch {
                    Write-ColorOutput "❌ STOPPED (stale PID file)" "Red"
                    Remove-Item $pidFile -ErrorAction SilentlyContinue
                }
            }
            else {
                Write-ColorOutput "❌ STOPPED (empty PID file)" "Red"
                Remove-Item $pidFile -ErrorAction SilentlyContinue
            }
        }
        else {
            if (Test-PortInUse -Port $service.LocalPort) {
                $portPid = Get-PortProcess -Port $service.LocalPort
                Write-ColorOutput "⚠️  PORT IN USE (PID: $portPid)" "Yellow"
            }
            else {
                Write-ColorOutput "❌ STOPPED" "Red"
            }
        }
    }
    
    Write-Host ""
    if ($anyRunning) {
        Write-ColorOutput "🌐 Access URLs:" "Green"
        foreach ($service in $SERVICES) {
            $pidFile = Join-Path $PID_DIR "$($service.Name).pid"
            
            if ((Test-Path $pidFile)) {
                $jobId = Get-Content $pidFile
                if ($jobId -and $jobId.Trim() -ne "") {
                    try {
                        $job = Get-Job -Id $jobId -ErrorAction Stop
                    if ($job.State -eq "Running") {
                        Write-Host ("   {0,-25} http://localhost:{1}" -f "$($service.Description):", $service.LocalPort)
                    }
                    }
                    catch {
                        # Job not found, skip
                    }
                }
            }
        }
    }
    else {
        Write-ColorOutput "💡 No port forwards currently running. Use '$($MyInvocation.MyCommand.Name) start' to begin." "Yellow"
    }
    Write-Host ""
}

# Function to start essential services only
function StartEssential {
    Write-Header
    Write-ColorOutput "🚀 Starting essential port forwards..." "Blue"
    Write-Host ""
    
    # Filter and sort essential services (priority 1-2)
    $essentialServices = $SERVICES | Where-Object { $_.Priority -le 2 } | Sort-Object Priority
    
    foreach ($service in $essentialServices) {
        StartPortForward -ServiceName $service.Name -LocalPort $service.LocalPort -ServicePort $service.ServicePort -Description $service.Description
        Write-Host ""
    }
    
    Write-ColorOutput "✅ Essential services started!" "Green"
    Write-ColorOutput "   Main UI: http://localhost:3080" "Cyan"
    Write-ColorOutput "   FHIR Proxy: http://localhost:8003" "Cyan"
}

# Function to start all services
function StartAll {
    Write-Header
    Write-ColorOutput "🚀 Starting all port forwards..." "Blue"
    Write-Host ""
    
    # Sort services by priority
    $sortedServices = $SERVICES | Sort-Object Priority
    
    foreach ($service in $sortedServices) {
        StartPortForward -ServiceName $service.Name -LocalPort $service.LocalPort -ServicePort $service.ServicePort -Description $service.Description
        Write-Host ""
    }
    
    Write-ColorOutput "✅ All services started!" "Green"
}

# Function to stop all port forwards
function StopAll {
    Write-Header
    Write-ColorOutput "🛑 Stopping all port forwards..." "Blue"
    Write-Host ""
    
    foreach ($service in $SERVICES) {
        StopPortForward -ServiceName $service.Name
    }
    
    # Clean up any remaining kubectl jobs
    Get-Job | Where-Object { $_.Command -like "*kubectl*port-forward*" } | Stop-Job -PassThru | Remove-Job
    
    # Clean up PID directory
    if (Test-Path $PID_DIR) {
        Remove-Item $PID_DIR -Recurse -Force
        New-Item -ItemType Directory -Path $PID_DIR -Force | Out-Null
    }
    
    Write-ColorOutput "✅ All port forwards stopped!" "Green"
    Write-Host ""
}

# Function to restart all port forwards
function RestartAll {
    Write-ColorOutput "🔄 Restarting all port forwards..." "Blue"
    StopAll
    Start-Sleep 2
    StartAll
}

# Function to show help
function ShowHelp {
    Write-Header
    Write-ColorOutput "📖 Usage: .\port-forward.ps1 [command]" "Blue"
    Write-Host ""
    Write-ColorOutput "Commands:" "Cyan"
    Write-Host "  start         Start essential services (UI + FHIR Proxy)"
    Write-Host "  start-all     Start all available services"
    Write-Host "  stop          Stop all port forwards"
    Write-Host "  restart       Restart all port forwards"
    Write-Host "  status        Show current status of all port forwards"
    Write-Host "  help          Show this help message"
    Write-Host ""
    Write-ColorOutput "Examples:" "Cyan"
    Write-Host "  .\port-forward.ps1 start      # Start essential services"
    Write-Host "  .\port-forward.ps1 status     # Check what's running"
    Write-Host "  .\port-forward.ps1 stop       # Stop everything"
    Write-Host ""
    Write-ColorOutput "Essential Services:" "Cyan"
    Write-Host "  • Healthcare UI (http://localhost:3080) - Main application"
    Write-Host "  • FHIR Proxy (http://localhost:8003) - CORS handler for FHIR"
    Write-Host ""
    Write-ColorOutput "All Services:" "Cyan"
    foreach ($service in $SERVICES) {
        Write-Host ("  • {0,-25} (http://localhost:{1})" -f $service.Description, $service.LocalPort)
    }
    Write-Host ""
}

# Function to test connectivity
function TestServices {
    Write-Header
    Write-ColorOutput "🧪 Testing service connectivity..." "Blue"
    Write-Host ""
    
    foreach ($service in $SERVICES) {
        $pidFile = Join-Path $PID_DIR "$($service.Name).pid"
        
        if ((Test-Path $pidFile)) {
            $jobId = Get-Content $pidFile
            if ($jobId -and $jobId.Trim() -ne "") {
                try {
                    $job = Get-Job -Id $jobId -ErrorAction Stop
                if ($job.State -eq "Running") {
                    Write-Host ("{0,-25} " -f "$($service.Description):") -NoNewline
                    
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:$($service.LocalPort)" -TimeoutSec 3 -ErrorAction Stop
                        Write-ColorOutput "✅ RESPONDING" "Green"
                    }
                    catch {
                        Write-ColorOutput "⚠️  NO RESPONSE" "Yellow"
                    }
                }
                }
                catch {
                    # Job not found, skip
                }
            }
        }
    }
    Write-Host ""
}

# Main script logic
switch ($Command.ToLower()) {
    "start" {
        Test-KubectlAccess
        StartEssential
    }
    "start-all" {
        Test-KubectlAccess
        StartAll
    }
    "stop" {
        StopAll
    }
    "restart" {
        Test-KubectlAccess
        RestartAll
    }
    "status" {
        ShowStatus
    }
    "test" {
        TestServices
    }
    "help" {
        ShowHelp
    }
    default {
        Write-ColorOutput "❌ Unknown command: $Command" "Red"
        Write-Host ""
        ShowHelp
        exit 1
    }
}
