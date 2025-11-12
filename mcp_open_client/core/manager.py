"""
MCP Server Manager - Main orchestrator for MCP server operations.

This manager coordinates between different specialized modules:
- transport_factory: Creates FastMCP clients
- lifecycle_manager: Handles server start/stop/shutdown
- tool_operations: Manages tool discovery and execution
- process: Manages server configuration and state
"""

from typing import Any, Dict, List, Optional

from ..api.models.server import ServerInfo, ToolInfo
from ..exceptions import MCPError
from . import lifecycle_manager, tool_operations
from .process import ProcessManager


class MCPServerManager:
    """
    Main manager for MCP servers using FastMCP clients.

    This manager creates and manages FastMCP Client instances for each server.
    The clients maintain subprocess connections and can be used directly for
    operations like listing tools and calling tools.
    """

    def __init__(self):
        """Initialize MCP server manager."""
        self._process_manager = ProcessManager()
        self._transports: Dict[str, Any] = {}  # Stores FastMCP Transport instances

    # ========== Server Configuration Operations ==========

    async def add_server(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        cwd: str = None,
    ) -> ServerInfo:
        """
        Add a new MCP server configuration.

        Args:
            name: Server name
            command: Command to execute
            args: Command arguments
            env: Environment variables
            cwd: Working directory

        Returns:
            ServerInfo: Created server information
        """
        from ..api.models.server import ServerConfig

        config = ServerConfig(
            name=name,
            transport="stdio",
            command=command,
            args=args or [],
            env=env,
            cwd=cwd,
        )

        return await self._process_manager.add_server(config)

    async def add_server_from_config(self, config) -> ServerInfo:
        """
        Add server from configuration object.

        Args:
            config: ServerConfig object

        Returns:
            ServerInfo: Created server information
        """
        return await self._process_manager.add_server(config)

    def get_server(self, server_id: str) -> Optional[ServerInfo]:
        """Get server information by ID or slug."""
        return self._process_manager.get_server(server_id)

    def get_all_servers(self) -> List[ServerInfo]:
        """Get all server information."""
        return self._process_manager.get_all_servers()

    def find_server_by_name(self, name: str) -> Optional[ServerInfo]:
        """Find server by name."""
        return self._process_manager.find_server_by_name(name)

    # ========== Server Lifecycle Operations ==========

    async def start_server(self, server_id: str) -> ServerInfo:
        """
        Start an MCP server by creating a FastMCP transport.

        Args:
            server_id: Server identifier (UUID or slug)

        Returns:
            Updated server information

        Raises:
            MCPError: If server start fails
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")

        return await lifecycle_manager.start_server(
            server,
            self._transports,
            self._process_manager,
        )

    async def stop_server(self, server_id: str) -> ServerInfo:
        """
        Stop an MCP server and close the FastMCP transport.

        Args:
            server_id: Server identifier (UUID or slug)

        Returns:
            Updated server information

        Raises:
            MCPError: If server not found
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")

        return await lifecycle_manager.stop_server(
            server,
            self._transports,
            self._process_manager,
        )

    async def remove_server(self, server_id: str) -> bool:
        """
        Remove a server configuration.

        Args:
            server_id: Server identifier (UUID or slug)

        Returns:
            True if server was removed

        Raises:
            MCPError: If server not found
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            return False

        return await lifecycle_manager.remove_server(
            server,
            self._transports,
            self._process_manager,
        )

    async def shutdown_all(self) -> None:
        """Shutdown all running servers and clean up transports."""
        await lifecycle_manager.shutdown_all(
            self._transports,
            self._process_manager,
        )

    # ========== Tool Operations ==========

    async def get_server_tools(self, server_id: str) -> List[ToolInfo]:
        """
        Get tools available from a running server.

        Args:
            server_id: Server identifier (UUID or slug)

        Returns:
            List of available tools

        Raises:
            MCPError: If server not running or transport not available
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            raise MCPError(f"Server with ID or slug '{server_id}' not found")

        transport = self._transports.get(server.id)
        return await tool_operations.get_server_tools(server, transport)

    async def call_server_tool(
        self, server_id: str, tool_name: str, arguments: Dict[str, Any] = None
    ) -> Any:
        """
        Call a tool on a running server.

        Args:
            server_id: Server identifier (UUID or slug)
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPError: If server not running or transport not available
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            raise MCPError(f"Server with ID or slug '{server_id}' not found")

        transport = self._transports.get(server.id)
        return await tool_operations.call_server_tool(
            server,
            transport,
            tool_name,
            arguments,
        )

    # ========== Utility Methods ==========

    def get_transport(self, server_id: str) -> Optional[Any]:
        """
        Get the FastMCP transport for a server.

        Args:
            server_id: Server identifier

        Returns:
            FastMCP transport or None if not available
        """
        return self._transports.get(server_id)

    def check_server_health(self, server_id: str) -> bool:
        """
        Check if a server is healthy by checking if it has a running transport.

        Args:
            server_id: Server identifier

        Returns:
            True if server has a transport (is running), False otherwise
        """
        from ..api.models.server import ServerStatus

        server = self._process_manager.get_server(server_id)
        if not server:
            return False

        # Server is healthy if it has a transport and status is RUNNING
        return server.status == ServerStatus.RUNNING and server.id in self._transports
