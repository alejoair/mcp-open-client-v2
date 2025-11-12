"""
FastMCP Transport Factory - Creates appropriate transports based on command configuration.
"""

import logging
from typing import Any

from ..exceptions import MCPError

logger = logging.getLogger(__name__)


def create_transport(config) -> Any:
    """
    Create appropriate FastMCP transport based on command configuration.

    Returns a transport with keep_alive=True, which maintains the subprocess
    connection across multiple Client usages.

    Args:
        config: ServerConfig object with command, args, env, cwd

    Returns:
        FastMCP transport instance

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
    logger.info(f"Creating FastMCP transport for command: {config.command}")
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
    """Create NpxStdioTransport for npm/npx packages."""
    from fastmcp.client import NpxStdioTransport

    logger.info("Detected npx/npm command, using NpxStdioTransport")

    # Extract package name from args
    if config.args and len(config.args) >= 2:
        if config.args[0] in ["-y", "-x"]:
            package_name = config.args[1]
            remaining_args = config.args[2:] if len(config.args) > 2 else []
        else:
            package_name = config.args[0]
            remaining_args = config.args[1:] if len(config.args) > 1 else []

        logger.info(f"Package: {package_name}, Args: {remaining_args}")
        return NpxStdioTransport(
            package=package_name,
            args=remaining_args,
            env_vars=config.env,
            project_directory=config.cwd,
            keep_alive=True,  # Reuse subprocess across calls
        )
    else:
        logger.error("Not enough arguments for npx command")
        raise MCPError("Not enough arguments for npx command")


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
