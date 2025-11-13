# MCP Open Client

[![PyPI version](https://badge.fury.io/py/mcp-open-client.svg)](https://badge.fury.io/py/mcp-open-client)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python client and REST API for the Model Context Protocol (MCP), enabling seamless integration with MCP servers and AI providers.

## Features

- **FastAPI REST API** - Full-featured API server for managing MCP servers
- **Rich CLI** - Beautiful command-line interface with colored output
- **AI Provider Integration** - Support for OpenAI, Anthropic, and custom providers
- **Process Management** - Automatic lifecycle management for MCP servers
- **Tool Discovery** - Automatic detection and execution of MCP server tools
- **Conversation Management** - Persistent conversation storage and retrieval
- **Type Safe** - Full type hints with Pydantic v2

## Installation

### From PyPI (Recommended)

```bash
pip install mcp-open-client
```

### From Source

```bash
git clone https://github.com/alejoair/mcp-open-client-v2.git
cd mcp-open-client-v2
pip install -e .
```

## Quick Start

### 1. Start the API Server

```bash
mcp-open-client api serve --port 8001
```

The API server will be available at:
- **API**: http://localhost:8001
- **Swagger Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### 2. Add an MCP Server

```bash
mcp-open-client api add \
  --name "filesystem" \
  --command "npx" \
  --args "-y" \
  --args "@modelcontextprotocol/server-filesystem" \
  --args "."
```

### 3. Start the Server

```bash
mcp-open-client api start <server-id>
```

### 4. List Available Tools

```bash
mcp-open-client api tools <server-id>
```

## CLI Reference

### Direct Connection Commands

Connect directly to MCP servers without the API:

```bash
# Connect and test
mcp-open-client connect http://localhost:3000

# List resources
mcp-open-client list-resources http://localhost:3000

# List tools
mcp-open-client list-tools http://localhost:3000

# Call custom method
mcp-open-client call http://localhost:3000 method-name --params '{"key": "value"}'
```

### API Server Management

Manage MCP servers through the REST API:

```bash
# Start API server
mcp-open-client api serve --port 8001 --host 127.0.0.1

# Server operations
mcp-open-client api add --name <name> --command <cmd> --args <arg>
mcp-open-client api list [--format json|table]
mcp-open-client api start <server-id>
mcp-open-client api stop <server-id>
mcp-open-client api tools <server-id> [--format json|table]
```

### AI Provider Management

Configure AI providers for chat completions:

```bash
# Add provider
mcp-open-client api providers add \
  --name "OpenAI" \
  --type openai \
  --base-url "https://api.openai.com/v1" \
  --api-key "sk-..."

# List providers
mcp-open-client api providers list

# Show provider details
mcp-open-client api providers show <provider-id>

# Update provider
mcp-open-client api providers update <provider-id> \
  --name "New Name" \
  --api-key "new-key"

# Test connection
mcp-open-client api providers test <provider-id>

# Set as default
mcp-open-client api providers set-default <provider-id>

# Enable/disable
mcp-open-client api providers enable <provider-id>
mcp-open-client api providers disable <provider-id>
```

### Model Configuration

Configure small and main models for providers:

```bash
# Set model
mcp-open-client api providers models set <provider-id> small \
  --name "gpt-3.5-turbo" \
  --max-tokens 4096

# List models
mcp-open-client api providers models list <provider-id>

# Remove model
mcp-open-client api providers models remove <provider-id> small
```

## REST API Endpoints

### Server Management

```
POST   /servers/                    # Add server
GET    /servers/                    # List servers
POST   /servers/{id}/start          # Start server
POST   /servers/{id}/stop           # Stop server
GET    /servers/{id}/tools          # Get server tools
DELETE /servers/{id}                # Remove server
```

### Provider Management

```
POST   /providers/                  # Add provider
GET    /providers/                  # List providers
GET    /providers/{id}              # Get provider
PUT    /providers/{id}              # Update provider
PATCH  /providers/{id}              # Partial update
DELETE /providers/{id}              # Delete provider
POST   /providers/{id}/enable       # Enable provider
POST   /providers/{id}/disable      # Disable provider
POST   /providers/{id}/set-default  # Set as default
POST   /providers/{id}/test         # Test connection
```

### Conversation Management

```
POST   /conversations               # Create conversation
GET    /conversations               # List conversations
GET    /conversations/{id}          # Get conversation
PUT    /conversations/{id}          # Update conversation
DELETE /conversations/{id}          # Delete conversation
POST   /conversations/{id}/chat     # Send message
GET    /conversations/{id}/messages # Get messages
POST   /conversations/{id}/context  # Add context
GET    /conversations/{id}/tools    # Get enabled tools
```

### Chat Completions (OpenAI-Compatible)

```
POST   /v1/chat/completions         # Create chat completion
POST   /v1/chat/stream               # Stream completion
GET    /v1/models                    # List models
```

## Configuration

Configuration files are stored in `~/.mcp-open-client/`:

- `mcp_servers.json` - MCP server configurations
- `ai_providers.json` - AI provider configurations
- `conversations/` - Conversation storage directory

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Code Quality Tools

```bash
# Format code
black mcp_open_client/
isort mcp_open_client/

# Lint
flake8 mcp_open_client/

# Type check
mypy mcp_open_client/

# Run tests
pytest
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           mcp-open-client CLI               │
├─────────────────────────────────────────────┤
│                                             │
│  Direct Commands      API Commands         │
│  ├─ connect          ├─ api serve          │
│  ├─ list-resources   ├─ api add            │
│  ├─ list-tools       ├─ api start          │
│  └─ call             └─ api providers      │
│                                             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────┐
    │   FastAPI REST API      │
    │   (Port 8001)           │
    └─────────────┬───────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌──────────────┐
│ MCP Servers   │   │ AI Providers │
│ (FastMCP)     │   │ (OpenAI API) │
└───────────────┘   └──────────────┘
```

## Chat Completion Example

```python
import requests

response = requests.post("http://localhost:8001/v1/chat/completions", json={
    "model": "gpt-4",
    "messages": [
        {"role": "user", "content": "List files in current directory"}
    ],
    "model_type": "main"
})

print(response.json())
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: https://pypi.org/project/mcp-open-client/
- **GitHub**: https://github.com/alejoair/mcp-open-client-v2
- **Issues**: https://github.com/alejoair/mcp-open-client-v2/issues

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- MCP integration via [FastMCP](https://github.com/jlowin/fastmcp)
- CLI powered by [Click](https://click.palletsprojects.com/)
- Beautiful output with [Rich](https://rich.readthedocs.io/)
