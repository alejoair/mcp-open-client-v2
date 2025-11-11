"""
FastAPI endpoints for conversation management.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...core.chat_service import ChatService
from ...core.conversations import get_conversation_manager
from ...core.provider_manager import AIProviderManager
from ..models.conversation import (
    AvailableToolsResponse,
    ContextCreateRequest,
    ContextResponse,
    ContextUpdateRequest,
    ConversationChatRequest,
    ConversationChatResponse,
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    ConversationSearchResponse,
    ConversationUpdateRequest,
    EnabledToolCreateRequest,
    EnabledToolResponse,
    MessageCreateRequest,
    MessageResponse,
    OpenEditorCreateRequest,
    OpenEditorResponse,
)
from .servers import get_server_manager

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Get manager instances
conversation_manager = get_conversation_manager()
server_manager = get_server_manager()
chat_service = ChatService()
provider_manager = AIProviderManager()


@router.post(
    "", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(request: ConversationCreateRequest):
    """
    Create a new conversation.

    - **title**: Conversation title
    - **description**: Optional description
    - **system_prompt**: Optional system prompt
    """
    try:
        conversation = conversation_manager.create_conversation(
            title=request.title,
            description=request.description,
            system_prompt=request.system_prompt,
        )
        return ConversationResponse(
            success=True,
            conversation=conversation,
            message=f"Conversation '{conversation.title}' created successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}",
        )


@router.get("", response_model=ConversationListResponse)
async def list_conversations():
    """
    List all conversations ordered by last update.
    """
    try:
        conversations = conversation_manager.list_conversations()
        return ConversationListResponse(
            success=True, conversations=conversations, count=len(conversations)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}",
        )


@router.get("/search", response_model=ConversationSearchResponse)
async def search_conversations(
    q: str = Query(..., description="Search query for title, description, or keywords")
):
    """
    Search conversations by title, description, or context keywords.

    - **q**: Search query string
    """
    try:
        results = conversation_manager.search_conversations(q)
        return ConversationSearchResponse(
            success=True,
            conversations=results,
            count=len(results),
            message=f"Found {len(results)} conversations matching '{q}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """
    Get a specific conversation by ID.

    - **conversation_id**: Conversation identifier
    """
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationResponse(
        success=True,
        conversation=conversation,
        message=f"Retrieved conversation '{conversation.title}'",
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: str, request: ConversationUpdateRequest):
    """
    Update conversation metadata.

    - **conversation_id**: Conversation identifier
    - **title**: New title (optional)
    - **description**: New description (optional)
    - **system_prompt**: New system prompt (optional)
    """
    conversation = conversation_manager.update_conversation(
        conversation_id=conversation_id,
        title=request.title,
        description=request.description,
        system_prompt=request.system_prompt,
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return ConversationResponse(
        success=True,
        conversation=conversation,
        message=f"Conversation '{conversation.title}' updated successfully",
    )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.

    - **conversation_id**: Conversation identifier
    """
    success = conversation_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "message": f"Conversation '{conversation_id}' deleted"}


# Message endpoints


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(conversation_id: str, request: MessageCreateRequest):
    """
    Add a message to a conversation.

    - **conversation_id**: Conversation identifier
    - **role**: Message role (user, assistant, system)
    - **content**: Message content
    """
    message = conversation_manager.add_message(
        conversation_id=conversation_id, role=request.role, content=request.content
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return MessageResponse(
        success=True, message=message, result_message="Message added successfully"
    )


@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    """
    Get all messages from a conversation.

    - **conversation_id**: Conversation identifier
    """
    messages = conversation_manager.get_messages(conversation_id)
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "messages": messages, "count": len(messages)}


@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(conversation_id: str, message_id: str):
    """
    Delete a specific message from a conversation.

    - **conversation_id**: Conversation identifier
    - **message_id**: Message identifier
    """
    success = conversation_manager.delete_message(conversation_id, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message '{message_id}' not found in conversation '{conversation_id}'",
        )

    return {"success": True, "message": f"Message '{message_id}' deleted"}


# Context endpoints


@router.post("/{conversation_id}/context", response_model=ContextResponse)
async def add_context(conversation_id: str, request: ContextCreateRequest):
    """
    Add a context item to a conversation.

    - **conversation_id**: Conversation identifier
    - **descriptive_name**: Descriptive name for the context
    - **related_keywords**: Related keywords
    - **related_files**: Related file paths
    - **content**: Context content
    """
    result = conversation_manager.add_context(
        conversation_id=conversation_id,
        descriptive_name=request.descriptive_name,
        content=request.content,
        related_keywords=request.related_keywords,
        related_files=request.related_files,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    context_id, context_item = result
    return ContextResponse(
        success=True,
        context_id=context_id,
        context=context_item,
        message="Context added successfully",
    )


@router.get("/{conversation_id}/context")
async def get_context(conversation_id: str):
    """
    Get all context items from a conversation.

    - **conversation_id**: Conversation identifier
    """
    context = conversation_manager.get_context(conversation_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "context": context, "count": len(context)}


@router.put("/{conversation_id}/context/{context_id}", response_model=ContextResponse)
async def update_context(
    conversation_id: str, context_id: str, request: ContextUpdateRequest
):
    """
    Update a context item.

    - **conversation_id**: Conversation identifier
    - **context_id**: Context item identifier
    """
    context_item = conversation_manager.update_context(
        conversation_id=conversation_id,
        context_id=context_id,
        descriptive_name=request.descriptive_name,
        content=request.content,
        related_keywords=request.related_keywords,
        related_files=request.related_files,
    )

    if not context_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context '{context_id}' not found in conversation '{conversation_id}'",
        )

    return ContextResponse(
        success=True,
        context_id=context_id,
        context=context_item,
        message="Context updated successfully",
    )


