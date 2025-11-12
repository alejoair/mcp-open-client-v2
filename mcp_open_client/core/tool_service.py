"""
MCP Tool Service - Handles tool discovery and execution for MCP servers.
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from fastmcp import Client

from ..api.models.server import ServerInfo, ServerStatus, ToolInfo
from ..exceptions import MCPError

logger = logging.getLogger(__name__)


class ToolService:
    """Service for MCP tool operations."""

    @staticmethod
    async def get_server_tools(
        server: ServerInfo,
        client: "Client",
    ) -> List[ToolInfo]:
        """
        Get tools available from a running server.

        Args:
            server: Server information
            client: FastMCP client

        Returns:
            List of available tools

        Raises:
            MCPError: If server not running or tool retrieval fails
        """
        if server.status != ServerStatus.RUNNING:
            raise MCPError(
                f"Server '{server.config.name}' is not running (status: {server.status})"
            )

        if not client:
            raise MCPError(
                f"No FastMCP client available for server '{server.config.name}'"
            )

        try:
            logger.info(
                f"Getting tools from server '{server.config.name}' (ID: {server.id})"
            )

            # Use FastMCP client to list tools with timeout
            async with client:
                # Add timeout to prevent hanging
                tools_response = await asyncio.wait_for(
                    client.list_tools(), timeout=10.0  # 10 second timeout
                )

                # Convert FastMCP tools to ToolInfo models
                tool_infos = []
                # Handle different response formats
                tools_list = (
                    tools_response.tools
                    if hasattr(tools_response, "tools")
                    else tools_response
                )
                for tool in tools_list:
                    tool_info = ToolInfo(
                        name=tool.name,
                        description=getattr(tool, "description", None),
                        input_schema=getattr(tool, "inputSchema", None),
                    )
                    tool_infos.append(tool_info)

                logger.info(
                    f"Successfully got {len(tool_infos)} tools from server '{server.config.name}'"
                )
                return tool_infos

        except asyncio.TimeoutError:
            logger.error(f"Timeout getting tools from server '{server.config.name}'")
            raise MCPError(
                f"Timeout getting tools from server '{server.config.name}' (server may be unresponsive)"
            )
        except Exception as e:
            logger.error(
                f"Error getting tools from server '{server.config.name}': {type(e).__name__}: {str(e)}"
            )
            raise MCPError(
                f"Failed to get tools from server '{server.config.name}': {e}"
            )

    @staticmethod
    async def call_server_tool(
        server: ServerInfo,
        client: "Client",
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Call a tool on a running server.

        Args:
            server: Server information
            client: FastMCP client
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPError: If server not running or tool execution fails
        """
        if server.status != ServerStatus.RUNNING:
            raise MCPError(
                f"Server '{server.config.name}' is not running (status: {server.status})"
            )

        if not client:
            raise MCPError(
                f"No FastMCP client available for server '{server.config.name}'"
            )

        try:
            logger.info(
                f"Calling tool '{tool_name}' on server '{server.config.name}' with args: {arguments}"
            )

            # Use FastMCP client to call tool with timeout
            async with client:
                result = await asyncio.wait_for(
                    client.call_tool(tool_name, arguments or {}),
                    timeout=30.0,  # 30 second timeout for tool execution
                )
                logger.info(f"Tool '{tool_name}' completed successfully")
                return result

        except asyncio.TimeoutError:
            logger.error(
                f"Timeout calling tool '{tool_name}' on server '{server.config.name}'"
            )
            raise MCPError(
                f"Timeout calling tool '{tool_name}' on server '{server.config.name}' (tool execution took too long)"
            )
        except Exception as e:
            logger.error(
                f"Error calling tool '{tool_name}' on server '{server.config.name}': {type(e).__name__}: {str(e)}"
            )
            raise MCPError(
                f"Failed to call tool '{tool_name}' on server '{server.config.name}': {e}"
            )
