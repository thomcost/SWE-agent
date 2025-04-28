# GitHub MCP Server Integration Guide

This guide describes how to integrate the SWE-agent with GitHub's Model Context Protocol (MCP) Server for creating pull requests and issues.

## Overview

GitHub MCP Server is a tool that provides a standardized API for interacting with GitHub repositories. The SWE-agent uses this to automate PR and issue creation.

## Setup Options

There are two main approaches for integration:

### 1. Docker-based Official GitHub MCP Server

This approach uses the official GitHub MCP Server Docker container:

```bash
# Pull the official Docker image
docker pull ghcr.io/github/github-mcp-server

# Run the container with GitHub token
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN \
  -e GITHUB_TOOLSETS=all \
  ghcr.io/github/github-mcp-server
```

**Considerations:**
- Requires Docker setup
- Needs GitHub Personal Access Token
- Communication via JSON-RPC over stdio
- May encounter networking/permission issues in WSL environments

### 2. Mock MCP Server (Recommended for Development)

This approach uses our Python-based mock implementation:

```bash
# Start the mock server
python mock_github_mcp_server.py

# Or use the convenience script
./run_mock_server.sh
```

**Advantages:**
- No Docker required
- Works consistently across environments
- Easy to debug and extend
- Provides the same API interface

## Technical Notes

### Communication Protocol

The GitHub MCP Server uses a JSON-RPC protocol over stdio:

```json
{
  "jsonrpc": "2.0", 
  "id": "1", 
  "method": "invoke", 
  "params": {
    "name": "create_issue",
    "arguments": {
      "owner": "repo-owner",
      "repo": "repo-name",
      "title": "Issue Title",
      "body": "Issue Body"
    }
  }
}
```

### Error Handling

Common errors include:
- "Method not found" - Incorrect method name
- "Parse error" - Invalid JSON format
- "Invalid JSON-RPC version" - Incorrect protocol version

## Production Recommendations

For the most reliable GitHub integration in production environments:

1. **GitHub CLI** (`gh`):
   ```bash
   gh issue create --title "Issue Title" --body "Issue Body"
   ```

2. **GitHub REST API**:
   ```bash
   curl -X POST https://api.github.com/repos/owner/repo/issues \
     -H "Authorization: token $GITHUB_TOKEN" \
     -d '{"title":"Issue Title","body":"Issue Body"}'
   ```

3. **PyGithub Library**:
   ```python
   from github import Github
   g = Github(token)
   repo = g.get_repo("owner/repo")
   repo.create_issue(title="Issue Title", body="Issue Body")
   ```

## Troubleshooting

### Docker Issues in WSL

If encountering permission errors with Docker in WSL:

```bash
# Fix Docker socket permissions
wsl.exe -d Ubuntu -u root chmod 666 /var/run/docker.sock

# Verify Docker is working
docker run hello-world
```

### Authentication Issues

Make sure your GitHub token has the necessary permissions:

```bash
# Set token for current session
export GITHUB_TOKEN=$(gh auth token)

# Verify token with GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Path Forward

For new SWE-agent implementations, we recommend:

1. Use the mock server for development and testing
2. Implement fallback mechanisms to direct GitHub API if needed
3. Consider using GitHub CLI or PyGithub for production deployments