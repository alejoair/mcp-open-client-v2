"""
Tool execution utilities for chat endpoint.
"""

import json
from datetime import datetime
from typing import Any, Dict, Tuple

from ..sse import get_local_sse_service


def filter_context_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove context arguments before calling the actual MCP server.

    The MCP server doesn't expect these arguments - they're only for the LLM.
    """
    filtered = arguments.copy()
    filtered.pop("tool_usage_reason", None)
    filtered.pop("error_handling_plan", None)
    return filtered


def inject_required_context_arguments(input_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject two additional required arguments to a tool's input schema.

    These arguments force the LLM to explain:
    1. Why it's using the tool
    2. What to do in case of error
    """
    modified_schema = (
        input_schema.copy() if input_schema else {"type": "object", "properties": {}}
    )

    if "properties" not in modified_schema:
        modified_schema["properties"] = {}

    modified_schema["properties"]["tool_usage_reason"] = {
        "type": "string",
        "description": "¿Para qué estás usando esta herramienta? Explica brevemente el propósito y contexto de uso.",
    }

    modified_schema["properties"]["error_handling_plan"] = {
        "type": "string",
        "description": "¿Qué debes hacer en caso de error? Describe tu plan de contingencia si la herramienta falla.",
    }

    if "required" not in modified_schema:
        modified_schema["required"] = []

    if "tool_usage_reason" not in modified_schema["required"]:
        modified_schema["required"].append("tool_usage_reason")
    if "error_handling_plan" not in modified_schema["required"]:
        modified_schema["required"].append("error_handling_plan")

    return modified_schema


async def prepare_tools_for_llm(enabled_tools, server_manager) -> Tuple[list, dict]:
    """
    Prepare tools from MCP servers for LLM.

    Returns:
        tuple: (tools_for_llm, tool_server_mapping)
    """
    tools_for_llm = []
    tool_server_mapping = {}

    if not enabled_tools:
        return tools_for_llm, tool_server_mapping

    for enabled_tool in enabled_tools:
        server = server_manager.get_server(enabled_tool.server_id)
        if not server or server.status.value != "running":
            continue

        try:
            server_tools = await server_manager.get_server_tools(enabled_tool.server_id)
            for tool in server_tools:
                if tool.name == enabled_tool.tool_name:
                    modified_schema = inject_required_context_arguments(
                        tool.input_schema or {}
                    )
                    tools_for_llm.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description or "",
                                "parameters": modified_schema,
                            },
                        }
                    )
                    tool_server_mapping[tool.name] = enabled_tool.server_id
                    break
        except Exception:
            continue

    return tools_for_llm, tool_server_mapping


def convert_tool_result_to_string(tool_result_raw) -> str:
    """Convert MCP tool result to string format."""
    if isinstance(tool_result_raw, list):
        result_text = ""
        for item in tool_result_raw:
            if hasattr(item, "text"):
                result_text += item.text
            elif isinstance(item, dict) and "text" in item:
                result_text += item["text"]
            else:
                result_text += str(item)
        return result_text
    elif hasattr(tool_result_raw, "content"):
        content = tool_result_raw.content
        if isinstance(content, list):
            result_text = ""
            for item in content:
                if hasattr(item, "text"):
                    result_text += item.text
                elif isinstance(item, dict) and "text" in item:
                    result_text += item["text"]
                else:
                    result_text += str(item)
            return result_text
        else:
            return str(content)
    elif hasattr(tool_result_raw, "text"):
        return tool_result_raw.text
    elif isinstance(tool_result_raw, (str, int, float, bool)):
        return str(tool_result_raw)
    elif isinstance(tool_result_raw, dict):
        return json.dumps(tool_result_raw)
    else:
        return str(tool_result_raw)


async def execute_single_tool_call(
    tool_call, tool_server_mapping, server_manager, conversation_id
) -> str:
    """
    Execute a single tool call and emit SSE events.

    Returns:
        str: Tool result as string
    """
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    timestamp = datetime.utcnow().isoformat() + "Z"

    print(f"[DEBUG] Executing tool call: {tool_name} (id: {tool_call.id})")

    # Emit tool call event
    try:
        sse_service = get_local_sse_service()
        await sse_service.emit_tool_call(
            conversation_id,
            {
                "tool_call_id": tool_call.id,
                "tool_name": tool_name,
                "arguments": tool_args,
                "assistant_content": "",
                "timestamp": timestamp,
            },
        )
    except Exception as sse_error:
        print(f"[DEBUG] SSE emit_tool_call failed (non-critical): {sse_error}")

    # Find which server has this tool
    server_id = tool_server_mapping.get(tool_name)
    if not server_id:
        error_msg = f"Tool '{tool_name}' not found"
        print(f"[DEBUG] {error_msg}")

        # Emit error event
        try:
            sse_service = get_local_sse_service()
            await sse_service.emit_tool_error(
                conversation_id,
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "error": error_msg,
                    "timestamp": timestamp,
                },
            )
        except Exception as sse_error:
            print(f"[DEBUG] SSE emit_tool_error failed (non-critical): {sse_error}")

        return json.dumps({"error": error_msg})

    # Execute the tool
    try:
        filtered_args = filter_context_arguments(tool_args)
        print(
            f"[DEBUG] Calling tool '{tool_name}' on server '{server_id}' with args: {filtered_args}"
        )

        tool_result_raw = await server_manager.call_server_tool(
            server_id=server_id,
            tool_name=tool_name,
            arguments=filtered_args,
        )

        tool_result = convert_tool_result_to_string(tool_result_raw)
        print(
            f"[DEBUG] Tool '{tool_name}' returned result (length={len(str(tool_result))})"
        )

        # Emit tool response event
        try:
            sse_service = get_local_sse_service()
            await sse_service.emit_tool_response(
                conversation_id,
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "result": tool_result,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
            )
        except Exception as sse_error:
            print(f"[DEBUG] SSE emit_tool_response failed (non-critical): {sse_error}")

        return tool_result

    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] Tool '{tool_name}' failed with error: {error_msg}")

        # Emit error event
        try:
            sse_service = get_local_sse_service()
            await sse_service.emit_tool_error(
                conversation_id,
                {
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_name,
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
            )
        except Exception as sse_error:
            print(f"[DEBUG] SSE emit_tool_error failed (non-critical): {sse_error}")

        return json.dumps({"error": error_msg})
