#!/usr/bin/env python3
"""
Create a PR using the mock GitHub MCP server.

This script replicates the functionality of create_mcp_pr.sh but uses the mock
GitHub Model Context Protocol (MCP) server instead of Docker, avoiding permission issues.
"""

import os
import sys
import time
import json
import logging
import subprocess
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-pr-creator")

# Configuration
REPO_OWNER = "thomcost"
REPO_NAME = "mcp-test-repo"
BRANCH_NAME = f"fix-issue-1-mock-mcp-{int(time.time())}"
MCP_PORT = 7444

# Set environment variable to use mock server
os.environ["USE_MOCK_SERVER"] = "true"


class GitHubMCPClient:
    """Client for interacting with GitHub MCP Server."""
    
    def __init__(self, port: int = 7444):
        self.base_url = f"http://localhost:{port}"
        
    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a GitHub MCP tool."""
        url = f"{self.base_url}/mcp/v1/tools/{tool_name}"
        logger.info(f"Calling GitHub MCP tool: {tool_name}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request params: {params}")
        
        try:
            payload = {
                "arguments": params
            }
            
            # Add retry logic for better reliability
            for attempt in range(3):
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    if attempt < 2:
                        logger.warning(f"Connection issue calling {tool_name}, retrying... (attempt {attempt+1}/3)")
                        time.sleep(1)
                    else:
                        raise
            
            if response.status_code != 200:
                error_message = f"GitHub MCP tool call failed: {response.status_code}"
                logger.error(f"{error_message}: {response.text}")
                raise Exception(error_message)
            
            result = response.json()
            logger.debug(f"Response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error calling GitHub MCP tool {tool_name}: {str(e)}")
            raise


def ensure_mock_server_running():
    """Ensure the mock GitHub MCP server is running."""
    # Try to connect to the server
    logger.info("Checking if mock GitHub MCP server is running...")
    
    try:
        response = requests.get(f"http://localhost:{MCP_PORT}/mcp/v1/schema", timeout=2)
        if response.status_code == 200:
            logger.info("Mock GitHub MCP server is already running")
            return True
    except requests.RequestException:
        logger.info("Mock GitHub MCP server is not running, starting it")
    
    # Get the path to the mock server script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mock_script_path = os.path.join(script_dir, "mock_github_mcp_server.py")
    
    if not os.path.exists(mock_script_path):
        logger.error(f"Mock server script not found at {mock_script_path}")
        return False
    
    # Start the mock server
    env = os.environ.copy()
    if "GITHUB_PERSONAL_ACCESS_TOKEN" not in env and "GITHUB_TOKEN" in env:
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = env["GITHUB_TOKEN"]
    
    try:
        process = subprocess.Popen(
            [sys.executable, mock_script_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        logger.info("Waiting for mock server to start...")
        for _ in range(10):
            try:
                response = requests.get(f"http://localhost:{MCP_PORT}/mcp/v1/schema", timeout=2)
                if response.status_code == 200:
                    logger.info("Mock GitHub MCP server started successfully")
                    return True
            except:
                pass
            time.sleep(1)
        
        logger.error("Failed to start mock GitHub MCP server")
        return False
        
    except Exception as e:
        logger.error(f"Error starting mock GitHub MCP server: {str(e)}")
        return False


def create_pr():
    """Create a pull request using the mock GitHub MCP server."""
    # Ensure the mock server is running
    if not ensure_mock_server_running():
        logger.error("Cannot continue without a running mock GitHub MCP server")
        return False
    
    # Create client
    client = GitHubMCPClient(port=MCP_PORT)
    
    try:
        # Get default branch
        logger.info(f"Getting repository info for {REPO_OWNER}/{REPO_NAME}...")
        repo_info = client._call_tool("get_repo", {
            "owner": REPO_OWNER,
            "repo": REPO_NAME
        })
        
        default_branch = repo_info.get("default_branch", "main")
        logger.info(f"Default branch: {default_branch}")
        
        # Get branch SHA
        logger.info(f"Getting branch info for {default_branch}...")
        branch_info = client._call_tool("get_branch", {
            "owner": REPO_OWNER,
            "repo": REPO_NAME,
            "branch": default_branch
        })
        
        branch_sha = branch_info.get("commit", {}).get("sha")
        if not branch_sha:
            logger.error("Failed to get branch SHA")
            return False
        
        logger.info(f"Branch SHA: {branch_sha}")
        
        # Create a new branch
        logger.info(f"Creating branch {BRANCH_NAME}...")
        create_branch_result = client._call_tool("create_branch", {
            "owner": REPO_OWNER,
            "repo": REPO_NAME,
            "branch": BRANCH_NAME,
            "sha": branch_sha
        })
        
        logger.info(f"Created branch: {BRANCH_NAME}")
        
        # Update file
        logger.info("Updating test file...")
        file_content = "# Test File\n\nThis file has been fixed using the MOCK GitHub MCP Server!\n\nThe issue is now resolved using the mock MCP Server."
        
        update_result = client._call_tool("create_or_update_file", {
            "owner": REPO_OWNER,
            "repo": REPO_NAME,
            "path": "test-file.md",
            "message": "Fix issue #1 using mock GitHub MCP",
            "content": file_content,
            "branch": BRANCH_NAME
        })
        
        logger.info("File updated successfully")
        
        # Create PR
        logger.info("Creating pull request...")
        pr_body = "This PR fixes issue #1 by updating the test file.\n\nCreated using the MOCK GitHub MCP Server.\n\nCloses #1"
        
        pr_result = client._call_tool("create_pull_request", {
            "owner": REPO_OWNER,
            "repo": REPO_NAME,
            "title": "Fix issue #1 using MOCK GitHub MCP Server",
            "head": BRANCH_NAME,
            "base": default_branch,
            "body": pr_body
        })
        
        pr_number = pr_result.get("number")
        pr_url = pr_result.get("html_url")
        
        if not pr_number:
            logger.error("Failed to create PR")
            return False
        
        logger.info(f"Created PR #{pr_number}: {pr_url}")
        logger.info("Pull request created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating PR: {str(e)}")
        return False


if __name__ == "__main__":
    # Get GitHub token
    github_token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.warning("GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment variable not set")
        logger.warning("The mock server will work without a token, but authentication will fail")
    
    success = create_pr()
    sys.exit(0 if success else 1)