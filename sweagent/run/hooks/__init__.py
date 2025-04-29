"""
Run hooks for SWE-agent.

This package contains hooks that run at different stages of the SWE-agent
execution. These hooks can be used to customize the behavior of the agent.
"""

from .github_mcp_pr import GitHubMCPPRHook, GitHubMCPPRConfig

__all__ = [
    "GitHubMCPPRHook",
    "GitHubMCPPRConfig"
]