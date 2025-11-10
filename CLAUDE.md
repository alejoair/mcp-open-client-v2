# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MCP Open Client v2** is a Python REST API server that manages Model Context Protocol (MCP) servers and provides an OpenAI-compatible chat interface with automatic tool calling integration. It bridges MCP servers with AI providers, enabling tool-augmented AI interactions.

## Essential Commands

### Development Setup
```bash
# Install in editable mode
pip install -e .

# Install with dev dependencies (includes pre-commit)
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### Running the Application
```bash
# Start API server (main entry point)
mcp-open-api serve --port 8001 --host 127.0.0.1

# Or directly with uvicorn
uvicorn mcp_open_client.api.main:app --host 127.0.0.1 --port 8001

# Development with hot reload
uvicorn mcp_open_client.api.main:app --reload --port 8001
```

### Configuration Files
Configuration files are automatically created in `~/.mcp-open-client/` on first use:
- `mcp_servers.json` - MCP server configurations
- `ai_providers.json` - AI provider configurations
- `conversations/` - Directory for conversation storage (JSON files)

**Important**: Existing configuration files are never overwritten during upgrades. The system only creates default configs if they don't exist.

### Code Quality Tools
```bash
# Format code (automatically runs on commit via pre-commit hooks)
black mcp_open_client/
isort mcp_open_client/

# Lint
flake8 mcp_open_client/

# Type check
mypy mcp_open_client/

# Run tests
pytest

# Run single test
pytest tests/test_client.py::test_name
```

### Pre-commit Hooks
Pre-commit hooks automatically run before each commit to format and lint code:
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting (warnings only)
- **File checks**: trailing whitespace, EOF, YAML/JSON/TOML validation

### Common Operations
```bash
# MCP Server management
mcp-open-client servers add --name <name> --command <cmd> --args <arg1> --args <arg2>
mcp-open-client servers list [--format json|table]
mcp-open-client servers start <server-id>
mcp-open-client servers stop <server-id>
mcp-open-client servers tools <server-id>

# AI Provider management
mcp-open-client providers add --name <name> --type openai --base-url <url> --api-key <key>
mcp-open-client providers list
mcp-open-client providers models set <provider-id> small --name "gpt-3.5-turbo"
mcp-open-client providers test <provider-id>
mcp-open-client providers set-default <provider-id>
```

## Architecture Overview

### Layered Architecture
1. **API Layer** (`api/`): FastAPI endpoints (REST interface)
2. **Service Layer** (`core/`): Business logic and managers
3. **Data Layer**: JSON file persistence (`mcp_servers.json`, `ai_providers.json`)

### Core Components

**MCPServerManager** (`core/manager.py`)
- Orchestrates MCP servers using FastMCP integration
- Creates appropriate transports (NPX, Node, Python STDIO)
- Manages client lifecycle alongside processes
- Tool discovery and execution

**ProcessManager** (`core/process.py`)
- Manages server processes via `asyncio.subprocess`
- Status tracking: configured → starting → running → stopping → stopped/error
- Health checking and graceful shutdown
- JSON persistence

**AIProviderManager** (`core/provider_manager.py`)
- Provider CRUD operations and model configuration (small/main)
- Default provider management
- Validation/testing of providers

**ConversationManager** (`core/conversation_manager.py`)
- Conversation persistence and CRUD operations
- Message, context, and enabled tools management
- Open editors tracking for IDE integration
- Search functionality by title, description, and keywords
- JSON file storage in `~/.mcp-open-client/conversations/`

**ChatService** (`core/chat_service.py`)
- OpenAI-compatible chat interface at `/v1/chat/completions`
- Provider/model resolution
- Automatic MCP tool integration
- Function calling support and streaming

### Application Flow

**MCP Server Lifecycle:**
```
Add Config → Start Process → Connect FastMCP Client → Use Tools → Stop & Cleanup
```

**Chat Request Flow:**
```
POST /v1/chat/completions
→ Resolve provider & model
→ Get MCP tools from running servers
→ Convert tools to OpenAI format
→ Make OpenAI API call with tools
→ Return response
```

### Transport Integration

The system auto-detects and uses appropriate FastMCP transports:
- **NpxStdioTransport**: For npm/npx packages
- **NodeStdioTransport**: For Node.js scripts
- **PythonStdioTransport**: For Python modules
- **Fallback**: Generic command string

## Key Design Patterns

1. **Manager Pattern**: MCPServerManager, ProcessManager, AIProviderManager
2. **Dependency Injection**: FastAPI `Depends()` for service injection
3. **Context Managers**: `async with client:` for resource cleanup
4. **Async/Await**: Full async support throughout
5. **Type Safety**: Pydantic v2 models with strict validation

## Configuration Files

- **pyproject.toml**: Project metadata, dependencies, tool configs (black, isort, mypy)
- **mcp_servers.json**: Auto-generated server configurations
- **ai_providers.json**: Auto-generated provider configurations
- **Entry points**: `mcp-client` (CLI), `mcp-api` (API server)

## Important Technical Details

### Python Version Support
- Python 3.8+ (supports 3.8-3.12)
- Uses Pydantic v2 (migrated from v1)

### Key Dependencies
- FastAPI + Uvicorn for REST API
- FastMCP for MCP server integration
- OpenAI SDK for AI provider interface
- Click + Rich for CLI
- aiohttp for async HTTP

### Code Style
- Black formatter (line-length=88)
- isort with "black" profile
- mypy strict type checking enabled
- Flake8 for linting

### Testing
- pytest with pytest-asyncio
- Tests in `tests/` directory

## Environment Variables

- `MCP_API_URL`: Default API URL (default: `http://localhost:8001`)
- `MCP_API_HOST`: API server host (default: `127.0.0.1`)
- `MCP_API_PORT`: API server port (default: `8001`)

