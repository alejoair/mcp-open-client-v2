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
from .transport_factory import create_transport

logger = logging.getLogger(__name__)


async def start_server(
    server: ServerInfo,
    transports: Dict[str, Any],
    process_manager: ProcessManager,
) -> ServerInfo:
    """
    Start an MCP server by creating a FastMCP transport.

    The transport has keep_alive=True, which means it will start and maintain
    the subprocess connection. The transport can be reused across multiple
    Client instances.

    Args:
        server: ServerInfo object
        transports: Dictionary storing transport instances by server ID
        process_manager: ProcessManager instance

    Returns:
        Updated server information

    Raises:
        MCPError: If server start fails
    """
    if Client is None:
        raise MCPError("FastMCP is not installed. Install with: pip install fastmcp")

    # Check if transport already exists (server was already running)
    if server.id in transports:
        logger.info(
            f"Transport already exists for server: {server.config.name}, server is running"
        )
        return server

    # Update server status to starting
    server = process_manager._update_server_status(server.id, ServerStatus.STARTING)

    try:
        logger.info(f"Creating FastMCP transport for server: {server.config.name}")
        logger.info(f"Config command: {server.config.command}")
        logger.info(f"Config args: {server.config.args}")

        # Create FastMCP transport (with keep_alive=True)
        transport = create_transport(server.config)

        logger.info(f"Transport created successfully for server: {server.config.name}")

        # Store the transport
        transports[server.id] = transport

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

        # Clean up transport if it was stored
        if server.id in transports:
            try:
                transport_instance = transports[server.id]
                await transport_instance.close()
            except Exception:
                pass
            finally:
                del transports[server.id]

        # Re-raise with full error details
        raise MCPError(
            f"Failed to create client for '{server.config.name}': {error_details}"
        )


async def stop_server(
    server: ServerInfo,
    transports: Dict[str, Any],
    process_manager: ProcessManager,
) -> ServerInfo:
    """
    Stop an MCP server and close the FastMCP transport.

    Args:
        server: ServerInfo object
        transports: Dictionary storing transport instances by server ID
        process_manager: ProcessManager instance

    Returns:
        Updated server information
    """
    # Update status to stopping
    server = process_manager._update_server_status(server.id, ServerStatus.STOPPING)

    # Close transport if it exists
    transport = transports.get(server.id)
    if transport:
        try:
            logger.info(f"Closing transport for server: {server.config.name}")
            # Close transport (this stops the subprocess)
            await transport.close()
            logger.info(f"Transport closed for server: {server.config.name}")
        except Exception as e:
            logger.error(f"Error closing transport: {e}")
        finally:
            del transports[server.id]

    # Update status to stopped
    server = process_manager._update_server_status(server.id, ServerStatus.STOPPED)

    return server


async def remove_server(
    server: ServerInfo,
    transports: Dict[str, Any],
    process_manager: ProcessManager,
) -> bool:
    """
    Remove a server configuration.

    Args:
        server: ServerInfo object
        transports: Dictionary storing transport instances by server ID
        process_manager: ProcessManager instance

    Returns:
        True if server was removed
    """
    # Clean up FastMCP transport if exists
    transport = transports.get(server.id)
    if transport:
        try:
            await transport.close()
        except Exception:
            pass  # Ignore cleanup errors
        finally:
            del transports[server.id]

    return await process_manager.remove_server(server.id)


async def shutdown_all(
    transports: Dict[str, Any],
    process_manager: ProcessManager,
) -> None:
    """
    Shutdown all running servers and clean up transports.

    Args:
        transports: Dictionary storing transport instances by server ID
        process_manager: ProcessManager instance
    """
    # Close all FastMCP transports
    for server_id in list(transports.keys()):
        transport = transports.get(server_id)
        if transport:
            try:
                logger.info(f"Closing transport for server {server_id}")
                await transport.close()
            except Exception as e:
                logger.error(f"Error closing transport for server {server_id}: {e}")
                pass  # Ignore cleanup errors

    transports.clear()

    # Update all server statuses to stopped
    for server in process_manager.get_all_servers():
        if server.status == ServerStatus.RUNNING:
            process_manager._update_server_status(server.id, ServerStatus.STOPPED)
