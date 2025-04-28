# GitHub MCP Server Integration for SWE-agent

This document summarizes our work on integrating the SWE-agent with GitHub's Model Context Protocol (MCP) Server for creating pull requests and issues.

## Overview

We explored multiple approaches to integrate with the GitHub MCP Server, including:

1. Docker-based GitHub MCP Server (official approach)
2. Mock GitHub MCP Server (custom implementation)
3. Direct GitHub API integration (fallback option)

The GitHub MCP integration allows SWE-agent to interact with GitHub repositories, issues, pull requests, and other GitHub features using the GitHub MCP Server.

## Key Components

All integration code has been organized in the `github-mcp-integration/` directory:

- **Mock Server:** `mock_github_mcp_server.py` - Python implementation of the MCP Server
- **PR Creation:** Scripts for creating PRs using both real and mock servers
- **Issue Creation:** Tools for creating GitHub issues
- **Documentation:** Integration guide in `docs/github_mcp/integration_guide.md`

## Testing the Integration

### 1. Using the Mock Server (No Docker Required)

To test the integration using the mock server:

```bash
# Start the mock server
./github-mcp-integration/run_mock_server.sh

# Create a PR using the mock server
python github-mcp-integration/create_pr_with_mock.py
```

This uses a mock GitHub MCP Server that doesn't require Docker or a real GitHub repository.

### 2. Using the Real GitHub MCP Server (Docker Required)

To test the integration with a real GitHub repository:

```bash
# Set your GitHub token
export GITHUB_TOKEN=$(gh auth token)

# Run the PR creation script
./github-mcp-integration/create_mcp_pr.sh
```

This will start the GitHub MCP Server using Docker and create a PR in your test repository.

## Using the Integration in Your Code

### Basic Usage

```python
from sweagent.integrations.github_mcp import (
    GitHubMCPClient,
    GitHubMCPConfig,
    start_github_mcp_server,
    stop_github_mcp_server
)

# Configure the integration
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

### Using the PR Hook

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

## Challenges & Solutions

### Docker in WSL2

We encountered several challenges with Docker in WSL2:

- **Permission Issues:** Fixed with `chmod 666 /var/run/docker.sock`
- **Networking:** Addressed with host networking and proper port mapping
- **Authentication:** Resolved by using GitHub CLI for token extraction

### MCP Server Communication

The GitHub MCP Server communication protocol was challenging:

- Uses JSON-RPC over stdio (not HTTP as initially expected)
- Requires specific format with `jsonrpc`, `id`, and `method` fields
- Inconsistent behavior with method naming and parameters

## Available Methods

The `GitHubMCPClient` class provides the following methods:

### Repository Operations

- `list_branches(owner, repo)`: List branches in a repository
- `get_branch(owner, repo, branch)`: Get information about a branch
- `create_branch(owner, repo, branch, sha)`: Create a new branch

### File Operations

- `get_file_contents(owner, repo, path, ref)`: Get file contents
- `create_or_update_file(owner, repo, path, message, content, branch, sha)`: Create or update a file

### Issue Operations

- `get_issue(owner, repo, issue_number)`: Get information about an issue
- `create_issue(owner, repo, title, body, assignees, labels)`: Create a new issue
- `add_issue_comment(owner, repo, issue_number, body)`: Add a comment to an issue

### Pull Request Operations

- `create_pull_request(owner, repo, title, head, base, body, draft)`: Create a new pull request
- `get_pull_request(owner, repo, pull_number)`: Get information about a pull request
- `merge_pull_request(owner, repo, pull_number, commit_title, commit_message, merge_method)`: Merge a pull request

## Recommended Approach

After extensive testing, we recommend:

1. **For Development & Testing:**
   - Use our mock MCP server implementation
   - Provides consistent behavior across environments
   - No Docker dependencies

2. **For Production:**
   - GitHub CLI (`gh`) for direct issue/PR creation
   - GitHub REST API for programmatic access
   - PyGithub library for Python integrations

## Troubleshooting

If you encounter issues with the GitHub MCP integration:

1. Check if Docker is installed and running (for real GitHub MCP Server)
2. Verify your GitHub token has the necessary permissions
3. Try using the mock server for testing (no Docker required)
4. Check the logs for error messages

## Conclusion

While we successfully implemented a working integration with both the real and mock GitHub MCP Servers, we found that the mock server approach provides a more reliable and consistent solution for the SWE-agent's needs.

The code has been organized and documented for easy maintenance and future development.