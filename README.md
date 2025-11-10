# MCP Open Client

An open client implementation for the Model Context Protocol (MCP) with REST API server management capabilities.

## Features

- 🚀 **FastAPI-based REST API** for MCP server management
- 🔧 **FastMCP integration** with multiple transport support (STDIO, WebSocket, HTTP)
- ⚙️ **Process management** for MCP servers with automatic cleanup
- 🎯 **Click-based CLI** with rich console output
- 📁 **Filesystem support** for configuration and data persistence
- 🛡️ **Type safety** with Pydantic models throughout
- 🔄 **Async/await support** for high-performance operations

## Installation

### Install from source (editable mode)

Clone this repository and install the package in editable mode:

```bash
git clone https://github.com/yourusername/mcp-open-client.git
cd mcp-open-client
pip install -e .
```

### Install development dependencies

For development, install the optional development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Start the API Server

```bash
# Start the MCP Open Client API server
mcp-client api serve --port 8001
```

### 2. Add an MCP Server

```bash
# Add a filesystem MCP server
mcp-client api add --name filesystem \
    --command npm.cmd \
    --args -x --args -y --args @modelcontextprotocol/server-filesystem --args .
```

### 3. Start the MCP Server

```bash
# Start the configured server
mcp-client api start <server-id>
```

### 4. List Available Tools

```bash
# List tools from the running server
mcp-client api tools <server-id>
```

## Usage

### REST API

The MCP Open Client provides a REST API for managing MCP servers:

#### Server Management Endpoints

```bash
# Add a new server configuration
POST /servers/
{
  "server": {
    "name": "filesystem",
    "command": "npm.cmd",
    "args": ["-x", "-y", "@modelcontextprotocol/server-filesystem", "."]
  }
}

# List all servers
GET /servers/

# Start a server
POST /servers/{server_id}/start

# Stop a server
POST /servers/{server_id}/stop

# Get server tools
GET /servers/{server_id}/tools
```

#### Example with curl

```bash
# Add server
curl -X POST "http://localhost:8001/servers/" \
  -H "Content-Type: application/json" \
  -d '{"server": {"name": "filesystem", "command": "npm.cmd", "args": ["-x", "-y", "@modelcontextprotocol/server-filesystem", "."]}}'

# Start server
curl -X POST "http://localhost:8001/servers/{server-id}/start"

# Get tools
curl -X GET "http://localhost:8001/servers/{server-id}/tools"
```

### Command-line Interface

#### API Management Commands

```bash
# Show API help
mcp-client api --help

# Start the API server
mcp-client api serve --port 8001 --host 127.0.0.1

# Add a new server
mcp-client api add --name my-server --command npm.cmd --args -x --args -y --args @modelcontextprotocol/server-name

# List all servers (table format)
mcp-client api list

# List servers in JSON format
mcp-client api list --format json

# Start a server
mcp-client api start <server-id>

# Stop a server
mcp-client api stop <server-id>

# Get tools from a server
mcp-client api tools <server-id>

# Get tools in JSON format
mcp-client api tools <server-id> --format json
```

#### Direct MCP Client Commands

```bash
# Connect to a server and test connection
mcp-client --verbose connect http://localhost:8080

# List available resources
mcp-client --timeout 60.0 list-resources http://localhost:8080

# List available tools
mcp-client list-tools http://localhost:8080

# Call a custom method
mcp-client call http://localhost:8080 custom/method -p '{"param": "value"}'
```

### As a Python Library

```python
import asyncio
from mcp_open_client import MCPClient

async def main():
    # Create a client instance
    client = MCPClient("http://localhost:8080")
    
    # Use the client as a context manager
    async with client:
        # Initialize the session
        await client.initialize()
        
        # List available resources
        resources = await client.list_resources()
        print("Resources:", resources)
        
        # List available tools
        tools = await client.list_tools()
        print("Tools:", tools)

# Run the async main function
asyncio.run(main())
```

### Server Management API

