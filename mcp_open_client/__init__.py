"""
MCP Open Client - An open MCP client implementation.

This package provides a client implementation for the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import MCPClient
from .exceptions import MCPError

__all__ = [
    "MCPClient",
    "MCPError",
    "__version__",
]