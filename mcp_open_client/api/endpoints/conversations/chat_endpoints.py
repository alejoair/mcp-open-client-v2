"""
Chat endpoint for LLM interactions.
"""

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
    5. Saves both user and assistant messages
    6. Returns both messages

    - **conversation_id**: Conversation identifier
    - **content**: User message content
    """
    import uuid
    from datetime import datetime

    # Check if conversation exists
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Check if there's a default provider
    default_provider = provider_manager.get_default_provider()
    if not default_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No default AI provider configured. Please set a default provider.",
        )

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

    # Get tool definitions from MCP servers
    tools_for_llm = []
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
                        break
            except Exception:
                # Skip tools that fail to load
                continue

    # Get provider config
    provider_config = provider_manager.get_provider(default_provider)
    if not provider_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provider '{default_provider}' configuration not found",
        )

    # Determine which model to use (prefer main model)
    model_name = None
    if provider_config.models.main:
        model_name = provider_config.models.main.name
    elif provider_config.models.small:
        model_name = provider_config.models.small.name

    if not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No model configured for provider '{default_provider}'",
        )

    # Get OpenAI client
    from openai import OpenAI

    client = OpenAI(api_key=provider_config.api_key, base_url=provider_config.base_url)

    # Build request parameters
    request_params = {
        "model": model_name,
        "messages": [{"role": "system", "content": system_prompt}] + messages_for_llm,
    }

    # Add tools if available
    if tools_for_llm:
        request_params["tools"] = tools_for_llm

    try:
        # Call the LLM
        response = client.chat.completions.create(**request_params)

        # Extract assistant response
        assistant_content = response.choices[0].message.content or ""

        # Create message IDs and timestamps
        user_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
        assistant_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Save user message
        user_message = conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.content,
            message_id=user_msg_id,
            timestamp=timestamp,
        )

        # Save assistant message
        assistant_message = conversation_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            message_id=assistant_msg_id,
            timestamp=timestamp,
        )

        return ConversationChatResponse(
            success=True,
            user_message=user_message,
            assistant_message=assistant_message,
            message="Chat completed successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM response: {str(e)}",
        )
