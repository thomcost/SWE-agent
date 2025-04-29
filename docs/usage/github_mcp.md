# GitHub MCP Integration

SWE-agent supports integration with [GitHub MCP Server](https://github.com/github/github-mcp-server), which provides access to GitHub's features through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction).

## Overview

GitHub MCP Server is an official GitHub tool that provides standardized access to GitHub's APIs. This integration allows SWE-agent to:

1. Access GitHub repositories, issues, pull requests, and other features
2. Create and manage branches
3. Submit changes as pull requests
4. Interact with code scanning and security alerts

## Requirements

To use the GitHub MCP integration, you need:

1. A GitHub Personal Access Token with appropriate permissions
2. Either Docker installed (recommended) or the GitHub MCP Server binary

## Installation

The GitHub MCP integration is included in SWE-agent by default. If you're using SWE-agent from source, make sure to install the dependencies:

```bash
pip install -r sweagent/integrations/github_mcp/requirements.txt
```

## Configuration

### Environment Variables

The integration uses the following environment variables:

- `GITHUB_TOKEN`: Your GitHub Personal Access Token (required)
- `GITHUB_HOST`: GitHub Enterprise Server hostname (optional, for GitHub Enterprise)

### Configuration Options

When using the GitHub MCP PR hook, you can configure the following options:

```yaml
run:
  hooks:
    - type: github_mcp_pr
      config:
        skip_if_commits_reference_issue: true
        use_docker: true
        server_path: null
        docker_image: "ghcr.io/github/github-mcp-server"
        github_host: null
        enabled_toolsets: ["repos", "issues", "pull_requests"]
```

## Usage

### Using the GitHub MCP PR Hook

To use the GitHub MCP PR hook for automatic pull request creation, add it to your run configuration:

```yaml
run:
  hooks:
    - type: github_mcp_pr
```

The hook will automatically create pull requests when SWE-agent successfully fixes an issue.

### Using the GitHubMCPClient Directly

You can also use the GitHub MCP client directly in your code:

```python
from sweagent.integrations.github_mcp import GitHubMCPClient, GitHubMCPConfig

# Create configuration
config = GitHubMCPConfig(
    github_token=os.environ["GITHUB_TOKEN"],
    enabled_toolsets=["repos", "issues", "pull_requests"]
)

# Initialize client
client = GitHubMCPClient(config)

# Use the client
issue = client.get_issue("owner", "repo", 123)
print(f"Issue title: {issue['title']}")
```

## Toolsets

GitHub MCP Server supports various toolsets that can be enabled or disabled:

- `repos`: Repository-related tools (file operations, branches, commits)
- `issues`: Issue-related tools (create, read, update, comment)
- `users`: User-related tools
- `pull_requests`: Pull request operations (create, merge, review)
- `code_security`: Code scanning alerts and security features
- `experiments`: Experimental features (not considered stable)

By default, the GitHub MCP PR hook enables only the necessary toolsets for PR creation (`repos`, `issues`, `pull_requests`).

## Comparing with Standard GitHub Integration

SWE-agent includes two ways to integrate with GitHub:

1. **Standard GitHub Integration**: Uses the traditional GitHub REST API through the `ghapi` library
2. **GitHub MCP Integration**: Uses the GitHub MCP Server for a more standardized, structured approach

### Advantages of GitHub MCP

- **Standardized Interface**: Uses the Model Context Protocol for consistent access
- **Granular Tools**: More fine-grained access to GitHub features
- **Official Support**: Maintained by GitHub
- **Enhanced Security**: Containerized execution for better isolation

### Choosing an Integration

- **Use GitHub MCP Integration** when you need more structured access to GitHub features or want to leverage the MCP ecosystem
- **Use Standard GitHub Integration** for simpler scenarios or when you want to avoid Docker dependencies

## Troubleshooting

### Docker Issues

If you encounter issues with Docker:

1. Make sure Docker is installed and running
2. Try pulling the image manually: `docker pull ghcr.io/github/github-mcp-server`
3. Check for any authentication issues with GitHub Container Registry

### Authentication Issues

If you see authentication errors:

1. Verify your GitHub token has the necessary permissions
2. Check that the token is correctly set in the environment
3. Ensure the token hasn't expired

### Server Connection Issues

If the client can't connect to the server:

1. Check that the server has started successfully
2. Verify the port is not blocked by a firewall
3. Check for error messages in the logs

## Resources

- [GitHub MCP Server Repository](https://github.com/github/github-mcp-server)
- [Model Context Protocol Documentation](https://modelcontextprotocol.io/introduction)