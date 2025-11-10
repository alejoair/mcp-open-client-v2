"""
Process management for MCP servers using STDIO transport.
"""

import asyncio
import json
import os
import signal
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..api.models.server import ServerConfig, ServerInfo, ServerStatus
from ..exceptions import MCPError


class ProcessManager:
    """Manages MCP server processes using STDIO transport."""
    
    def __init__(self, config_file: str = "mcp_servers.json"):
        """
        Initialize process manager.
        
        Args:
            config_file: Path to JSON configuration file
        """
        self._processes: Dict[str, asyncio.subprocess.Process] = {}
        self._servers: Dict[str, ServerInfo] = {}
        self._config_file = Path(config_file)
        self._load_servers()
    
    def _load_servers(self) -> None:
        """
        Load server configurations from JSON file.
        
        Only loads configurations (not running state), as processes need to be started explicitly.
        """
        if not self._config_file.exists():
            return
        
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            servers_data = data.get('servers', [])
            for server_data in servers_data:
                config_data = server_data.get('config')
                if config_data:
                    config = ServerConfig(**config_data)
                    
                    # Reset status to configured (don't restore running state)
                    server_info = ServerInfo(
                        id=server_data['id'],
                        config=config,
                        status=ServerStatus.CONFIGURED,
                        created_at=server_data.get('created_at', datetime.utcnow().isoformat()),
                        started_at=None,  # Don't restore running state
                        stopped_at=None,
                        error_message=None,
                        process_id=None
                    )
                    
                    self._servers[server_info.id] = server_info
                    
        except Exception as e:
            # If loading fails, start with empty server list
            print(f"Warning: Failed to load server configurations from {self._config_file}: {e}")
            self._servers = {}
    
    def _save_servers(self) -> None:
        """
        Save server configurations to JSON file.
        
        Only saves configurations and metadata, not running processes.
        """
        try:
            # Convert servers to dict format
            servers_data = []
            for server_id, server in self._servers.items():
                server_dict = {
                    'id': server.id,
                    'config': {
                        'name': server.config.name,
                        'transport': server.config.transport,
                        'command': server.config.command,
                        'args': server.config.args,
                        'env': server.config.env,
                        'cwd': server.config.cwd
                    },
                    'status': 'configured',  # Always save as configured
                    'created_at': server.created_at,
                    'started_at': None,
                    'stopped_at': None,
                    'error_message': None,
                    'process_id': None
                }
                servers_data.append(server_dict)
            
            # Save to file
            data = {
                'servers': servers_data,
                'version': '1.0',
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Create directory if it doesn't exist
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Failed to save server configurations to {self._config_file}: {e}")

    async def add_server(self, config: ServerConfig) -> ServerInfo:
        """
        Add a new server configuration.
        
        Args:
            config: Server configuration
            
        Returns:
            ServerInfo: Created server information
            
        Raises:
            MCPError: If server name already exists
        """
        # Check for duplicate names
        for server in self._servers.values():
            if server.config.name == config.name:
                raise MCPError(f"Server with name '{config.name}' already exists")
        
        # Generate unique ID
        server_id = str(uuid.uuid4())
        
        # Create server info
        server_info = ServerInfo(
            id=server_id,
            config=config,
            status=ServerStatus.CONFIGURED,
            created_at=datetime.utcnow().isoformat(),
        )
        
        self._servers[server_id] = server_info
        
        # Save to JSON file
        self._save_servers()
        
        return server_info
    
    def get_server(self, server_id: str) -> Optional[ServerInfo]:
        """
        Get server information by ID.
        
        Args:
            server_id: Server identifier
            
        Returns:
            ServerInfo or None if not found
        """
        return self._servers.get(server_id)
    
    def get_all_servers(self) -> List[ServerInfo]:
        """
        Get all server information.
        
        Returns:
            List of all servers
        """
        return list(self._servers.values())
    
    def find_server_by_name(self, name: str) -> Optional[ServerInfo]:
        """
        Find server by name.
        
        Args:
            name: Server name
            
        Returns:
            ServerInfo or None if not found
        """
        for server in self._servers.values():
            if server.config.name == name:
                return server
        return None
    
    async def start_server(self, server_id: str) -> ServerInfo:
        """
        Start an MCP server process.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Updated server information
            
        Raises:
            MCPError: If server not found or already running
        """
        server = self._servers.get(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")
        
        if server.status == ServerStatus.RUNNING:
            raise MCPError(f"Server '{server.config.name}' is already running")
        
        if server.status == ServerStatus.STARTING:
            raise MCPError(f"Server '{server.config.name}' is already starting")
        
        # Update status to starting
        server.status = ServerStatus.STARTING
        server.error_message = None
        
        try:
            # Prepare environment
            env = os.environ.copy()
            if server.config.env:
                env.update(server.config.env)
            
            # Prepare command
            cmd = [server.config.command] + server.config.args
            
            # Start the process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=server.config.cwd,
            )
            
            # Store process and update server info
            self._processes[server_id] = process
            server.status = ServerStatus.RUNNING
            server.process_id = process.pid
            server.started_at = datetime.utcnow().isoformat()
            
            # Give the process a moment to start and check if it's still alive
            await asyncio.sleep(0.1)
            if process.returncode is not None:
                # Process exited immediately
                stderr_output = ""
                try:
                    stderr_output = await process.stderr.read()
                    stderr_output = stderr_output.decode('utf-8')
                except Exception:
                    pass
                
                server.status = ServerStatus.ERROR
                server.error_message = f"Process exited immediately with code {process.returncode}: {stderr_output}"
                server.process_id = None
                server.started_at = None
                del self._processes[server_id]
                
                raise MCPError(f"Failed to start server '{server.config.name}': Process exited with code {process.returncode}")
            
            return server
            
        except Exception as e:
            server.status = ServerStatus.ERROR
            server.error_message = str(e)
            if server_id in self._processes:
                del self._processes[server_id]
            raise MCPError(f"Failed to start server '{server.config.name}': {e}")
    
    async def stop_server(self, server_id: str) -> ServerInfo:
        """
        Stop an MCP server process.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Updated server information
            
        Raises:
            MCPError: If server not found or not running
        """
        server = self._servers.get(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")
        
        if server.status not in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            raise MCPError(f"Server '{server.config.name}' is not running")
        
        process = self._processes.get(server_id)
        if process:
            server.status = ServerStatus.STOPPING
            
            try:
                # Try graceful termination first
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    process.kill()
                    await process.wait()
            
            except Exception as e:
                # Process might already be dead
                try:
                    process.kill()
                except Exception:
                    pass
                raise MCPError(f"Error stopping server '{server.config.name}': {e}")
            
            finally:
                del self._processes[server_id]
                server.status = ServerStatus.STOPPED
                server.process_id = None
                server.stopped_at = datetime.utcnow().isoformat()
        
        return server
    
    async def remove_server(self, server_id: str) -> bool:
        """
        Remove a server configuration.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if server was removed, False if not found
            
        Raises:
            MCPError: If server is running
        """
        server = self._servers.get(server_id)
        if not server:
            return False
        
        if server.status in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            raise MCPError(f"Cannot remove running server '{server.config.name}'. Stop it first.")
        
        del self._servers[server_id]
        
        # Save to JSON file
        self._save_servers()
        
        return True
    
    async def shutdown_all(self) -> None:
        """
        Shutdown all running servers.
        
        This should be called when the application is shutting down.
        """
        # Get list of running servers
        running_server_ids = [
            server_id for server_id, server in self._servers.items()
            if server.status in [ServerStatus.RUNNING, ServerStatus.STARTING]
        ]
        
        # Stop all running servers concurrently
        if running_server_ids:
            await asyncio.gather(
                *[self.stop_server(server_id) for server_id in running_server_ids],
                return_exceptions=True
            )
    
    def get_process(self, server_id: str) -> Optional[asyncio.subprocess.Process]:
        """
        Get the process for a running server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Process or None if not found or not running
        """
        return self._processes.get(server_id)
    
    async def check_server_health(self, server_id: str) -> bool:
        """
        Check if a server process is still healthy.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if server is healthy, False otherwise
        """
        process = self._processes.get(server_id)
        if not process:
            return False
        
        # Check if process is still running
        return process.returncode is None