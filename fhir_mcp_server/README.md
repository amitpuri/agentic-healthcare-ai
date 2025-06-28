# FHIR MCP Server

A Model Context Protocol (MCP) server that provides secure, standardized access to FHIR (Fast Healthcare Interoperability Resources) servers. This server acts as a bridge between MCP clients and FHIR APIs, offering a simplified and secure way to access healthcare data.

## Features

- **MCP Protocol Support**: Full Model Context Protocol implementation
- **FHIR R4 Compatibility**: Works with any FHIR R4-compliant server
- **Simplified Configuration**: Easy setup with environment variables
- **Docker Ready**: Containerized for easy deployment
- **Health Monitoring**: Built-in health check endpoints
- **Security**: Optional OAuth/Bearer token authentication
- **Two Server Modes**: Simple server for development, full server for production

## Supported FHIR Operations

The server provides the following MCP tools for FHIR operations:

- `get_capabilities` - Get FHIR server capabilities for a resource type
- `search` - Search for FHIR resources with parameters
- `read` - Read a specific FHIR resource by ID
- `create` - Create a new FHIR resource
- `update` - Update an existing FHIR resource
- `delete` - Delete a FHIR resource

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project root
2. Copy the environment template:
   ```bash
   cp env.template .env
   ```
3. Edit `.env` with your FHIR server configuration
4. Start the server:
   ```bash
   docker-compose up fhir-mcp-server
   ```

### Manual Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export FHIR_MCP_FHIR__BASE_URL="https://hapi.fhir.org/baseR4"
   export FHIR_MCP_HOST="localhost"
   export FHIR_MCP_PORT="8004"
   ```

3. Run the server:
   ```bash
   python -m fhir_mcp_server
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FHIR_MCP_HOST` | Server host address | `localhost` |
| `FHIR_MCP_PORT` | Server port | `8004` |
| `FHIR_MCP_FHIR__BASE_URL` | FHIR server base URL | `https://hapi.fhir.org/baseR4` |
| `FHIR_MCP_FHIR__ACCESS_TOKEN` | Bearer token for FHIR server | (empty) |
| `FHIR_MCP_FHIR__TIMEOUT` | Request timeout in seconds | `30` |
| `FHIR_MCP_USE_SIMPLE` | Use simplified server | `true` |

### Server Modes

#### Simple Server (Default)
- Lightweight implementation
- Basic FHIR operations
- Minimal dependencies
- Best for development and testing

#### Full Server
- Complete OAuth2/OIDC support
- Advanced authentication flows
- Production-ready features
- Set `FHIR_MCP_USE_SIMPLE=false` to enable

## Usage Examples

### Using with Healthcare AI UI

The FHIR MCP server integrates seamlessly with the Healthcare AI UI:

1. Enable MCP mode in UI Settings
2. Set MCP server URL to `http://localhost:8004`
3. Configure your FHIR server URL
4. Test the connection

### Direct MCP Protocol Usage

```javascript
// Example MCP request to search for patients
const request = {
  jsonrpc: "2.0",
  id: 1,
  method: "tools/call",
  params: {
    name: "search",
    arguments: {
      type: "Patient",
      searchParam: {
        name: "John"
      }
    }
  }
};

fetch('http://localhost:8004/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(request)
});
```

## API Endpoints

- `POST /mcp` - MCP protocol endpoint
- `GET /health` - Health check endpoint
- `GET /oauth/callback` - OAuth callback (full server only)
- `GET /fhir/callback` - FHIR OAuth callback (full server only)

## Health Check

The server provides a health check endpoint at `/health`:

```bash
curl http://localhost:8004/health
```

Response:
```json
{
  "status": "healthy",
  "service": "FHIR MCP Server",
  "version": "1.0.0",
  "fhir_url": "https://hapi.fhir.org/baseR4"
}
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Code Structure

```
fhir_mcp_server/
├── Dockerfile              # Docker configuration for the service
├── README.md               # This README file
├── __init__.py             # Package initialization
├── __main__.py             # Main entry point for the service
├── fhir_mcp_service.py     # Main FHIR MCP service implementing business logic and tool definitions
└── requirements.txt        # Python dependencies
```

## Security Considerations

- Always use HTTPS in production
- Configure proper FHIR server authentication
- Validate all input parameters
- Monitor access logs
- Keep dependencies updated

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the server is running
   - Verify host and port configuration
   - Ensure firewall allows connections

2. **FHIR Authentication Errors**
   - Verify FHIR server URL is correct
   - Check access token if using authentication
   - Ensure FHIR server is accessible

3. **MCP Protocol Errors**
   - Verify JSON-RPC 2.0 format
   - Check method and parameter names
   - Review server logs for details

### Logs

Enable debug logging for troubleshooting:

```bash
python -m fhir_mcp_server --log-level DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Review the troubleshooting guide

## Related Projects

- [Healthcare AI Agents](../README.md) - Main healthcare AI platform
- [FHIR Proxy](../fhir_proxy/) - Alternative FHIR access method
- [MCP Specification](https://modelcontextprotocol.io/) - Official MCP documentation

## New File Structure

```
fhir_mcp_server/
├── Dockerfile              # Docker configuration for the service
├── README.md               # This README file
├── __init__.py             # Package initialization
├── __main__.py             # Main entry point for the service
├── fhir_mcp_service.py     # Main FHIR MCP service implementing business logic and tool definitions
└── requirements.txt        # Python dependencies
```