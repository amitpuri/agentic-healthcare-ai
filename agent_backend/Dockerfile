FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY agent_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules first
COPY ./shared ./shared

# Copy application code
COPY agent_backend/. .

# Set Python path
ENV PYTHONPATH=/app:/app/shared

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/api/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 