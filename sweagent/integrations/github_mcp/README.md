# GitHub Model Context Protocol (MCP) Integration for SWE-agent

This module integrates the GitHub Model Context Protocol (MCP) Server with SWE-agent, allowing the agent to interact with GitHub repositories, issues, pull requests, and other GitHub features using a standardized interface.

## Overview

The GitHub MCP Server is an official GitHub tool that provides a standardized API for automated tools to interact with GitHub. This integration allows SWE-agent to:

1. Create pull requests automatically when fixing issues
2. Comment on issues and pull requests
3. Create and manage branches
4. Access repository files and content
5. And more...

## Components

The integration consists of:

- **Client**: A Python client for the GitHub MCP Server API
- **Server Manager**: Functions to start and stop the GitHub MCP Server
- **Configuration**: Pydantic models for configuring the integration
- **Hooks**: Run hooks for creating pull requests and interacting with GitHub
- **Mock Server**: A mock implementation for testing without Docker

## Installation

The integration requires either Docker or a local GitHub MCP Server binary:

### With Docker

1. Install Docker on your system
2. Set the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable with a GitHub personal access token
3. The integration will automatically download and run the GitHub MCP Server Docker image

### With Mock Server

For development and testing, a mock server is provided that simulates the GitHub MCP Server API:

1. Set the `USE_MOCK_SERVER` environment variable to `true`
2. The integration will use the mock server instead of the real GitHub MCP Server

## Configuration

Configure the integration using the `GitHubMCPConfig` class:

```python
from sweagent.integrations.github_mcp import GitHubMCPConfig

config = GitHubMCPConfig(
    github_token="your-github-token",
    server_port=9127,  # Port to run the GitHub MCP Server on
    enabled_toolsets=["repos", "issues", "pull_requests", "users"],
    use_docker=True,  # Whether to use Docker
    github_host=None,  # GitHub Enterprise Server hostname (if any)
    dynamic_toolsets=False  # Whether to enable dynamic toolsets
)
```

## PR Hook

The integration includes a run hook that automatically creates pull requests when SWE-agent fixes an issue:

```python
from sweagent.run.hooks import GitHubMCPPRHook, GitHubMCPPRConfig

# Configure the PR hook
pr_hook_config = GitHubMCPPRConfig(
    github_token="your-github-token",
    create_draft_pr=True,  # Whether to create draft PRs
    include_trajectory=True  # Whether to include the agent's thought process
)

# Create the hook
pr_hook = GitHubMCPPRHook(pr_hook_config)

# Add the hook to your agent
agent.add_hook(pr_hook)
```

## Usage Example

```python
from sweagent.integrations.github_mcp import (
    GitHubMCPClient,
    GitHubMCPConfig,
    start_github_mcp_server,
    stop_github_mcp_server
)

# Create a configuration
config = GitHubMCPConfig(
    github_token="your-github-token",
    enabled_toolsets=["repos", "issues", "pull_requests", "users"]
)

# Start the GitHub MCP Server
if start_github_mcp_server(config):
    # Create a client
    client = GitHubMCPClient(config)
    
    # Use the client to interact with GitHub
    user = client.get_me()
    print(f"Authenticated as: {user['login']}")
    
    # Create a pull request
    pr = client.create_pull_request(
        owner="owner",
        repo="repo",
        title="Fix issue",
        head="feature-branch",
        base="main",
        body="This PR fixes an issue"
    )
    
    print(f"Created PR: {pr['html_url']}")
    
    # Stop the GitHub MCP Server when done
    stop_github_mcp_server()
```

## Testing

The integration includes a mock server for testing without Docker:

```python
# Set environment variable to use mock server
import os
os.environ["USE_MOCK_SERVER"] = "true"

# Then use the integration as normal
```

## Troubleshooting

If you encounter issues with the GitHub MCP Server:

1. Check if Docker is installed and running
2. Verify your GitHub token has the necessary permissions
3. Try using the mock server for testing
4. Check the logs for error messages

For more information on GitHub MCP, visit the [GitHub MCP Server repository](https://github.com/github/github-mcp-server).