@router.delete("/{conversation_id}/context/{context_id}")
async def delete_context(conversation_id: str, context_id: str):
    """
    Delete a context item from a conversation.

    - **conversation_id**: Conversation identifier
    - **context_id**: Context item identifier
    """
    success = conversation_manager.delete_context(conversation_id, context_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context '{context_id}' not found in conversation '{conversation_id}'",
        )

    return {"success": True, "message": f"Context '{context_id}' deleted"}


# Tool endpoints


@router.get("/{conversation_id}/tools")
async def get_enabled_tools(conversation_id: str):
    """
    Get all enabled tools for a conversation.

    - **conversation_id**: Conversation identifier
    """
    tools = conversation_manager.get_enabled_tools(conversation_id)
    if tools is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "enabled_tools": tools, "count": len(tools)}


@router.post("/{conversation_id}/tools", response_model=EnabledToolResponse)
async def enable_tool(conversation_id: str, request: EnabledToolCreateRequest):
    """
    Enable a tool for a conversation.

    Validates that:
    1. The server exists
    2. The server is running
    3. The tool exists in that server

    - **conversation_id**: Conversation identifier
    - **server_id**: Server UUID or slug
    - **tool_name**: Name of the tool to enable
    """
    # Check if conversation exists
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Validate server exists
    server = server_manager.get_server(request.server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server '{request.server_id}' not found",
        )

    # Validate server is running
    if server.status.value != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server '{request.server_id}' is not running (status: {server.status.value})",
        )

    # Validate tool exists in server
    try:
        tools = await server_manager.get_server_tools(request.server_id)
        tool_names = [tool.name for tool in tools]
        if request.tool_name not in tool_names:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{request.tool_name}' not found in server '{request.server_id}'. Available tools: {', '.join(tool_names)}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate tool: {str(e)}",
        )

    # Add the tool
    enabled_tools = conversation_manager.add_enabled_tool(
        conversation_id=conversation_id,
        server_id=request.server_id,
        tool_name=request.tool_name,
    )

    return EnabledToolResponse(
        success=True,
        enabled_tools=enabled_tools,
        message=f"Tool '{request.tool_name}' from server '{request.server_id}' enabled successfully",
    )


@router.delete("/{conversation_id}/tools", response_model=EnabledToolResponse)
async def disable_tool(
    conversation_id: str,
    server_id: str = Query(..., description="Server UUID or slug"),
    tool_name: str = Query(..., description="Tool name to disable"),
):
    """
    Disable a tool for a conversation.

    - **conversation_id**: Conversation identifier
    - **server_id**: Server UUID or slug
    - **tool_name**: Name of the tool to disable
    """
    enabled_tools = conversation_manager.remove_enabled_tool(
        conversation_id=conversation_id, server_id=server_id, tool_name=tool_name
    )

    if enabled_tools is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return EnabledToolResponse(
        success=True,
        enabled_tools=enabled_tools,
        message=f"Tool '{tool_name}' from server '{server_id}' disabled",
    )


@router.get("/{conversation_id}/tools/available", response_model=AvailableToolsResponse)
async def get_available_tools(conversation_id: str):
    """
    Get all available tools from running servers.

    - **conversation_id**: Conversation identifier
    """
    # Check if conversation exists
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Get all running servers
    servers = server_manager.get_all_servers()
    available_tools = []

    for server in servers:
        if server.status.value == "running":
            try:
                tools = await server_manager.get_server_tools(server.id)
                for tool in tools:
                    available_tools.append(
                        {
                            "server_id": server.id,
                            "server_slug": server.slug,
                            "server_name": server.config.name,
                            "tool_name": tool.name,
                            "tool_description": tool.description,
                        }
                    )
            except Exception:
                # Skip servers that fail to respond
                continue

    return AvailableToolsResponse(
        success=True, available_tools=available_tools, count=len(available_tools)
    )


# Open editor endpoints


@router.get("/{conversation_id}/editors")
async def get_open_editors(conversation_id: str):
    """
    Get all open editors for a conversation.

    - **conversation_id**: Conversation identifier
    """
    editors = conversation_manager.get_open_editors(conversation_id)
    if editors is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "open_editors": editors, "count": len(editors)}


@router.post("/{conversation_id}/editors", response_model=OpenEditorResponse)
async def add_open_editor(conversation_id: str, request: OpenEditorCreateRequest):
    """
    Add an open editor to a conversation.

    - **conversation_id**: Conversation identifier
    - **file_path**: Path to the open file
    - **language**: Optional programming language
    - **line_number**: Optional current line number
    """
    # Check if conversation exists
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Add the editor
    open_editors = conversation_manager.add_open_editor(
        conversation_id=conversation_id,
        file_path=request.file_path,
        language=request.language,
        line_number=request.line_number,
    )

    return OpenEditorResponse(
        success=True,
        open_editors=open_editors,
        message=f"Editor '{request.file_path}' added successfully",
    )


@router.delete("/{conversation_id}/editors", response_model=OpenEditorResponse)
async def remove_open_editor(
    conversation_id: str,
    file_path: str = Query(..., description="Path to the open file"),
):
    """
    Remove an open editor from a conversation.

    - **conversation_id**: Conversation identifier
    - **file_path**: Path to the open file to remove
    """
    open_editors = conversation_manager.remove_open_editor(
        conversation_id=conversation_id, file_path=file_path
    )

    if open_editors is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return OpenEditorResponse(
        success=True,
        open_editors=open_editors,
        message=f"Editor '{file_path}' removed",
    )


# Chat endpoint


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
