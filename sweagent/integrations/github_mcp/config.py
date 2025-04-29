"""
Configuration module for GitHub MCP integration.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field


class GitHubMCPConfig(BaseModel):
    """Configuration for the GitHub MCP integration."""
    
    github_token: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_TOKEN", ""),
        description="GitHub Personal Access Token for authentication"
    )
    
    github_host: Optional[str] = Field(
        default=None,
        description="GitHub Enterprise Server hostname (if using GitHub Enterprise)"
    )
    
    enabled_toolsets: List[str] = Field(
        default=["repos", "issues", "pull_requests", "code_security", "users"],
        description="Enabled GitHub MCP toolsets"
    )
    
    dynamic_toolsets: bool = Field(
        default=False,
        description="Enable dynamic toolset discovery"
    )
    
    docker_image: str = Field(
        default="ghcr.io/github/github-mcp-server",
        description="Docker image for GitHub MCP Server"
    )
    
    server_path: Optional[str] = Field(
        default=None,
        description="Path to local GitHub MCP Server binary (if not using Docker)"
    )
    
    use_docker: bool = Field(
        default=True,
        description="Use Docker to run GitHub MCP Server"
    )
    
    server_port: int = Field(
        default=9127,
        description="Port for GitHub MCP Server"
    )
    
    @property
    def toolsets_string(self) -> str:
        """Get the toolsets as a comma-separated string."""
        return ",".join(self.enabled_toolsets)