## REST API Endpoints

**Server Management:**
- `POST /servers/` - Add server
- `GET /servers/` - List servers
- `POST /servers/{id}/start` - Start server
- `POST /servers/{id}/stop` - Stop server
- `GET /servers/{id}/tools` - Get server tools

**Provider Management:**
- `POST /providers/` - Add provider
- `GET /providers/` - List providers
- `PUT /providers/{id}/models/{type}` - Set model config
- `POST /providers/{id}/test` - Test provider
- `POST /providers/set-default/{id}` - Set default

**Chat:**
- `POST /v1/chat/completions` - OpenAI-compatible chat (with automatic tool integration)

**Conversations:**
- `POST /conversations` - Create conversation
- `GET /conversations` - List all conversations
- `GET /conversations/{id}` - Get conversation by ID
- `PUT /conversations/{id}` - Update conversation
- `DELETE /conversations/{id}` - Delete conversation
- `GET /conversations/search?q={query}` - Search conversations

**Messages:**
- `POST /conversations/{id}/messages` - Add message
- `GET /conversations/{id}/messages` - Get all messages
- `DELETE /conversations/{id}/messages/{msg_id}` - Delete message

**Context:**
- `POST /conversations/{id}/context` - Add context item
- `GET /conversations/{id}/context` - Get all context
- `PUT /conversations/{id}/context/{ctx_id}` - Update context
- `DELETE /conversations/{id}/context/{ctx_id}` - Delete context

**Tools (Conversation-specific):**
- `GET /conversations/{id}/tools` - List enabled tools
- `POST /conversations/{id}/tools` - Enable tool (validates server & tool exist)
- `DELETE /conversations/{id}/tools` - Disable tool
- `GET /conversations/{id}/tools/available` - List available tools from running servers

**Open Editors:**
- `GET /conversations/{id}/editors` - List open editors
- `POST /conversations/{id}/editors` - Add open editor
- `DELETE /conversations/{id}/editors` - Remove open editor

**Registry (MCP Server Discovery):**
- `GET /registry/search?q={query}` - Search MCP servers in registry
- `GET /registry/servers` - List all registry servers
- `GET /registry/servers/{name}` - Get specific server details
- `GET /registry/categories` - Get servers grouped by namespace
- `GET /registry/health` - Check registry health

## Common Development Patterns

### Adding New Endpoints
1. Create Pydantic models in `api/models/`
2. Implement endpoint logic in `api/endpoints/`
3. Register router in `api/main.py`
4. Use `Depends()` for manager injection

### Adding New Manager Functionality
1. Implement in appropriate manager (`core/manager.py`, `core/process.py`, etc.)
2. Update Pydantic models if needed
3. Expose via API endpoint if necessary
4. Add CLI command if user-facing

### Working with MCP Tools
- Tools are auto-discovered from running MCP servers
- Converted to OpenAI function format in ChatService
- Available in chat completions when servers are running

## Troubleshooting

### Server Fails to Start
- Check command and args are correct for the platform (e.g., `npm.cmd` on Windows)
- Verify process has permission to access directories
- Use `--verbose` flag for detailed logging

### Type Errors
- Ensure using Pydantic v2 syntax (`ConfigDict` instead of `Config` class)
- Run `mypy mcp_open_client/` to catch type issues

### Process Cleanup
- API uses lifespan events for graceful shutdown
- Always use `await manager.shutdown_all()` when manually managing
