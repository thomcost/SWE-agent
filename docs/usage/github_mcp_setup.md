# Setting Up GitHub MCP Integration

This guide provides step-by-step instructions for setting up and testing the GitHub MCP integration for SWE-agent.

## Prerequisites

Before you can use the GitHub MCP integration, you need:

1. **Docker**: The GitHub MCP Server runs in a Docker container
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Ensure Docker is running and properly configured

2. **GitHub Personal Access Token (PAT)**:
   - Go to [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Grant the following permissions:
     - `repo` (Full control of private repositories)
     - `workflow` (Optional, for GitHub Actions)
   - Copy the generated token

3. **Python Environment**:
   - Python 3.8 or later
   - Required packages: `requests`, `python-dotenv`

## Installation

1. **Set up a virtual environment** (recommended):

   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   
   # Install dependencies
   pip install requests python-dotenv
   ```

2. **Configure GitHub Token**:

   Create or update your `.env` file with your GitHub token:

   ```
   GITHUB_TOKEN=your_github_token_here
   ```

3. **Pull GitHub MCP Server Docker Image**:

   ```bash
   docker pull ghcr.io/github/github-mcp-server
   ```

## Basic Testing

To test that the GitHub MCP integration is working correctly, you can use the standalone test script:

```bash
python test_standalone_github_mcp.py
```

This script:
1. Starts the GitHub MCP Server in a Docker container
2. Tests basic GitHub API operations:
   - Getting the authenticated user
   - Listing branches in a repository
   - Getting the contents of a file
3. Stops the server

If everything is working correctly, you should see output similar to:

```
INFO - Starting GitHub MCP Server using Docker...
INFO - GitHub MCP Server started successfully
INFO - Testing get_me...
INFO - Authenticated as: your-github-username
INFO - Testing list_branches...
INFO - Found 3 branches
INFO - Testing get_file_contents...
INFO - README content length: 12345 characters
INFO - All tests passed!
INFO - GitHub MCP Server stopped successfully
```

## Testing PR Creation

To test the GitHub MCP PR functionality, you need:

1. **A repository where you have write access**
2. **An open issue in that repository**

Update your `.env` file with the repository details:

```
GITHUB_TOKEN=your_github_token_here
TEST_REPO_OWNER=your-github-username
TEST_REPO_NAME=your-test-repo-name
TEST_ISSUE_NUMBER=123
```

Then run the PR test script:

```bash
python test_github_mcp_pr.py
```

This script:
1. Starts the GitHub MCP Server
2. Creates a branch in your repository
3. Makes changes to files
4. Creates a pull request that references the issue
5. Stops the server

## Troubleshooting

### Docker Issues

If you encounter Docker-related issues:

1. **Docker not found**:
   - Make sure Docker is installed and in your PATH
   - Try running `docker --version` to verify

2. **Permission errors**:
   - On Linux, you may need to add your user to the docker group:
     ```bash
     sudo usermod -aG docker $USER
     # Then log out and back in
     ```

3. **Image pull issues**:
   - If you can't pull the image, try logging out and back in:
     ```bash
     docker logout ghcr.io
     ```

### Authentication Issues

If you encounter authentication issues:

1. **Invalid token**:
   - Verify your token has the necessary permissions
   - Generate a new token if needed

2. **Token not recognized**:
   - Check that the token is correctly set in the environment
   - Try setting it directly in the code for testing

### API Issues

If you encounter API-related issues:

1. **Rate limiting**:
   - GitHub has rate limits that may affect your usage
   - Check the error response for details

2. **Permission errors**:
   - Ensure your token has the necessary permissions for the operations

## Using with SWE-agent

To use the GitHub MCP integration with SWE-agent, use the `github_mcp.yaml` configuration:

```bash
# Activate your environment
source .venv/bin/activate

# Run SWE-agent with GitHub MCP configuration
python -m sweagent.run.run_single \
  --github_url https://github.com/username/repo/issues/123 \
  --config config/github_mcp.yaml
```

## Resources

- [GitHub MCP Server Documentation](https://github.com/github/github-mcp-server)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Docker Documentation](https://docs.docker.com/)