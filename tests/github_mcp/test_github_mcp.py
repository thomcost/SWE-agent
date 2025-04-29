#!/usr/bin/env python3
"""
Test script for GitHub MCP integration with SWE-agent.

This script tests the GitHub MCP integration by:
1. Starting the GitHub MCP Server
2. Testing basic GitHub API operations
3. Stopping the server

Requirements:
- Docker installed (for running GitHub MCP Server)
- GITHUB_TOKEN environment variable set with a valid token
"""

import os
import time
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-test")

# Load environment variables from .env file
load_dotenv()

# Import GitHub MCP modules
from sweagent.integrations.github_mcp import (
    GitHubMCPClient,
    GitHubMCPConfig,
    start_github_mcp_server,
    stop_github_mcp_server
)


def test_server_startup():
    """Test starting and stopping the GitHub MCP Server."""
    logger.info("Testing GitHub MCP Server startup...")
    
    # Create config
    config = GitHubMCPConfig(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        enabled_toolsets=["repos", "issues", "users", "pull_requests"],
        use_docker=True
    )
    
    # Start server
    success = start_github_mcp_server(config)
    assert success, "Failed to start GitHub MCP Server"
    logger.info("GitHub MCP Server started successfully")
    
    # Give server time to initialize
    time.sleep(2)
    
    # Stop server
    success = stop_github_mcp_server()
    assert success, "Failed to stop GitHub MCP Server"
    logger.info("GitHub MCP Server stopped successfully")


def test_github_client():
    """Test GitHub MCP client functionality."""
    logger.info("Testing GitHub MCP client...")
    
    # Create config
    config = GitHubMCPConfig(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        enabled_toolsets=["repos", "users", "issues", "pull_requests"],
        use_docker=True
    )
    
    # Start server
    success = start_github_mcp_server(config)
    assert success, "Failed to start GitHub MCP Server"
    logger.info("GitHub MCP Server started successfully")
    
    # Give server time to initialize
    time.sleep(2)
    
    try:
        # Create client
        client = GitHubMCPClient(config)
        
        # Test getting authenticated user
        logger.info("Getting authenticated user...")
        user = client.get_me()
        logger.info(f"Authenticated user: {user.get('login', 'Unknown')}")
        
        # Test listing a public repository
        repo_owner = "SWE-agent"
        repo_name = "SWE-agent"
        
        logger.info(f"Listing branches for {repo_owner}/{repo_name}...")
        branches = client.list_branches(repo_owner, repo_name)
        logger.info(f"Found {len(branches.get('items', []))} branches")
        
        # Test getting repository content
        readme_path = "README.md"
        logger.info(f"Getting content of {readme_path}...")
        readme = client.get_file_contents(repo_owner, repo_name, readme_path)
        content_preview = readme.get('content', "")[:100] + "..." if readme.get('content') else "No content"
        logger.info(f"README content preview: {content_preview}")
        
    except Exception as e:
        logger.error(f"Error testing GitHub MCP client: {e}")
        raise
    finally:
        # Stop server
        stop_github_mcp_server()
        logger.info("GitHub MCP Server stopped")


def main():
    """Run all tests."""
    logger.info("Starting GitHub MCP integration tests...")
    
    # Check if GitHub token is set
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable not set. Please set it before running tests.")
        return 1
    
    # Check if Docker is installed
    try:
        import subprocess
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except Exception:
        logger.error("Docker not found. Please install Docker before running tests.")
        return 1
    
    try:
        # Run tests
        test_server_startup()
        test_github_client()
        
        logger.info("All tests completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())