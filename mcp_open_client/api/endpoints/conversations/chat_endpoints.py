"""
Chat endpoint for LLM interactions.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from openai import OpenAI

from ...models.conversation import ConversationChatRequest, ConversationChatResponse

# Import the shared SSE service from the sse module
from ..sse import get_local_sse_service
from . import router
from .dependencies import conversation_manager, provider_manager, server_manager


def inject_required_context_arguments(input_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject two additional required arguments to a tool's input schema.

    These arguments force the LLM to explain:
    1. Why it's using the tool
    2. What to do in case of error

    Args:
        input_schema: Original tool input schema

    Returns:
        Modified schema with additional required arguments
    """
    # Create a copy to avoid modifying the original
    modified_schema = (
        input_schema.copy() if input_schema else {"type": "object", "properties": {}}
    )

    # Ensure properties exists
    if "properties" not in modified_schema:
        modified_schema["properties"] = {}

    # Add the two required context arguments
    modified_schema["properties"]["tool_usage_reason"] = {
        "type": "string",
        "description": "¿Para qué estás usando esta herramienta? Explica brevemente el propósito y contexto de uso.",
    }

    modified_schema["properties"]["error_handling_plan"] = {
        "type": "string",
        "description": "¿Qué debes hacer en caso de error? Describe tu plan de contingencia si la herramienta falla.",
    }

    # Update required fields
    if "required" not in modified_schema:
        modified_schema["required"] = []

    # Add to required if not already present
    if "tool_usage_reason" not in modified_schema["required"]:
        modified_schema["required"].append("tool_usage_reason")
    if "error_handling_plan" not in modified_schema["required"]:
        modified_schema["required"].append("error_handling_plan")

    return modified_schema


