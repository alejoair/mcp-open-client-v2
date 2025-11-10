# MCP Open Client Storage Systems

This document describes the current storage patterns used in the MCP Open Client for managing servers and conversations.

## Current Storage Patterns

### 1. MCP Servers Storage System (Single File Approach)

**Storage Location**: `~/.mcp-open-client/servers.json`

**File Structure**: Single JSON file containing all server configurations

**Data Organization**:
- Root level object with server UUIDs as keys
- Each server entry contains:
  - `id`: Server UUID identifier
  - `name`: Human-readable server name
  - `description`: Server description
  - `status`: Current server status (configured, running, error, etc.)
  - `type`: Transport type (stdio)
  - `config`: Server execution configuration (command, args, env, working_dir, timeout)
  - `connection`: Connection details (transport, host, port)
  - `metadata`: Version, author, timestamps
  - `health`: Process monitoring data (ping, uptime, errors, process_id)

**Implementation Components**:
- `mcp_open_client/core/provider_manager.py`: Manages server configurations with JSON persistence
- `mcp_open_client/api/endpoints/servers.py`: FastAPI endpoints for server management
- `mcp_open_client/api/models/server.py`: Pydantic models for server data structures

**Key Operations**:
- Load all servers from single JSON file
- Save all servers to single JSON file
- CRUD operations on server configurations
- Server lifecycle management (start, stop, monitor)

### 2. Conversations Storage System (File-per-Conversation Approach)

**Storage Location**: `~/.mcp-open-client/conversations/`

**Directory Creation**: The `conversations/` directory is automatically created when the package is installed or when the configuration system is initialized via `ensure_config_directory()`.

**File Structure**: Individual JSON files, one per conversation

**Data Organization**:
- Directory containing separate `.json` files
- Filename pattern: `{conversation_id}.json`
- Each file contains complete conversation data:
  - `id`: Conversation identifier
  - `title`: Conversation title
  - `description`: Conversation description
  - `created_at`, `updated_at`: Timestamps
  - `system_prompt`: AI system prompt
  - `enabled_tools`: List of enabled MCP tools
  - `context`: Dictionary of context items
  - `messages`: List of conversation messages

**Implementation Components**:
- `mcp_open_client/core/conversation_manager.py`: Manages conversation persistence and operations
- `mcp_open_client/api/endpoints/conversations.py`: FastAPI endpoints for conversation management
- `mcp_open_client/api/models/conversation.py`: Pydantic models for conversation data structures

**Key Operations**:
- Individual file operations per conversation
- Load specific conversation by ID
- List all conversations by scanning directory
- CRUD operations on conversations, messages, context, and tools
- Search functionality across conversations

## Comparison of Approaches

### Single File Approach (MCP Servers)
**Advantages**:
- Simple file management (one file to read/write)
- Easy to implement atomic operations
- Better for systems with many small objects
- Lower file system overhead

**Disadvantages**:
- Loading entire dataset even for single item access
- Potential performance issues with large datasets
- Difficult to scale to many servers
- All data lost if file becomes corrupted

### File-per-Item Approach (Conversations)
**Advantages**:
- Efficient for targeted access (load only needed conversation)
- Better scalability for large datasets
- Individual file corruption affects only one conversation
- Easier to implement backup/restore per conversation
- Better for systems with larger individual items

**Disadvantages**:
- More complex file management (many files to track)
- Higher file system overhead
- Directory scanning required for listing
- Potential filesystem performance impact with many files

## File Locations and Naming

### Configuration Directory Structure
```
~/.mcp-open-client/
├── servers.json              # Single file: all server configurations
├── app_config.json           # Application settings
├── ai_providers.json         # AI provider configurations
├── mcp_servers.json          # MCP server definitions
├── .encryption_key           # Encryption key for sensitive data
└── conversations/            # Directory: individual conversation files
    ├── conv-a1b2c3d4e5f6g7h8.json
    ├── conv-i9j0k1l2m3n4o5p6.json
    └── ...
```

### File Naming Patterns
- **MCP Servers**: Single file `servers.json`
- **Conversations**: `{conversation_id}.json` where `conversation_id` follows pattern `conv-{uuid.hex[:16]}`
- **MCP Server IDs**: UUID format
- **Conversation IDs**: `conv-{16-char-hex}` format

## Storage Pattern Recommendation

The **file-per-conversation approach** used in the conversation system is recommended for:
- Large datasets where only subset is accessed frequently
- Systems where individual items have significant data size
- Applications requiring granular backup/restore capabilities
- Systems where data corruption isolation is important

The **single file approach** is recommended for:
- Small datasets that fit comfortably in memory
- Systems with frequent bulk operations
- Applications where atomic operations are critical
- Simple configuration management use cases

## Implementation Status

- ✅ **MCP Servers**: Implemented using single file approach
- ✅ **Conversations**: Implemented using file-per-conversation approach
- ✅ **API Endpoints**: Both systems have complete REST API coverage
- ✅ **Data Models**: Comprehensive Pydantic models for all data structures
- ✅ **Validation**: Server validation ensures running status before tool operations