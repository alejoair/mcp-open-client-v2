"""
FastAPI endpoints for MCP server management.
"""

from typing import List

from fastapi import APIRouter, HTTPException, status

from ...core.manager import MCPServerManager
from ...exceptions import MCPError
from ..models.server import (
    ErrorResponse,
    ServerCreateRequest,
    ServerCreateResponse,
    ServerListResponse,
    ServerStartResponse,
    ServerStopResponse,
    ServerToolsResponse,
    ToolCallRequest,
    ToolCallResponse,
)

# Global server manager instance
_server_manager = MCPServerManager()

router = APIRouter(prefix="/servers", tags=["MCP Servers"])


@router.post(
    "/",
    response_model=ServerCreateResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="mcp_create_server",
)
async def create_server(request: ServerCreateRequest):
    """
    Create a new MCP server configuration.

    This endpoint adds a new server configuration that can later be started.
    The server remains in 'configured' state until explicitly started.
    """
    try:
        server = await _server_manager.add_server_from_config(request.server)

        return ServerCreateResponse(
            success=True,
            server=server,
            message=f"Server '{server.config.name}' created successfully with ID: {server.id}",
        )

    except MCPError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/", response_model=ServerListResponse, operation_id="mcp_list_servers")
async def list_servers():
    """
    List all configured MCP servers.

    Returns information about all servers, including their current status
    (configured, running, stopped, error, etc.).
    """
    try:
        servers = _server_manager.get_all_servers()

        return ServerListResponse(success=True, servers=servers, count=len(servers))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/{server_id}/start",
    response_model=ServerStartResponse,
    operation_id="mcp_start_server",
)
async def start_server(server_id: str):
    """
    Start an MCP server process.

    This launches the server process using STDIO transport and establishes
    a FastMCP client connection. The server will be available for tool calls.
    """
    try:
        server = await _server_manager.start_server(server_id)

        return ServerStartResponse(
            success=True,
            server=server,
            message=f"Server '{server.config.name}' started successfully",
        )

    except MCPError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/{server_id}/stop",
    response_model=ServerStopResponse,
    operation_id="mcp_stop_server",
)
async def stop_server(server_id: str):
    """
    Stop a running MCP server process.

    This gracefully terminates the server process and cleans up the
    FastMCP client connection. The server configuration remains available
    for future restarts.
    """
    try:
        server = await _server_manager.stop_server(server_id)

        return ServerStopResponse(
            success=True,
            server=server,
            message=f"Server '{server.config.name}' stopped successfully",
        )

    except MCPError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/{server_id}/tools",
    response_model=ServerToolsResponse,
    operation_id="mcp_get_server_tools",
)
async def get_server_tools(server_id: str):
    """
    Get tools available from a running MCP server.

    Returns the list of tools that the server exposes, including their
    names, descriptions, and input schemas.
    """
    try:
        server = _server_manager.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID '{server_id}' not found",
            )

        tools = await _server_manager.get_server_tools(server_id)

        return ServerToolsResponse(
            success=True,
            server_name=server.config.name,
            status=server.status,
            tools=tools,
            message=f"Retrieved {len(tools)} tools from server '{server.config.name}'",
        )

    except MCPError as e:
        # Check if it's a "not running" error and return appropriate status
        error_msg = str(e)
        if "not running" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/{server_id}/tools/call",
    response_model=ToolCallResponse,
    operation_id="mcp_call_server_tool",
)
async def call_tool(server_id: str, request: ToolCallRequest):
    """
    Execute a tool on a running MCP server.

    Calls a specific tool with the provided arguments and returns the result.
    The server must be in 'running' state for this operation to succeed.
    """
    try:
        server = _server_manager.get_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID '{server_id}' not found",
            )

        # Call the tool
        result = await _server_manager.call_server_tool(
            server_id=server_id,
            tool_name=request.tool_name,
            arguments=request.arguments,
        )

        return ToolCallResponse(
            success=True,
            server_id=server_id,
            server_name=server.config.name,
            tool_name=request.tool_name,
            result=result,
            message=f"Tool '{request.tool_name}' executed successfully on server '{server.config.name}'",
        )

    except MCPError as e:
        # Check if it's a "not running" error and return appropriate status
        error_msg = str(e)
        if "not running" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete("/{server_id}", response_model=dict, operation_id="mcp_delete_server")
async def remove_server(server_id: str):
    """
    Remove a server configuration.

    Permanently removes a server configuration. The server must be stopped
    before it can be removed.
    """
    try:
        success = await _server_manager.remove_server(server_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID '{server_id}' not found",
            )

        return {
            "success": True,
            "message": f"Server with ID '{server_id}' removed successfully",
        }

    except MCPError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{server_id}", response_model=dict, operation_id="mcp_get_server_details")
async def get_server(server_id: str):
    """
    Get detailed information about a specific server.

    Returns the complete configuration and current status of a server.
    """
    try:
        server = _server_manager.get_server(server_id)

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID '{server_id}' not found",
            )

        return {"success": True, "server": server.model_dump()}

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


def get_server_manager() -> MCPServerManager:
    """
    Get the global server manager instance.

    This is used by the main FastAPI app to access the server manager
    for shutdown operations.
    """
    return _server_manager
