"""
Lifecycle Manager - Handle server lifecycle (start, stop, shutdown).
"""

import logging
import traceback
from typing import Any, Dict

try:
    from fastmcp import Client
except ImportError:
    Client = None

from ..api.models.server import ServerInfo, ServerStatus
from ..exceptions import MCPError
from .process import ProcessManager
from .transport_factory import create_client

logger = logging.getLogger(__name__)


async def start_server(
    server: ServerInfo,
    clients: Dict[str, Any],
    process_manager: ProcessManager,
) -> ServerInfo:
    """
    Start an MCP server by creating a FastMCP client.

    The client maintains the subprocess connection and can be reused
    for multiple operations.

    Args:
        server: ServerInfo object
        clients: Dictionary storing client instances by server ID
        process_manager: ProcessManager instance

    Returns:
        Updated server information

    Raises:
        MCPError: If server start fails
    """
    if Client is None:
        raise MCPError("FastMCP is not installed. Install with: pip install fastmcp")

    # Check if client already exists (server was already running)
    if server.id in clients:
        logger.info(
            f"Client already exists for server: {server.config.name}, server is running"
        )
        return server

    # Update server status to starting
    server = process_manager._update_server_status(server.id, ServerStatus.STARTING)

    try:
        logger.info(f"Creating FastMCP client for server: {server.config.name}")
        logger.info(f"Config command: {server.config.command}")
        logger.info(f"Config args: {server.config.args}")

        # Create FastMCP client
        client = create_client(server.config)

        # Connect the client initially
        await client.__aenter__()

        logger.info(
            f"Client created and connected successfully for server: {server.config.name}"
        )

        # Store the client
        clients[server.id] = client

        # Update server status to running
        server = process_manager._update_server_status(server.id, ServerStatus.RUNNING)

        logger.info(f"Server '{server.config.name}' started successfully")
        return server

    except Exception as e:
        # Log full traceback for debugging
        error_details = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Failed to start server '{server.config.name}': {error_details}")

        # Update status to error
        process_manager._update_server_status(
            server.id, ServerStatus.ERROR, error_message=str(e)
        )

        # Clean up client if it was stored
        if server.id in clients:
            try:
                client_instance = clients[server.id]
                await client_instance.__aexit__(None, None, None)
            except Exception:
                pass
            finally:
                del clients[server.id]

        # Re-raise with full error details
        raise MCPError(
            f"Failed to create client for '{server.config.name}': {error_details}"
        )


async def stop_server(
    server: ServerInfo,
    clients: Dict[str, Any],
    process_manager: ProcessManager,
) -> ServerInfo:
    """
    Stop an MCP server and close the FastMCP client.

    Args:
        server: ServerInfo object
        clients: Dictionary storing client instances by server ID
        process_manager: ProcessManager instance

    Returns:
        Updated server information
    """
    # Update status to stopping
    server = process_manager._update_server_status(server.id, ServerStatus.STOPPING)

    # Close client if it exists
    client = clients.get(server.id)
    if client:
        try:
            logger.info(f"Closing client for server: {server.config.name}")
            # Close client (this stops the subprocess)
            await client.__aexit__(None, None, None)
            logger.info(f"Client closed for server: {server.config.name}")
        except Exception as e:
            logger.error(f"Error closing client: {e}")
        finally:
            del clients[server.id]

    # Update status to stopped
    server = process_manager._update_server_status(server.id, ServerStatus.STOPPED)

    return server


async def remove_server(
    server: ServerInfo,
    clients: Dict[str, Any],
    process_manager: ProcessManager,
) -> bool:
    """
    Remove a server configuration.

    Args:
        server: ServerInfo object
        clients: Dictionary storing client instances by server ID
        process_manager: ProcessManager instance

    Returns:
        True if server was removed
    """
    # Clean up FastMCP client if exists
    client = clients.get(server.id)
    if client:
        try:
            await client.__aexit__(None, None, None)
        except Exception:
            pass  # Ignore cleanup errors
        finally:
            del clients[server.id]

    return await process_manager.remove_server(server.id)


async def shutdown_all(
    clients: Dict[str, Any],
    process_manager: ProcessManager,
) -> None:
    """
    Shutdown all running servers and clean up clients.

    Args:
        clients: Dictionary storing client instances by server ID
        process_manager: ProcessManager instance
    """
    # Close all FastMCP clients
    for server_id in list(clients.keys()):
        client = clients.get(server_id)
        if client:
            try:
                logger.info(f"Closing client for server {server_id}")
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing client for server {server_id}: {e}")
                pass  # Ignore cleanup errors

    clients.clear()

    # Update all server statuses to stopped
    for server in process_manager.get_all_servers():
        if server.status == ServerStatus.RUNNING:
            process_manager._update_server_status(server.id, ServerStatus.STOPPED)