```python
import asyncio
from mcp_open_client.core.manager import MCPServerManager
from mcp_open_client.api.models.server import ServerConfig

async def main():
    # Create server manager
    manager = MCPServerManager()
    
    # Add a server configuration
    config = ServerConfig(
        name="filesystem",
        command="npm.cmd",
        args=["-x", "-y", "@modelcontextprotocol/server-filesystem", "."]
    )
    
    server = await manager.add_server_from_config(config)
    print(f"Added server: {server.id}")
    
    # Start the server
    started_server = await manager.start_server(server.id)
    print(f"Server status: {started_server.status}")
    
    # Get tools
    tools = await manager.get_server_tools(server.id)
    print(f"Available tools: {len(tools)}")
    
    # Shutdown all servers
    await manager.shutdown_all()

asyncio.run(main())
```

## Supported MCP Servers

The client works with any MCP-compliant server. Here are some examples:

### Filesystem Server

```bash
mcp-client api add --name filesystem \
    --command npm.cmd \
    --args -x --args -y --args @modelcontextprotocol/server-filesystem --args /path/to/directory
```

### Other Popular MCP Servers

```bash
# Sequential thinking server
mcp-client api add --name thinking \
    --command npm.cmd \
    --args -x --args -y --args @modelcontextprotocol/server-sequential-thinking

# Custom Python server
mcp-client api add --name my-python-server \
    --command python \
    --args -m --args my_mcp_server
```

## Project Structure

```
mcp-open-client/
├── pyproject.toml              # Project configuration
├── README.md                   # This file
├── servers.json               # Server configurations (auto-generated)
└── mcp_open_client/           # Main package directory
    ├── __init__.py            # Package initialization
    ├── client.py              # Core MCP client
    ├── exceptions.py          # Custom exceptions
    ├── cli.py                 # Command-line interface
    ├── api/                   # FastAPI REST API
    │   ├── __init__.py
    │   ├── main.py           # FastAPI application
    │   ├── cli.py            # API CLI entry point
    │   ├── models/           # Pydantic models
    │   │   ├── __init__.py
    │   │   └── server.py     # Server configuration models
    │   └── endpoints/        # API endpoints
    │       ├── __init__.py
    │       └── servers.py    # Server management endpoints
    └── core/                 # Core business logic
        ├── __init__.py
        ├── manager.py        # MCP server manager
        └── process.py        # Process management
```

## Development

### Code formatting

This project uses several tools for code quality:

- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run these tools with:

```bash
# Format code
black mcp_open_client/

# Sort imports
isort mcp_open_client/

# Run linting
flake8 mcp_open_client/

# Run type checking
mypy mcp_open_client/
```

### Running tests

```bash
pytest
```

## Configuration

### Environment Variables

- `MCP_API_URL`: Default API URL (default: `http://localhost:8001`)
- `MCP_API_HOST`: API server host (default: `127.0.0.1`)
- `MCP_API_PORT`: API server port (default: `8001`)

### Server Configuration

Server configurations are stored in `servers.json` in the current working directory. The format is:

```json
{
  "servers": [
    {
      "id": "unique-server-id",
      "config": {
        "name": "server-name",
        "transport": "stdio",
        "command": "npm.cmd",
        "args": ["-x", "-y", "@modelcontextprotocol/server-name"],
        "env": {"KEY": "VALUE"},
        "cwd": "/working/directory"
      },
      "status": "running",
      "created_at": "2025-01-01T00:00:00.000000",
      "started_at": "2025-01-01T00:01:00.000000"
    }
  ]
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### Common Issues

1. **Server fails to start**: Check that the command and arguments are correct for your system
2. **Connection refused**: Ensure the API server is running on the specified port
3. **Permission denied**: Make sure the server process has permission to access required directories

### Debug Mode

Enable verbose output to troubleshoot issues:

```bash
mcp-client --verbose api list
mcp-client --verbose api start <server-id>
```

### Logs

The API server logs MCP server activity and errors to the console. Use `--verbose` flag for detailed logging.