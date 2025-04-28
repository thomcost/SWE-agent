# GitHub MCP Server Integration

This directory contains tools and utilities for integrating with GitHub's Machine Callable Protocol (MCP) Server. These tools enable the SWE-agent to create pull requests and issues programmatically.

## Components

### Mock MCP Server

- `mock_github_mcp_server.py` - A Python implementation of the GitHub MCP Server that can be used for development and testing without requiring Docker.

### PR Creation Tools

- `create_pr_with_mock.py` - Creates pull requests using the mock MCP server
- `create_mcp_pr.sh` - Bash script to create PRs using the Docker-based GitHub MCP Server
- `create_mcp_pr_python.py` - Python script that can use either the real or mock MCP server for PR creation

### Issue Creation Tools

- `mcp_issue_creator.py` - Python script to create GitHub issues using the MCP server
- `working_mcp_issues.sh` - Shell script for issue creation using JSON-RPC communication
- `final_mcp_solution.py` - Recommended approach for reliable issue creation

### Utility Scripts

- `run_mock_server.sh` - Starts the mock MCP server
- `test_tools.sh` - Tests various MCP server commands
- `test_standalone_github_mcp.py` - Comprehensive testing script for MCP functionality

## Usage

### Using the Mock Server

The mock server provides a reliable simulation of the GitHub MCP Server:

```bash
# Start the mock server
./run_mock_server.sh

# Create a PR using the mock server
python create_pr_with_mock.py
```

### Using the Docker-based MCP Server

For integrating with the actual GitHub MCP Server:

```bash
# Make sure your GitHub token is set
export GITHUB_TOKEN=$(gh auth token)

# Create a PR using the official Docker container
./create_mcp_pr.sh
```

## Recommended Approach

After extensive testing, we recommend using the following approaches for production environments:

1. GitHub CLI (`gh`) for direct issue/PR creation
2. GitHub REST API for programmatic access
3. PyGithub library for Python-based integration
4. Our mock server for development and testing

The mock server approach is more reliable and avoids the complexities of Docker and authentication issues.