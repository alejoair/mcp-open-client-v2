"""
Process management for MCP servers using STDIO transport.
"""

import asyncio
import json
import logging
import os
import re
import signal
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..api.models.server import ServerConfig, ServerInfo, ServerStatus
from ..config import ensure_config_directory, get_config_path
from ..exceptions import MCPError

# Set up logger
logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        Slugified text
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Remove any characters that aren't alphanumeric or hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Remove consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    return text


class ProcessManager:
    """Manages MCP server processes using STDIO transport."""

    def __init__(self, config_file: str = "mcp_servers.json"):
        """
        Initialize process manager.

        Args:
            config_file: Path to JSON configuration file (relative to user config dir)
        """
        self._processes: Dict[str, subprocess.Popen] = {}
        self._servers: Dict[str, ServerInfo] = {}
        self._slug_to_id: Dict[str, str] = {}  # Slug to UUID mapping

        # Ensure config directory exists and get config file path
        ensure_config_directory()
        self._config_file = get_config_path(config_file)
        self._load_servers()

    def _load_servers(self) -> None:
        """
        Load server configurations from JSON file.

        Only loads configurations (not running state), as processes need to be started explicitly.
        """
        if not self._config_file.exists():
            return

        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            servers_data = data.get("servers", [])
            for server_data in servers_data:
                config_data = server_data.get("config")
                if config_data:
                    config = ServerConfig(**config_data)

                    # Get or generate slug
                    slug = (
                        server_data.get("slug") or config.slug or _slugify(config.name)
                    )

                    # Reset status to configured (don't restore running state)
                    server_info = ServerInfo(
                        id=server_data["id"],
                        slug=slug,
                        config=config,
                        status=ServerStatus.CONFIGURED,
                        created_at=server_data.get(
                            "created_at", datetime.utcnow().isoformat()
                        ),
                        started_at=None,  # Don't restore running state
                        stopped_at=None,
                        error_message=None,
                        process_id=None,
                    )

                    self._servers[server_info.id] = server_info
                    self._slug_to_id[slug] = server_info.id

        except Exception as e:
            # If loading fails, start with empty server list
            print(
                f"Warning: Failed to load server configurations from {self._config_file}: {e}"
            )
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
                    "id": server.id,
                    "slug": server.slug,
                    "config": {
                        "name": server.config.name,
                        "slug": server.config.slug,
                        "transport": server.config.transport,
                        "command": server.config.command,
                        "args": server.config.args,
                        "env": server.config.env,
                        "cwd": server.config.cwd,
                    },
                    "status": "configured",  # Always save as configured
                    "created_at": server.created_at,
                    "started_at": None,
                    "stopped_at": None,
                    "error_message": None,
                    "process_id": None,
                }
                servers_data.append(server_dict)

            # Save to file
            data = {
                "servers": servers_data,
                "version": "1.0",
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Create directory if it doesn't exist
            self._config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(
                f"Warning: Failed to save server configurations to {self._config_file}: {e}"
            )

    def _generate_unique_slug(self, base_slug: str) -> str:
        """
        Generate a unique slug by appending a number if necessary.

        Args:
            base_slug: Base slug to make unique

        Returns:
            Unique slug
        """
        if base_slug not in self._slug_to_id:
            return base_slug

        # Append numbers until we find a unique slug
        counter = 1
        while f"{base_slug}-{counter}" in self._slug_to_id:
            counter += 1

        return f"{base_slug}-{counter}"

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

        # Generate or use provided slug
        if config.slug:
            base_slug = _slugify(config.slug)
        else:
            base_slug = _slugify(config.name)

        slug = self._generate_unique_slug(base_slug)

        # Update config with the generated slug
        config.slug = slug

        # Create server info
        server_info = ServerInfo(
            id=server_id,
            slug=slug,
            config=config,
            status=ServerStatus.CONFIGURED,
            created_at=datetime.utcnow().isoformat(),
        )

        self._servers[server_id] = server_info
        self._slug_to_id[slug] = server_id

        # Save to JSON file
        self._save_servers()

        return server_info

    def get_server(self, server_id_or_slug: str) -> Optional[ServerInfo]:
        """
        Get server information by ID or slug.

        Args:
            server_id_or_slug: Server identifier (UUID) or slug

        Returns:
            ServerInfo or None if not found
        """
        # Try as UUID first
        server = self._servers.get(server_id_or_slug)
        if server:
            return server

        # Try as slug
        server_id = self._slug_to_id.get(server_id_or_slug)
        if server_id:
            return self._servers.get(server_id)

        return None

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

    async def start_server(self, server_id_or_slug: str) -> ServerInfo:
        """
        Start an MCP server process.

        Args:
            server_id_or_slug: Server identifier (UUID) or slug

        Returns:
            Updated server information

        Raises:
            MCPError: If server not found or already running
        """
        import traceback

        logger.info(f"Starting server: {server_id_or_slug}")

        server = self.get_server(server_id_or_slug)
        if not server:
            raise MCPError(f"Server with ID or slug '{server_id_or_slug}' not found")

        logger.info(f"Found server: {server.config.name}")
        logger.info(f"Server status: {server.status}")

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
            logger.info(f"Command to execute: {' '.join(cmd)}")

            # Start the process - use subprocess.Popen for better Windows compatibility
            import subprocess

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=server.config.cwd,
            )

            logger.info(f"Process started with PID: {process.pid}")

            # Store process and update server info
            self._processes[server.id] = process
            server.status = ServerStatus.RUNNING
            server.process_id = process.pid
            server.started_at = datetime.utcnow().isoformat()

            # Check if process is still running immediately
            if process.poll() is not None:
                # Process exited immediately
                stderr_output = ""
                try:
                    stderr_output = process.stderr.read().decode("utf-8")
                except Exception:
                    pass

                logger.error(
                    f"Process exited immediately with code {process.returncode}"
                )
                logger.error(f"Stderr: {stderr_output}")

                server.status = ServerStatus.ERROR
                server.error_message = f"Process exited immediately with code {process.returncode}: {stderr_output}"
                server.process_id = None
                server.started_at = None
                del self._processes[server.id]

                raise MCPError(
                    f"Failed to start server '{server.config.name}': Process exited with code {process.returncode}"
                )

            logger.info(f"Server '{server.config.name}' started successfully")
            return server

        except Exception as e:
            error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            logger.error(
                f"Error starting server '{server.config.name}': {error_details}"
            )

            server.status = ServerStatus.ERROR
            server.error_message = str(e)
            if server.id in self._processes:
                del self._processes[server.id]
            raise MCPError(
                f"Failed to start server '{server.config.name}': {error_details}"
            )

    async def stop_server(self, server_id_or_slug: str) -> ServerInfo:
        """
        Stop an MCP server process.

        Args:
            server_id_or_slug: Server identifier (UUID) or slug

        Returns:
            Updated server information

        Raises:
            MCPError: If server not found or not running
        """
        server = self.get_server(server_id_or_slug)
        if not server:
            raise MCPError(f"Server with ID or slug '{server_id_or_slug}' not found")

        if server.status not in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            raise MCPError(f"Server '{server.config.name}' is not running")

        process = self._processes.get(server.id)
        if process:
            server.status = ServerStatus.STOPPING

            try:
                # Try graceful termination first
                process.terminate()
                try:
                    # Use a background thread for the timeout since process.wait is blocking
                    import threading

                    def wait_for_process():
                        return process.wait()

                    wait_thread = threading.Thread(target=wait_for_process)
                    wait_thread.daemon = True
                    wait_thread.start()
                    wait_thread.join(timeout=5.0)

                    if wait_thread.is_alive():
                        # Timeout - force kill
                        process.kill()
                        process.wait()
                except Exception:
                    # Force kill if there's any error
                    try:
                        process.kill()
                        process.wait()
                    except Exception:
                        pass

            except Exception as e:
                # Process might already be dead or killed
                # Try force kill as last resort
                try:
                    process.kill()
                except Exception:
                    pass
                # Don't raise error - cleanup will happen in finally block
                # Log the error but consider it a successful stop since cleanup happens
                logger.warning(
                    f"Error during stop of server '{server.config.name}': {e}. "
                    "Process cleanup will continue."
                )
                # Continue with cleanup - don't re-raise the exception

            finally:
                # Always cleanup process tracking
                if server.id in self._processes:
                    del self._processes[server.id]
                server.status = ServerStatus.STOPPED
                server.process_id = None
                server.stopped_at = datetime.utcnow().isoformat()

        return server

    async def remove_server(self, server_id_or_slug: str) -> bool:
        """
        Remove a server configuration.

        Args:
            server_id_or_slug: Server identifier (UUID) or slug

        Returns:
            True if server was removed, False if not found

        Raises:
            MCPError: If server is running
        """
        server = self.get_server(server_id_or_slug)
        if not server:
            return False

        if server.status in [ServerStatus.RUNNING, ServerStatus.STARTING]:
            raise MCPError(
                f"Cannot remove running server '{server.config.name}'. Stop it first."
            )

        del self._servers[server.id]
        del self._slug_to_id[server.slug]

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
            server_id
            for server_id, server in self._servers.items()
            if server.status in [ServerStatus.RUNNING, ServerStatus.STARTING]
        ]

        # Stop all running servers concurrently
        if running_server_ids:
            await asyncio.gather(
                *[self.stop_server(server_id) for server_id in running_server_ids],
                return_exceptions=True,
            )

    def get_process(self, server_id: str) -> Optional[subprocess.Popen]:
        """
        Get the process for a running server.

        Args:
            server_id: Server identifier

        Returns:
            Process or None if not found or not running
        """
        return self._processes.get(server_id)

    def check_server_health(self, server_id: str) -> bool:
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
        return process.poll() is None
