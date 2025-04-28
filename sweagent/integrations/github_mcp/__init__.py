"""
GitHub Model Context Protocol (MCP) integration for SWE-agent.

This module integrates with GitHub MCP Server to provide SWE-agent with a
standardized way to interact with GitHub repositories, issues, pull requests,
and other GitHub features.
"""

from .client import GitHubMCPClient
from .server import start_github_mcp_server, stop_github_mcp_server
from .config import GitHubMCPConfig

__all__ = [
    "GitHubMCPClient",
    "start_github_mcp_server",
    "stop_github_mcp_server",
    "GitHubMCPConfig"
]