def filter_context_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove context arguments before calling the actual MCP server.

    The MCP server doesn't expect these arguments - they're only for the LLM.

    Args:
        arguments: Tool arguments including context arguments

    Returns:
        Filtered arguments without context arguments
    """
    filtered = arguments.copy()
    filtered.pop("tool_usage_reason", None)
    filtered.pop("error_handling_plan", None)
    return filtered


@router.post(
    "/{conversation_id}/chat",
    response_model=ConversationChatResponse,
    operation_id="conversation_chat",
)
async def conversation_chat(conversation_id: str, request: ConversationChatRequest):
    """
    Send a message in a conversation and get LLM response.

    This endpoint:
    1. Loads the conversation
    2. Prepares messages with system prompt, context, and history
    3. Gets enabled tools from MCP servers
    4. Calls the default AI provider
    5. Handles tool calling loop (if LLM requests tools)
    6. Saves all messages (user, assistant, tool responses)
    7. Returns user message and final assistant message

    - **conversation_id**: Conversation identifier
    - **content**: User message content
    """

    # Check if conversation exists
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Check if there's a default provider
    default_provider_info = provider_manager.get_default_provider()
    if not default_provider_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No default AI provider configured. Please set a default provider.",
        )

    # Use the provider info directly (already got from get_default_provider)
    provider_config = default_provider_info

    # Prepare messages for LLM (now with token counting and rolling window)
    result = conversation_manager.prepare_chat_messages(
        conversation_id, request.content
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    system_prompt, messages_for_llm, enabled_tools, token_count, messages_in_context = (
        result
    )

    # Determine which model to use (prefer main model)
    model_name = None
    if provider_config.config.models.main:
        model_name = provider_config.config.models.main.model_name
    elif provider_config.config.models.small:
        model_name = provider_config.config.models.small.model_name

    if not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No model configured for provider '{provider_config.id}'",
        )

    # Get tool definitions from MCP servers and create mapping
    tools_for_llm = []
    tool_server_mapping = {}  # Maps tool_name -> server_id

    if enabled_tools:
        for enabled_tool in enabled_tools:
            # Get the server
            server = server_manager.get_server(enabled_tool.server_id)
            if not server or server.status.value != "running":
                continue

            try:
                # Get all tools from the server
                server_tools = await server_manager.get_server_tools(
                    enabled_tool.server_id
                )
                # Find the specific tool
                for tool in server_tools:
                    if tool.name == enabled_tool.tool_name:
                        # Inject required context arguments into the schema
                        modified_schema = inject_required_context_arguments(
                            tool.input_schema or {}
                        )

                        # Convert to OpenAI function format
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
                        # Map tool name to server ID for later execution
                        tool_server_mapping[tool.name] = enabled_tool.server_id
                        break
            except Exception:
                # Skip tools that fail to load
                continue

    # Get OpenAI client
    client = OpenAI(
        api_key=provider_config.config.api_key, base_url=provider_config.config.base_url
    )

    # Save user message first
    user_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    user_message = conversation_manager.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.content,
        message_id=user_msg_id,
        timestamp=timestamp,
    )

    # NOTE: User message already added to messages_for_llm by prepare_chat_messages
    # Do NOT add it again here

    # Build initial request parameters
    request_params = {
        "model": model_name,
        "messages": [{"role": "system", "content": system_prompt}] + messages_for_llm,
    }

    # Add tools if available
    if tools_for_llm:
        request_params["tools"] = tools_for_llm
        print(f"[DEBUG] Sending {len(tools_for_llm)} tools to LLM:")
        for tool in tools_for_llm:
            print(f"  - {tool['function']['name']}")
        print(f"[DEBUG] Full tools JSON:\n{json.dumps(tools_for_llm, indent=2)}")
    else:
        print("[DEBUG] No tools available for this conversation")
        print(f"[DEBUG] enabled_tools from conversation: {enabled_tools}")

    try:
        # Tool calling loop - continue until we get a final response
        max_iterations = 50  # Prevent infinite loops
        iteration = 0
        assistant_message = None

        while iteration < max_iterations:
            iteration += 1

            # 🔥 FIX: Apply token counting and rolling window BEFORE each LLM call
            print(
                f"[DEBUG] Applying token counting and rolling window for iteration {iteration}"
            )

            # Use the conversation manager's token counter to apply rolling window
            from mcp_open_client.core.conversations.storage import ConversationStorage
            from mcp_open_client.core.conversations.token_counter import TokenCounter

            # Create temporary instances for token counting
            storage = ConversationStorage()
            token_counter = TokenCounter()

            # Load conversation to get current limits
            conversation = storage.load(conversation_id)
            if conversation:
                # Apply rolling window with the current messages_for_llm
                if conversation.max_tokens or conversation.max_messages:
                    messages_for_llm, token_count = token_counter.apply_rolling_window(
                        messages_for_llm,
                        max_tokens=conversation.max_tokens,
                        max_messages=conversation.max_messages,
                        model=model_name,
                    )
                    print(
                        f"[DEBUG] Rolling window applied: {len(messages_for_llm)} messages, {token_count} tokens"
                    )
                else:
                    # Just count tokens without applying window
                    token_count = token_counter.count_message_tokens(
                        messages_for_llm
                        + [{"role": "system", "content": system_prompt}],
                        model_name,
                    )
                    print(f"[DEBUG] Token count: {token_count} tokens")

                messages_in_context = len(messages_for_llm)
            else:
                print(
                    f"[WARNING] Could not load conversation for token counting, using original messages"
                )
                token_count = len(messages_for_llm) * 50  # Rough estimate
                messages_in_context = len(messages_for_llm)

            # Update request_params with the potentially trimmed messages
            request_params["messages"] = [
                {"role": "system", "content": system_prompt}
            ] + messages_for_llm

            # Call the LLM
            response = client.chat.completions.create(**request_params)
            response_message = response.choices[0].message

            # Log iteration without content (may contain emojis that cause encoding errors)
            tool_call_count = (
                len(response_message.tool_calls) if response_message.tool_calls else 0
            )
            print(
                f"[DEBUG] Iteration {iteration}: Got response (content_length={len(response_message.content or '')}) and tool_calls={tool_call_count}"
            )

            # Check if the assistant wants to call tools
            if response_message.tool_calls:
                print(
                    f"[DEBUG] Assistant wants to call {len(response_message.tool_calls)} tools"
                )
                # Save assistant message with tool calls
                assistant_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
                timestamp = datetime.utcnow().isoformat() + "Z"

                # Convert tool calls to dict format for storage
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in response_message.tool_calls
                ]

                assistant_message = conversation_manager.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_message.content,
                    message_id=assistant_msg_id,
                    timestamp=timestamp,
                    tool_calls=tool_calls_data,
                )

                # Add assistant message to conversation history
                messages_for_llm.append(
                    {
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": tool_calls_data,
                    }
                )

                # Emit SSE event for tool calls detected
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    print(
                        f"[DEBUG] Executing tool call: {tool_name} (id: {tool_call.id})"
                    )

                    # Emit tool call event (non-blocking, don't let SSE errors interrupt flow)
                    try:
                        sse_service = get_local_sse_service()
                        await sse_service.emit_tool_call(
                            conversation_id,
                            {
                                "tool_call_id": tool_call.id,
                                "tool_name": tool_name,
                                "arguments": tool_args,
                                "assistant_content": response_message.content,
                                "timestamp": timestamp,
                            },
                        )
                    except Exception as sse_error:
                        print(
                            f"[DEBUG] SSE emit_tool_call failed (non-critical): {sse_error}"
                        )

                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Find which server has this tool
                    server_id = tool_server_mapping.get(tool_name)
                    if not server_id:
                        tool_result = json.dumps(
                            {"error": f"Tool '{tool_name}' not found"}
                        )
                        print(f"[DEBUG] Tool '{tool_name}' not found in mapping")
                        # Emit error event (non-blocking, don't let SSE errors interrupt flow)
                        try:
                            sse_service = get_local_sse_service()
                            await sse_service.emit_tool_error(
                                conversation_id,
                                {
                                    "tool_call_id": tool_call.id,
                                    "tool_name": tool_name,
                                    "error": f"Tool '{tool_name}' not found",
                                    "timestamp": datetime.utcnow().isoformat() + "Z",
                                },
                            )
                        except Exception as sse_error:
                            print(
                                f"[DEBUG] SSE emit_tool_error failed (non-critical): {sse_error}"
                            )
                    else:
                        try:
                            # Filter out context arguments before sending to MCP server
                            filtered_args = filter_context_arguments(tool_args)

                            print(
                                f"[DEBUG] Calling tool '{tool_name}' on server '{server_id}' with args: {filtered_args}"
                            )
                            # Execute the tool with filtered arguments
                            tool_result_raw = await server_manager.call_server_tool(
                                server_id=server_id,
                                tool_name=tool_name,
                                arguments=filtered_args,
                            )

                            # Convert MCP result to serializable format
                            if isinstance(tool_result_raw, list):
                                # Handle list of TextContent objects
                                result_text = ""
                                for item in tool_result_raw:
                                    if hasattr(item, "text"):
                                        result_text += item.text
                                    elif isinstance(item, dict) and "text" in item:
                                        result_text += item["text"]
                                    else:
                                        result_text += str(item)
                                tool_result = result_text
                            elif hasattr(tool_result_raw, "content"):
                                # Handle CallToolResult object with content attribute
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
                                    tool_result = result_text
                                else:
                                    tool_result = str(content)
                            elif hasattr(tool_result_raw, "text"):
                                # Single TextContent object
                                tool_result = tool_result_raw.text
                            elif isinstance(tool_result_raw, (str, int, float, bool)):
                                tool_result = str(tool_result_raw)
                            elif isinstance(tool_result_raw, dict):
                                tool_result = json.dumps(tool_result_raw)
                            else:
                                tool_result = str(tool_result_raw)

                            print(
                                f"[DEBUG] Tool '{tool_name}' returned result (length={len(str(tool_result))})"
                            )

                            # Emit tool response event (non-blocking, don't let SSE errors interrupt flow)
                            try:
                                sse_service = get_local_sse_service()
                                await sse_service.emit_tool_response(
                                    conversation_id,
                                    {
                                        "tool_call_id": tool_call.id,
                                        "tool_name": tool_name,
                                        "result": tool_result,
                                        "timestamp": datetime.utcnow().isoformat()
                                        + "Z",
                                    },
                                )
                            except Exception as sse_error:
                                print(
                                    f"[DEBUG] SSE emit_tool_response failed (non-critical): {sse_error}"
                                )

                        except Exception as e:
                            tool_result = json.dumps({"error": str(e)})
                            print(
                                f"[DEBUG] Tool '{tool_name}' failed with error: {str(e)}"
                            )
                            # Emit error event (non-blocking, don't let SSE errors interrupt flow)
                            try:
                                sse_service = get_local_sse_service()
                                await sse_service.emit_tool_error(
                                    conversation_id,
                                    {
                                        "tool_call_id": tool_call.id,
                                        "tool_name": tool_name,
                                        "error": str(e),
                                        "timestamp": datetime.utcnow().isoformat()
                                        + "Z",
                                    },
                                )
                            except Exception as sse_error:
                                print(
                                    f"[DEBUG] SSE emit_tool_error failed (non-critical): {sse_error}"
                                )

                    # Save tool response message
                    tool_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
                    timestamp = datetime.utcnow().isoformat() + "Z"

                    conversation_manager.add_message(
                        conversation_id=conversation_id,
                        role="tool",
                        content=tool_result,
                        message_id=tool_msg_id,
                        timestamp=timestamp,
                        tool_call_id=tool_call.id,
                        name=tool_name,
                    )

                    # Add tool response to conversation history
                    messages_for_llm.append(
                        {
                            "role": "tool",
                            "content": tool_result,
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                        }
                    )

                # Debug print to see what's happening
                print(
                    f"[DEBUG] After tool execution, messages_for_llm length: {len(messages_for_llm)}"
                )
                for i, msg in enumerate(messages_for_llm):
                    print(
                        f"[DEBUG] Message {i}: {msg['role']} - {msg.get('tool_call_id', 'no tool_id')}"
                    )

                # Update request params for next iteration
                request_params["messages"] = [
                    {"role": "system", "content": system_prompt}
                ] + messages_for_llm

            else:
                # Final response without tool calls
                content = response_message.content or ""
                content_length = len(content.strip()) if content else 0

                print(
                    f"[DEBUG] Response without tool_calls (content_length={content_length})"
                )

                # Only accept as final response if there's actual content
                # Empty responses should not terminate the loop
                if content_length > 0:
                    assistant_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
                    timestamp = datetime.utcnow().isoformat() + "Z"

                    assistant_message = conversation_manager.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=content,
                        message_id=assistant_msg_id,
                        timestamp=timestamp,
                    )

                    # Break the loop - we have a final response with content
                    print(f"[DEBUG] Final assistant response accepted")
                    break
                else:
                    # Empty response - continue loop to get actual content
                    print(
                        f"[DEBUG] WARNING: LLM returned empty response without tool_calls, continuing loop..."
                    )
                    # Add empty message to history to maintain conversation flow
                    messages_for_llm.append({"role": "assistant", "content": ""})

        if not assistant_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get final assistant response after tool calls",
            )

        return ConversationChatResponse(
            success=True,
            user_message=user_message,
            assistant_message=assistant_message,
            message="Chat completed successfully",
            token_count=token_count,
            tokens_sent=token_count,
            messages_in_context=messages_in_context,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM response: {str(e)}",
        )
