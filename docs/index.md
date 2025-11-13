---
layout: default
title: Home
---

# MCP Open Client Documentation

Welcome to the MCP Open Client documentation. This site contains technical documentation and implementation guides.

## Quick Links

[![PyPI version](https://badge.fury.io/py/mcp-open-client.svg)](https://badge.fury.io/py/mcp-open-client)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install mcp-open-client
```

## Quick Start

```bash
# Start the API server
mcp-open-client api serve --port 8001

# Add an MCP server
mcp-open-client api add \
  --name "filesystem" \
  --command "npx" \
  --args "-y" \
  --args "@modelcontextprotocol/server-filesystem"

# Start the server
mcp-open-client api start <server-id>
```

## Documentation

### Architecture & Design

- [FastMCP Client Architecture](fastmcp-client-architecture) - Details about the FastMCP integration
- [UI Architecture](UI_ARCHITECTURE) - Frontend architecture overview
- [Storage Systems](storage-systems) - Data persistence and storage design

### Implementation Guides

- [Frontend Implementation Plan](frontend-implementation-plan) - Complete frontend development guide
- [Tool Calling System](tool-calling-system) - MCP tool calling implementation

## API Reference

The API server provides a REST API for managing MCP servers and AI providers.

**Base URL**: `http://localhost:8001`

**Interactive Documentation**:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Resources

- [GitHub Repository](https://github.com/alejoair/mcp-open-client-v2)
- [PyPI Package](https://pypi.org/project/mcp-open-client/)
- [Report Issues](https://github.com/alejoair/mcp-open-client-v2/issues)

## Features

- **FastAPI REST API** - Full-featured API server for managing MCP servers
- **Rich CLI** - Beautiful command-line interface with colored output
- **AI Provider Integration** - Support for OpenAI, Anthropic, and custom providers
- **Process Management** - Automatic lifecycle management for MCP servers
- **Tool Discovery** - Automatic detection and execution of MCP server tools
- **Conversation Management** - Persistent conversation storage and retrieval
- **Type Safe** - Full type hints with Pydantic v2

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
