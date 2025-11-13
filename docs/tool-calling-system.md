---
layout: default
title: Tool Calling System
---

# Tool Calling System

## Overview
Automatic MCP tool execution system integrated with LLM chat conversations. The system handles tool discovery, execution, and response loop until the LLM provides a final answer.

## Architecture

### Backend Components

#### 1. Message Model
**File:** `mcp_open_client/api/models/conversation.py`

**Message Fields:**
- `id`: Message identifier
- `role`: "user" | "assistant" | "system" | "tool"
- `content`: Message text (optional when tool_calls present)
- `timestamp`: ISO 8601 timestamp
- `tool_calls`: List of tool calls made by assistant
- `tool_call_id`: Reference to tool call being responded to
- `name`: Tool name (for tool response messages)

#### 2. Message Operations
**File:** `mcp_open_client/core/conversations/message_ops.py`

**Functions:**
- `add()`: Create and save message with optional tool calling fields
- `get_all()`: Retrieve all messages in conversation
- `delete()`: Remove specific message

#### 3. Chat Endpoint
**File:** `mcp_open_client/api/endpoints/conversations/chat_endpoints.py`

**Endpoint:** `POST /conversations/{conversation_id}/chat`

**Request:**
```json
{
  "content": "user message"
}
```

**Response:**
```json
{
  "success": true,
  "user_message": { "id": "...", "role": "user", "content": "..." },
  "assistant_message": { "id": "...", "role": "assistant", "content": "..." },
  "message": "Chat completed successfully"
}
```

**Process Flow:**
1. Load conversation (system prompt, context, history, enabled tools)
2. Get tool definitions from running MCP servers
3. Save user message
4. Call LLM with tools
5. **Tool Calling Loop** (max 10 iterations):
   - If LLM returns `tool_calls`:
     - Save assistant message with tool_calls
     - Execute each tool on its MCP server
     - Save tool response messages
     - Call LLM again with tool results
   - If LLM returns final answer:
     - Save assistant message
     - Break loop and return

## Message Types

### User Message
```json
{
  "id": "msg-xxx",
  "role": "user",
  "content": "What files are in /docs?",
  "timestamp": "2025-01-11T19:00:00Z"
}
```

### Assistant with Tool Calls
```json
{
  "id": "msg-yyy",
  "role": "assistant",
  "content": null,
  "timestamp": "2025-01-11T19:00:01Z",
  "tool_calls": [
    {
      "id": "call_123",
      "type": "function",
      "function": {
        "name": "list_directory",
        "arguments": "{\"path\": \"/docs\"}"
      }
    }
  ]
}
```

### Tool Response
```json
{
  "id": "msg-zzz",
  "role": "tool",
  "content": "{\"files\": [\"README.md\", \"API.md\"]}",
  "timestamp": "2025-01-11T19:00:02Z",
  "tool_call_id": "call_123",
  "name": "list_directory"
}
```

### Final Assistant Response
```json
{
  "id": "msg-aaa",
  "role": "assistant",
  "content": "The /docs directory contains: README.md and API.md",
  "timestamp": "2025-01-11T19:00:03Z"
}
```

## Tool Execution

### Server Mapping
**File:** `mcp_open_client/api/endpoints/conversations/chat_endpoints.py:64-101`

- Maps each enabled tool to its MCP server ID
- Validates server is running before including in tools list
- Converts MCP tool schema to OpenAI function format

### Tool Calling
**File:** `mcp_open_client/api/endpoints/conversations/chat_endpoints.py:199-243`

- Parses tool call arguments from JSON
- Executes via `server_manager.call_server_tool()`
- Handles execution errors (returns error as tool response)
- Saves all tool responses as separate messages

## Configuration

### Enabled Tools
Tools must be explicitly enabled per conversation:

**Enable Tool:**
```bash
POST /conversations/{id}/tools
{
  "server_id": "server-uuid",
  "tool_name": "list_directory"
}
```

**Get Available Tools:**
```bash
GET /conversations/{id}/tools/available
```

**Get Enabled Tools:**
```bash
GET /conversations/{id}/tools
```

## Testing

**File:** `test_chat_with_tools.py`

**Test Script:**
- Creates test conversation
- Lists available tools from running servers
- Enables tool if available
- Sends chat message
- Displays user and assistant messages
- Shows all messages including tool calls

**Run:**
```bash
python test_chat_with_tools.py
```

## Limitations

1. **Max Iterations:** 10 tool calling loops to prevent infinite loops
2. **No Streaming:** Responses are returned complete (not token-by-token)
3. **Error Handling:** Tool execution errors returned as JSON to LLM
4. **Parallel Tools:** Tools called sequentially, not in parallel

## Future Enhancements

- [ ] Streaming support with Server-Sent Events
- [ ] Stop generation button (requires streaming)
- [ ] Parallel tool execution
- [ ] Tool call approval/confirmation UI
- [ ] Tool execution timeout configuration
- [ ] Retry failed tool calls
