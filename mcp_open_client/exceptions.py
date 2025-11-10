"""
Custom exceptions for the MCP Open Client package.
"""


class MCPError(Exception):
    """Base exception class for MCP Open Client errors."""
    pass


class ConnectionError(MCPError):
    """Raised when there's an error connecting to an MCP server."""
    pass


class ProtocolError(MCPError):
    """Raised when there's an error in the MCP protocol communication."""
    pass


class AuthenticationError(MCPError):
    """Raised when there's an error with authentication."""
    pass


class TimeoutError(MCPError):
    """Raised when an operation times out."""
    pass