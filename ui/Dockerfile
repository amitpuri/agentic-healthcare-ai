# Multi-stage build for React app
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Define build-time arguments
ARG REACT_APP_AGENT_BACKEND_URL
ARG REACT_APP_FHIR_PROXY_URL
ARG REACT_APP_FHIR_MCP_URL
ARG REACT_APP_ENVIRONMENT
ARG REACT_APP_OPENAI_API_KEY

# Set environment variables from build-time arguments
ENV REACT_APP_AGENT_BACKEND_URL=$REACT_APP_AGENT_BACKEND_URL
ENV REACT_APP_FHIR_PROXY_URL=$REACT_APP_FHIR_PROXY_URL
ENV REACT_APP_FHIR_MCP_URL=$REACT_APP_FHIR_MCP_URL
ENV REACT_APP_ENVIRONMENT=$REACT_APP_ENVIRONMENT
ENV REACT_APP_OPENAI_API_KEY=$REACT_APP_OPENAI_API_KEY

# Copy package files
COPY ui/package.json ./

# Install all dependencies including devDependencies for build
RUN npm install --silent

# Copy source code
COPY ui/ .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY ui/nginx.conf /etc/nginx/conf.d/default.conf

# Install wget for health checks and set up nginx directories
RUN apk add --no-cache wget && \
    mkdir -p /var/cache/nginx/client_temp

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 