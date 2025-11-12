"""
FastMCP Client Factory - Creates appropriate FastMCP clients based on command configuration.
"""

import logging
from typing import Any

from ..exceptions import MCPError

logger = logging.getLogger(__name__)


def create_transport(config) -> Any:
    """
    Create appropriate FastMCP transport based on command configuration.

    Returns a FastMCP Transport that maintains the subprocess connection.

    Args:
        config: ServerConfig object with command, args, env, cwd

    Returns:
        FastMCP Transport instance

    Raises:
        MCPError: If transport creation fails
    """
    from fastmcp.client import (
        NodeStdioTransport,
        NpxStdioTransport,
        PythonStdioTransport,
        StdioTransport,
    )

    command = config.command.lower()
    logger.info(f"Creating FastMCP client for command: {config.command}")
    logger.info(f"Command lower: {command}")
    logger.info(f"Args: {config.args}")

    # Handle npm/npx packages
    if command == "npx" or command == "npm.cmd" or "npx.cmd" in command:
        return _create_npx_transport(config)

    # Handle node commands
    elif command == "node" or command.endswith("node.exe"):
        return _create_node_transport(config)

    # Handle python commands
    elif command == "python" or command == "python3" or command.endswith("python.exe"):
        return _create_python_transport(config)

    # Fallback to generic stdio transport
    logger.info("Using fallback generic StdioTransport")
    return StdioTransport(
        command=config.command,
        args=config.args,
        env=config.env,
        cwd=config.cwd,
        keep_alive=True,
    )


def _create_npx_transport(config) -> Any:
    """Create StdioTransport for npm/npx packages."""
    from fastmcp.client import StdioTransport

    logger.info("Detected npx/npm command, using StdioTransport directly")

    # Use StdioTransport directly with full command
    # This is the recommended approach per FastMCP documentation
    logger.info(f"Command: {config.command}, Args: {config.args}")
    return StdioTransport(
        command=config.command,
        args=config.args,
        env=config.env,
        cwd=config.cwd,
        keep_alive=True,
    )


def _create_node_transport(config) -> Any:
    """Create NodeStdioTransport for Node.js scripts."""
    from fastmcp.client import NodeStdioTransport

    logger.info("Detected node command, using NodeStdioTransport")

    if config.args:
        script_path = config.args[0]
        remaining_args = config.args[1:] if len(config.args) > 1 else []
        return NodeStdioTransport(
            script_path=script_path,
            args=remaining_args,
            env=config.env,
            cwd=config.cwd,
            keep_alive=True,
        )
    else:
        raise MCPError("No script path provided for node command")


def _create_python_transport(config) -> Any:
    """Create PythonStdioTransport for Python modules."""
    from fastmcp.client import PythonStdioTransport

    logger.info("Detected python command, using PythonStdioTransport")

    if config.args:
        module_path = config.args[0]
        remaining_args = config.args[1:] if len(config.args) > 1 else []
        return PythonStdioTransport(
            script_path=module_path,
            args=remaining_args,
            env=config.env,
            cwd=config.cwd,
            keep_alive=True,
        )
    else:
        raise MCPError("No module path provided for python command")
