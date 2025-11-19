"""
Process management for MCP servers - Configuration and state management.

Note: Actual process lifecycle is now managed by FastMCP clients in manager.py.
This module handles server configuration persistence and state tracking only.
"""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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
    """
    Manages MCP server configurations and state.

    Note: Process lifecycle (start/stop) is handled by FastMCP clients in MCPServerManager.
    This class only manages configuration persistence and status tracking.
    """

    def __init__(self, config_file: str = "mcp_servers.json"):
        """
        Initialize process manager.

        Args:
            config_file: Path to JSON configuration file (relative to user config dir)
        """
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
            logger.warning(
                f"Failed to load server configurations from {self._config_file}: {e}"
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
                        # HTTP transport fields
                        "url": server.config.url,
                        "headers": server.config.headers,
                        "auth_type": server.config.auth_type,
                        "auth_token": server.config.auth_token,
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
            logger.warning(
                f"Failed to save server configurations to {self._config_file}: {e}"
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

    def _update_server_status(
        self,
        server_id: str,
        status: ServerStatus,
        process_id: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> ServerInfo:
        """
        Update server status without managing processes.

        This is used by MCPServerManager to update status when FastMCP
        manages the process lifecycle.

        Args:
            server_id: Server identifier
            status: New server status
            process_id: Optional process ID
            error_message: Optional error message

        Returns:
            Updated server information

        Raises:
            MCPError: If server not found
        """
        server = self._servers.get(server_id)
        if not server:
            raise MCPError(f"Server with ID '{server_id}' not found")

        # Update status
        server.status = status

        # Update timestamps based on status
        if status == ServerStatus.STARTING:
            server.error_message = None
        elif status == ServerStatus.RUNNING:
            server.started_at = datetime.utcnow().isoformat()
            server.stopped_at = None
            server.error_message = None
            if process_id:
                server.process_id = process_id
        elif status == ServerStatus.STOPPING:
            pass  # Keep current timestamps
        elif status == ServerStatus.STOPPED:
            server.stopped_at = datetime.utcnow().isoformat()
            server.process_id = None
        elif status == ServerStatus.ERROR:
            server.error_message = error_message
            server.process_id = None

        return server
