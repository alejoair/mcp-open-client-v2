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
from .token_management import apply_rolling_window, emit_token_update
from .tool_execution import execute_single_tool_call, prepare_tools_for_llm


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
    tools_for_llm, tool_server_mapping = await prepare_tools_for_llm(
        enabled_tools, server_manager
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

            # Apply token counting and rolling window BEFORE each LLM call
            print(
                f"[DEBUG] Applying token counting and rolling window for iteration {iteration}"
            )
            messages_for_llm, token_count, messages_in_context = apply_rolling_window(
                conversation_id, messages_for_llm, model_name
            )

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

                # Execute each tool call using the extracted helper function
                for tool_call in response_message.tool_calls:
                    # Execute tool and get result (handles SSE events internally)
                    tool_result = await execute_single_tool_call(
                        tool_call, tool_server_mapping, server_manager, conversation_id
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
                        name=tool_call.function.name,
                    )

                    # Add tool response to conversation history
                    messages_for_llm.append(
                        {
                            "role": "tool",
                            "content": tool_result,
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
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

                # Emit token update after tool execution
                await emit_token_update(
                    conversation_id, messages_for_llm, model_name, iteration
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
