# GitHub MCP Test Repository Guide

This guide provides information about the [mcp-test-repo](https://github.com/thomcost/mcp-test-repo) and how it's used for testing the GitHub Model Context Protocol (MCP) integration with SWE-agent.

## Overview

The `mcp-test-repo` is a dedicated repository for testing GitHub MCP integration. It provides a controlled environment to test:

- Issue creation via MCP
- Pull request creation via MCP
- End-to-end MCP workflows

## Repository Setup

### Public Repository

The repository is publicly available at: https://github.com/thomcost/mcp-test-repo

### Local Clone

A local clone of this repository is maintained in the SWE-agent project at:

```
/test-repo/mcp-test-repo/
```

This allows for local testing and development of the MCP integration.

## Using the Test Repository

### For Testing MCP Issue Creation

```python
# Example code for creating an issue using the test repository
from sweagent.integrations.github_mcp import client

mcp_client = client.GitHubMCPClient(token="YOUR_GITHUB_TOKEN")
issue = mcp_client.create_issue(
    owner="thomcost",
    repo="mcp-test-repo",
    title="Test Issue from MCP",
    body="This is a test issue created using the GitHub MCP integration."
)
print(f"Created issue #{issue.number}: {issue.html_url}")
```

### For Testing MCP PR Creation

```python
# Example code for creating a PR using the test repository
from sweagent.integrations.github_mcp import client

mcp_client = client.GitHubMCPClient(token="YOUR_GITHUB_TOKEN")
pr = mcp_client.create_pull_request(
    owner="thomcost",
    repo="mcp-test-repo",
    title="Fix test issue",
    body="This PR fixes the test issue.",
    head="fix-branch",
    base="main"
)
print(f"Created PR #{pr.number}: {pr.html_url}")
```

## Testing Workflow

A typical testing workflow using this repository:

1. Create a test issue via MCP
2. Create a branch to fix the issue
3. Make changes to resolve the issue
4. Create a PR via MCP that references the issue
5. Verify the PR correctly references and can close the issue

## Test Repository Structure

The repository contains:

- `README.md` - Documentation about the repository
- `test-file.md` - A sample file used for testing changes
- `.github/` - GitHub configuration files (PR template, issue templates)

## Integration with SWE-agent

The test repository is referenced in:

- `tools/github_mcp/` - MCP tools that interact with the repository
- `examples/github_mcp/` - Example scripts that demonstrate MCP usage
- `tests/github_mcp/` - Test scripts that verify MCP functionality

## Maintenance

Periodically, you may want to:

1. Close old PRs and issues that were created for testing
2. Reset the repository to its initial state
3. Update the repository configuration as needed for new test cases

## Security Considerations

When testing with this repository:

1. Use testing GitHub tokens with limited permissions
2. Do not store sensitive information in the repository
3. Remember this is a public repository, so all content is visible