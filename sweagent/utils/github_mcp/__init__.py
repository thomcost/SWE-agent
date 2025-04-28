"""
GitHub Model Context Protocol (MCP) integration for SWE-agent.

This module provides integration with GitHub's MCP API, which allows programmatic
access to GitHub's features and data. MCP provides a more structured and stable
interface compared to the traditional REST API or ghapi.
"""

from .client import GitHubMCPClient
from .issue import Issue, IssueState
from .repository import Repository
from .pull_request import PullRequest, PullRequestState

__all__ = [
    "GitHubMCPClient",
    "Issue",
    "IssueState",
    "Repository",
    "PullRequest",
    "PullRequestState",
]