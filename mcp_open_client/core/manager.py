"""
MCP Server Manager - Integrates FastMCP clients with process management.
"""

import asyncio
from typing import Dict, List, Optional, Any

try:
    from fastmcp import Client
except ImportError:
    Client = None

from ..api.models.server import ServerInfo, ServerStatus, ToolInfo
from .process import ProcessManager
from ..exceptions import MCPError


class MCPServerManager:
    """
    Main manager for MCP servers using FastMCP clients and process management.
    """
    
    def __init__(self):
        """Initialize MCP server manager."""
        self._process_manager = ProcessManager()
        self._clients: Dict[str, Client] = {}
    
    def _create_fastmcp_client(self, config):
        """Create appropriate FastMCP client based on command configuration."""
        from fastmcp.client import NpxStdioTransport, NodeStdioTransport, PythonStdioTransport
        
        command = config.command.lower()
        
        # Handle npm/npx packages
        if command == "npx" or command == "npm.cmd":
            # Extract package name from args
            if config.args and len(config.args) >= 2:
                if config.args[0] in ["-y", "-x"]:
                    package_name = config.args[1]
                    remaining_args = config.args[2:] if len(config.args) > 2 else []
                else:
                    package_name = config.args[0]
                    remaining_args = config.args[1:] if len(config.args) > 1 else []
                
                transport = NpxStdioTransport(
                    package=package_name,
                    args=remaining_args,
                    env_vars=config.env
                )
                return Client(transport)
        
        # Handle node commands
        elif command == "node" or command.endswith("node.exe"):
            if config.args:
                script_path = config.args[0]
                remaining_args = config.args[1:] if len(config.args) > 1 else []
                transport = NodeStdioTransport(
                    script=script_path,
                    args=remaining_args,
                    env_vars=config.env
                )
                return Client(transport)
        
        # Handle python commands
        elif command == "python" or command == "python3" or command.endswith("python.exe"):
            if config.args:
                module_path = config.args[0]
                remaining_args = config.args[1:] if len(config.args) > 1 else []
                transport = PythonStdioTransport(
                    module=module_path,
                    args=remaining_args,
                    env_vars=config.env
                )
                return Client(transport)
        
        # Fallback to generic stdio transport (command string)
        return Client(f"{config.command} {' '.join(config.args)}")
    
    async def add_server(self, name: str, command: str, args: List[str] = None, 
                        env: Dict[str, str] = None, cwd: str = None) -> ServerInfo:
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
            cwd=cwd
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
        """Get server information by ID."""
        return self._process_manager.get_server(server_id)
    
    def get_all_servers(self) -> List[ServerInfo]:
        """Get all server information."""
        return self._process_manager.get_all_servers()
    
    def find_server_by_name(self, name: str) -> Optional[ServerInfo]:
        """Find server by name."""
        return self._process_manager.find_server_by_name(name)
    
    async def start_server(self, server_id: str) -> ServerInfo:
        """
        Start an MCP server and create FastMCP client.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Updated server information
        """
        if Client is None:
            raise MCPError("FastMCP is not installed. Install with: pip install fastmcp")
        
        # Start the process
        server = await self._process_manager.start_server(server_id)
        
        try:
            # Create FastMCP client for the running process
            # For STDIO processes, we need to create the client using the command
            process = self._process_manager.get_process(server_id)
            if not process:
                raise MCPError(f"Process not found for server ID '{server_id}'")
            
            # Create FastMCP client using appropriate transport
            client = self._create_fastmcp_client(server.config)
            
            # Store the client
            self._clients[server_id] = client
            
            return server
            
        except Exception as e:
            # If client creation fails, stop the process
            await self._process_manager.stop_server(server_id)
            raise MCPError(f"Failed to create FastMCP client: {e}")
    
    async def stop_server(self, server_id: str) -> ServerInfo:
        """
        Stop an MCP server and clean up FastMCP client.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Updated server information
        """
        # Clean up FastMCP client if exists
        client = self._clients.get(server_id)
        if client:
            try:
                # Close client connection if it's connected
                if hasattr(client, 'is_connected') and client.is_connected():
                    # FastMCP client might need explicit cleanup
                    pass
            except Exception:
                pass  # Ignore cleanup errors
            finally:
                del self._clients[server_id]
        
        # Stop the process
        return await self._process_manager.stop_server(server_id)
    
    async def remove_server(self, server_id: str) -> bool:
        """
        Remove a server configuration.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if server was removed
        """
        # Clean up FastMCP client if exists
        client = self._clients.get(server_id)
        if client:
            del self._clients[server_id]
        
        return await self._process_manager.remove_server(server_id)
    
    async def get_server_tools(self, server_id: str) -> List[ToolInfo]:
        """
        Get tools available from a running server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            List of available tools
            
        Raises:
            MCPError: If server not running or client not available
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")
        
        if server.status != ServerStatus.RUNNING:
            raise MCPError(f"Server '{server.config.name}' is not running (status: {server.status})")
        
        client = self._clients.get(server_id)
        if not client:
            raise MCPError(f"No FastMCP client available for server '{server.config.name}'")
        
        try:
            # Use FastMCP client to list tools
            async with client:
                tools_response = await client.list_tools()
                
                # Convert FastMCP tools to ToolInfo models
                tool_infos = []
                # Handle different response formats
                tools_list = tools_response.tools if hasattr(tools_response, 'tools') else tools_response
                for tool in tools_list:
                    tool_info = ToolInfo(
                        name=tool.name,
                        description=getattr(tool, 'description', None),
                        input_schema=getattr(tool, 'inputSchema', None)
                    )
                    tool_infos.append(tool_info)
                
                return tool_infos
                
        except Exception as e:
            raise MCPError(f"Failed to get tools from server '{server.config.name}': {e}")
    
    async def call_server_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        Call a tool on a running server.
        
        Args:
            server_id: Server identifier
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            MCPError: If server not running or client not available
        """
        server = self._process_manager.get_server(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")
        
        if server.status != ServerStatus.RUNNING:
            raise MCPError(f"Server '{server.config.name}' is not running (status: {server.status})")
        
        client = self._clients.get(server_id)
        if not client:
            raise MCPError(f"No FastMCP client available for server '{server.config.name}'")
        
        try:
            # Use FastMCP client to call tool
            async with client:
                result = await client.call_tool(tool_name, arguments or {})
                return result
                
        except Exception as e:
            raise MCPError(f"Failed to call tool '{tool_name}' on server '{server.config.name}': {e}")
    
    async def shutdown_all(self) -> None:
        """Shutdown all running servers and clean up clients."""
        # Close all FastMCP clients
        for server_id in list(self._clients.keys()):
            client = self._clients.get(server_id)
            if client:
                try:
                    # Close client connection if it's connected
                    if hasattr(client, 'is_connected') and client.is_connected():
                        pass
                except Exception:
                    pass  # Ignore cleanup errors
        
        self._clients.clear()
        
        # Shutdown all processes
        await self._process_manager.shutdown_all()
    
    def get_client(self, server_id: str) -> Optional[Client]:
        """
        Get the FastMCP client for a server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            FastMCP client or None if not available
        """
        return self._clients.get(server_id)
    
    async def check_server_health(self, server_id: str) -> bool:
        """
        Check if a server process is still healthy.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if server is healthy, False otherwise
        """
        return await self._process_manager.check_server_health(server_id)