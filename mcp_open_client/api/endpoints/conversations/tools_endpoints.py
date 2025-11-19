"""
Tool endpoints for conversations.
"""

from fastapi import HTTPException, Query, status

from ...models.conversation import (
    AvailableToolsResponse,
    EnabledToolCreateRequest,
    EnabledToolResponse,
)
from . import router
from .dependencies import conversation_manager, server_manager


@router.get("/{conversation_id}/tools", operation_id="conversation_get_enabled_tools")
async def get_enabled_tools(conversation_id: str):
    """
    Get all enabled tools for a conversation.

    - **conversation_id**: Conversation identifier
    """
    tools = conversation_manager.get_tools(conversation_id)
    if tools is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    return {"success": True, "enabled_tools": tools, "count": len(tools)}


@router.post(
    "/{conversation_id}/tools",
    response_model=EnabledToolResponse,
    operation_id="conversation_enable_tool",
)
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
    enabled_tools = conversation_manager.enable_tool(
        conversation_id=conversation_id,
        server_id=request.server_id,
        tool_name=request.tool_name,
    )

    return EnabledToolResponse(
        success=True,
        enabled_tools=enabled_tools,
        message=f"Tool '{request.tool_name}' from server '{request.server_id}' enabled successfully",
    )


@router.delete(
    "/{conversation_id}/tools",
    response_model=EnabledToolResponse,
    operation_id="conversation_disable_tool",
)
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
    enabled_tools = conversation_manager.disable_tool(
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


@router.get(
    "/{conversation_id}/tools/available",
    response_model=AvailableToolsResponse,
    operation_id="conversation_get_available_tools",
)
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
