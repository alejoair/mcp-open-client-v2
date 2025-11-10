"""
MCP Registry Client - Client for discovering MCP servers from the official registry.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class MCPRegistryClient:
    """Client for interacting with the official MCP Registry API."""

    def __init__(self, base_url: str = "https://registry.modelcontextprotocol.io"):
        """
        Initialize the MCP Registry client.

        Args:
            base_url: Base URL of the MCP registry (default: official registry)
        """
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def search_servers(
        self,
        search: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        version: str = "latest",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for MCP servers in the registry.

        Args:
            search: Case-insensitive substring to match server names
            updated_since: Filter servers modified after this timestamp
            version: Version filter (default: "latest")
            limit: Maximum number of results to return

        Returns:
            Dictionary containing servers list and pagination info
        """
        session = await self._get_session()

        # Build query parameters
        params = {}
        if search:
            params["search"] = search
        if updated_since:
            params["updated_since"] = updated_since.isoformat()
        if version:
            params["version"] = version

        url = f"{self.base_url}/v0/servers"

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # Limit results if specified
                if limit and "servers" in data:
                    data["servers"] = data["servers"][:limit]

                return data
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to fetch servers from registry: {e}")

    async def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific server by exact name match.

        Args:
            name: Exact server name (e.g., "ai.exa/exa")

        Returns:
            Server information or None if not found
        """
        # Search with the exact name
        result = await self.search_servers(search=name, version="latest")

        if "servers" not in result or not result["servers"]:
            return None

        # Find exact match
        for server_entry in result["servers"]:
            server = server_entry.get("server", {})
            if server.get("name") == name:
                return server_entry

        return None

    async def list_all_servers(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all available servers.

        Args:
            limit: Maximum number of servers to return

        Returns:
            List of server information
        """
        result = await self.search_servers(version="latest", limit=limit)
        return result.get("servers", [])

    async def get_server_categories(self) -> Dict[str, List[str]]:
        """
        Get servers grouped by category/namespace.

        Returns:
            Dictionary mapping namespaces to server lists
        """
        servers = await self.list_all_servers()
        categories: Dict[str, List[str]] = {}

        for server_entry in servers:
            server = server_entry.get("server", {})
            name = server.get("name", "")

            # Extract namespace (e.g., "ai.exa" from "ai.exa/exa")
            if "/" in name:
                namespace = name.split("/")[0]
            else:
                namespace = "other"

            if namespace not in categories:
                categories[namespace] = []
            categories[namespace].append(name)

        return categories

    async def health_check(self) -> bool:
        """
        Check if the registry is healthy.

        Returns:
            True if registry is accessible, False otherwise
        """
        session = await self._get_session()
        url = f"{self.base_url}/v0/health"

        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception:
            return False
