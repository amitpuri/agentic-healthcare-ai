# Docker Compose Deployment

This directory contains all the necessary files for deploying the Healthcare AI Agent system using Docker Compose, completely isolated from the Kubernetes deployment.

## 🚀 Quick Start

```bash
# Navigate to docker directory
cd docker

# Start all services
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down -v
```

## 📋 Services Included

- **CrewAI Healthcare Agent** (Port 8000)
- **Autogen Healthcare Agent** (Port 8001)
- **React UI Frontend** (Port 3030)
- **PostgreSQL Database** (Port 5432)
- **Redis Cache** (Port 6379)
- **Nginx Load Balancer** (Port 80)
- **Prometheus Monitoring** (Port 9090)
- **Grafana Dashboard** (Port 3000)
- **Elasticsearch** (Port 9200)
- **Kibana** (Port 5601)
- **Logstash** (Port 5044)

## 🌐 Access URLs

After deployment, access the services at:

- **Main UI**: http://localhost:3030
- **CrewAI API**: http://localhost:8000
- **Autogen API**: http://localhost:8001
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

## ⚙️ Configuration

1. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Required Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FHIR_SERVER_URL`: FHIR server endpoint
   - `DATABASE_URL`: PostgreSQL connection string
   - `REDIS_URL`: Redis connection string

## 🔧 Development

### Build Individual Services
```bash
# Build only specific services
docker-compose build crewai-healthcare-agent
docker-compose build autogen-healthcare-agent
docker-compose build healthcare-ui

# Restart specific service
docker-compose restart crewai-healthcare-agent
```

### Debugging
```bash
# View logs for specific service
docker-compose logs -f crewai-healthcare-agent

# Access container shell
docker-compose exec crewai-healthcare-agent bash
```

## 🧹 Cleanup

### Complete cleanup (removes all data)
```bash
docker-compose down -v
docker system prune -f --volumes
```

### Preserve data cleanup
```bash
docker-compose down
```

## 📊 Monitoring & Logs

- **Prometheus**: Metrics collection at http://localhost:9090
- **Grafana**: Dashboards at http://localhost:3000
- **ELK Stack**: Log aggregation via Elasticsearch/Kibana
- **Health Checks**: All services include health checks

## 🔒 Security Notes

- Database passwords are generated automatically
- API keys must be provided via environment variables
- All services run in isolated Docker networks
- Nginx provides SSL termination (certificates in `ssl/` directory)

## 🐛 Troubleshooting

### Common Issues:

1. **Port conflicts**: Check if ports are already in use
2. **Memory issues**: Increase Docker memory allocation
3. **Image build failures**: Check Docker daemon and network connectivity
4. **Database connection**: Ensure PostgreSQL is fully started before apps

### Resource Requirements:
- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **Disk Space**: 10GB free space

## 📁 Directory Structure

```
docker/
├── README.md                    # This file
├── docker-compose.yml          # Main compose file
├── docker-compose.override.yml # Development overrides
├── .env.example                # Environment template
├── .env                        # Your configuration (gitignored)
├── services/                   # Service configurations
│   ├── nginx/                  # Nginx configuration
│   ├── postgres/               # Database configuration
│   └── monitoring/             # Prometheus/Grafana config
├── volumes/                    # Persistent data
└── scripts/                    # Utility scripts
``` 