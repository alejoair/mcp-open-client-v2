"""
FastAPI endpoints for MCP Registry discovery.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from ...core.registry_client import MCPRegistryClient
from ..models.registry import (
    RegistryCategoriesResponse,
    RegistryHealthResponse,
    RegistrySearchResponse,
    RegistryServerDetailResponse,
    RegistryServerInfo,
)

router = APIRouter(prefix="/registry", tags=["registry"])

# Global registry client instance
_registry_client = MCPRegistryClient()


def _parse_server_data(server_entry: dict) -> RegistryServerInfo:
    """Parse server entry from registry to RegistryServerInfo model."""
    server = server_entry.get("server", {})
    meta = server_entry.get("_meta", {}).get(
        "io.modelcontextprotocol.registry/official", {}
    )

    # Extract transport types
    transport_types = []
    if "packages" in server:
        for package in server["packages"]:
            transport = package.get("transport", {})
            transport_type = transport.get("type")
            if transport_type and transport_type not in transport_types:
                transport_types.append(transport_type)

    if "remotes" in server:
        for remote in server["remotes"]:
            remote_type = remote.get("type")
            if remote_type and remote_type not in transport_types:
                transport_types.append(remote_type)

    # Extract repository URL
    repository = server.get("repository", {})
    repository_url = repository.get("url")

    return RegistryServerInfo(
        name=server.get("name", ""),
        description=server.get("description"),
        version=server.get("version"),
        repository_url=repository_url,
        published_at=meta.get("publishedAt"),
        updated_at=meta.get("updatedAt"),
        transport_types=transport_types,
        full_data=server_entry,
    )


@router.get(
    "/search",
    response_model=RegistrySearchResponse,
    operation_id="registry_search_servers",
)
async def search_servers(
    q: Optional[str] = Query(
        None, description="Search query to filter server names", alias="q"
    ),
    limit: Optional[int] = Query(
        20, description="Maximum number of results", ge=1, le=100
    ),
):
    """
    Search for MCP servers in the official registry.

    - **q**: Optional search query to filter server names
    - **limit**: Maximum number of results to return (1-100)
    """
    try:
        result = await _registry_client.search_servers(search=q, limit=limit)

        servers = []
        for server_entry in result.get("servers", []):
            try:
                servers.append(_parse_server_data(server_entry))
            except Exception:
                # Skip servers that fail to parse
                continue

        return RegistrySearchResponse(
            success=True,
            servers=servers,
            count=len(servers),
            total=len(result.get("servers", [])),
            message=f"Found {len(servers)} servers",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to query registry: {str(e)}",
        )


@router.get(
    "/servers",
    response_model=RegistrySearchResponse,
    operation_id="registry_list_servers",
)
async def list_servers(
    limit: Optional[int] = Query(
        50, description="Maximum number of results", ge=1, le=100
    )
):
    """
    List all available MCP servers from the registry.

    - **limit**: Maximum number of results to return (1-100)
    """
    try:
        servers_data = await _registry_client.list_all_servers(limit=limit)

        servers = []
        for server_entry in servers_data:
            try:
                servers.append(_parse_server_data(server_entry))
            except Exception:
                continue

        return RegistrySearchResponse(
            success=True,
            servers=servers,
            count=len(servers),
            message=f"Retrieved {len(servers)} servers from registry",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to list servers from registry: {str(e)}",
        )


@router.get(
    "/servers/{server_name:path}",
    response_model=RegistryServerDetailResponse,
    operation_id="registry_get_server",
)
async def get_server(server_name: str):
    """
    Get detailed information about a specific server.

    - **server_name**: Full server name (e.g., "ai.exa/exa")
    """
    try:
        server_entry = await _registry_client.get_server_by_name(server_name)

        if not server_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not found in registry",
            )

        server_info = _parse_server_data(server_entry)

        return RegistryServerDetailResponse(
            success=True,
            server=server_info,
            message=f"Retrieved server '{server_name}'",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get server from registry: {str(e)}",
        )


@router.get(
    "/categories",
    response_model=RegistryCategoriesResponse,
    operation_id="registry_get_categories",
)
async def get_categories():
    """
    Get servers grouped by category/namespace.

    Returns servers organized by their namespace (e.g., "ai.exa", "com.github", etc.)
    """
    try:
        categories = await _registry_client.get_server_categories()

        return RegistryCategoriesResponse(
            success=True,
            categories=categories,
            count=len(categories),
            message=f"Retrieved {len(categories)} categories",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to get categories from registry: {str(e)}",
        )


@router.get(
    "/health",
    response_model=RegistryHealthResponse,
    operation_id="registry_health_check",
)
async def check_registry_health():
    """
    Check if the MCP registry is accessible and healthy.
    """
    try:
        is_healthy = await _registry_client.health_check()

        if is_healthy:
            return RegistryHealthResponse(
                success=True, status="healthy", message="Registry is accessible"
            )
        else:
            return RegistryHealthResponse(
                success=False,
                status="unhealthy",
                message="Registry is not responding",
            )

    except Exception as e:
        return RegistryHealthResponse(
            success=False, status="error", message=f"Health check failed: {str(e)}"
        )


@router.on_event("shutdown")
async def shutdown_registry_client():
    """Clean up registry client on shutdown."""
    await _registry_client.close()
