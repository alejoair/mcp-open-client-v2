"""
Chat endpoint for LLM interactions.
"""

import json
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from openai import OpenAI

from ...models.conversation import ConversationChatRequest, ConversationChatResponse
from . import router
from .dependencies import conversation_manager, provider_manager, server_manager


@router.post("/{conversation_id}/chat", response_model=ConversationChatResponse)
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

    # Prepare messages for LLM
    result = conversation_manager.prepare_chat_messages(
        conversation_id, request.content
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    system_prompt, messages_for_llm, enabled_tools = result

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
                        # Convert to OpenAI function format
                        tools_for_llm.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description or "",
                                    "parameters": tool.input_schema or {},
                                },
                            }
                        )
                        # Map tool name to server ID for later execution
                        tool_server_mapping[tool.name] = enabled_tool.server_id
                        break
            except Exception:
                # Skip tools that fail to load
                continue

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

    # Add user message to conversation history
    messages_for_llm.append({"role": "user", "content": request.content})

    # Build initial request parameters
    request_params = {
        "model": model_name,
        "messages": [{"role": "system", "content": system_prompt}] + messages_for_llm,
    }

    # Add tools if available
    if tools_for_llm:
        request_params["tools"] = tools_for_llm

    try:
        # Tool calling loop - continue until we get a final response
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        assistant_message = None

        while iteration < max_iterations:
            iteration += 1

            # Call the LLM
            response = client.chat.completions.create(**request_params)
            response_message = response.choices[0].message

            # Check if the assistant wants to call tools
            if response_message.tool_calls:
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
                    else:
                        try:
                            # Execute the tool
                            tool_result = await server_manager.call_server_tool(
                                server_id=server_id,
                                tool_name=tool_name,
                                arguments=tool_args,
                            )
                            tool_result = json.dumps(tool_result)
                        except Exception as e:
                            tool_result = json.dumps({"error": str(e)})

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

                # Update request params for next iteration
                request_params["messages"] = [
                    {"role": "system", "content": system_prompt}
                ] + messages_for_llm

            else:
                # Final response without tool calls
                assistant_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
                timestamp = datetime.utcnow().isoformat() + "Z"

                assistant_message = conversation_manager.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_message.content or "",
                    message_id=assistant_msg_id,
                    timestamp=timestamp,
                )

                # Break the loop - we have a final response
                break

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
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM response: {str(e)}",
        )
