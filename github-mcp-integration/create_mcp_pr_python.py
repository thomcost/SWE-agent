#!/usr/bin/env python3
"""
Create a PR using GitHub MCP Server.

This script creates a pull request using either the GitHub MCP Server (running in Docker)
or the mock GitHub MCP Server (Python implementation). It handles the entire process
including getting repository information, creating a branch if needed, updating a file,
and creating the pull request.
"""

import os
import sys
import time
import json
import logging
import subprocess
import argparse
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-pr-creator")

# Default configuration
DEFAULT_PORT = 7444
DEFAULT_REPO_OWNER = "thomcost"
DEFAULT_REPO_NAME = "mcp-test-repo"
DEFAULT_FILE_PATH = "test-file.md"
DEFAULT_FILE_CONTENT = """# Test File

This file has been fixed using the GitHub MCP Server!

The issue is now resolved using the GitHub MCP integration.
"""


class GitHubMCPClient:
    """Client for interacting with GitHub MCP Server."""
    
    def __init__(self, port: int = DEFAULT_PORT):
        """Initialize the GitHub MCP client.
        
        Args:
            port: The port where the MCP server is running.
        """
        self.base_url = f"http://localhost:{port}"
        
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema information from the MCP server."""
        url = f"{self.base_url}/mcp/v1/schema"
        logger.info(f"Getting schema from {url}")
        
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Failed to get schema: {response.status_code}")
                return {}
            
            return response.json()
        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            return {}
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a GitHub MCP tool.
        
        Args:
            tool_name: The name of the tool to call.
            params: The parameters to pass to the tool.
            
        Returns:
            The response from the tool.
        """
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
                    if response.status_code == 200:
                        result = response.json()
                        logger.debug(f"Response: {result}")
                        return result
                    else:
                        error_message = f"GitHub MCP tool call failed: {response.status_code}"
                        logger.error(f"{error_message}: {response.text}")
                        if attempt < 2:
                            logger.warning(f"Retrying ({attempt+1}/3)...")
                            time.sleep(1)
                        else:
                            raise Exception(error_message)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < 2:
                        logger.warning(f"Connection issue calling {tool_name}, retrying... (attempt {attempt+1}/3): {e}")
                        time.sleep(1)
                    else:
                        raise
            
            raise Exception(f"Failed to call {tool_name} after 3 attempts")
            
        except Exception as e:
            logger.error(f"Error calling GitHub MCP tool {tool_name}: {str(e)}")
            raise
    
    def get_authenticated_user(self) -> Dict[str, Any]:
        """Get information about the authenticated user."""
        return self.call_tool("get_authenticated_user", {})
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information.
        
        Args:
            owner: The repository owner.
            repo: The repository name.
            
        Returns:
            Repository information.
        """
        return self.call_tool("get_repo", {
            "owner": owner,
            "repo": repo
        })
    
    def get_branch(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        """Get branch information.
        
        Args:
            owner: The repository owner.
            repo: The repository name.
            branch: The branch name.
            
        Returns:
            Branch information.
        """
        return self.call_tool("get_branch", {
            "owner": owner,
            "repo": repo,
            "branch": branch
        })
    
    def create_branch(self, owner: str, repo: str, branch: str, sha: str) -> Dict[str, Any]:
        """Create a new branch.
        
        Args:
            owner: The repository owner.
            repo: The repository name.
            branch: The new branch name.
            sha: The SHA to create the branch from.
            
        Returns:
            Branch creation result.
        """
        return self.call_tool("create_branch", {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "sha": sha
        })
    
    def create_or_update_file(self, owner: str, repo: str, path: str, 
                              message: str, content: str, branch: str) -> Dict[str, Any]:
        """Create or update a file.
        
        Args:
            owner: The repository owner.
            repo: The repository name.
            path: The file path.
            message: The commit message.
            content: The file content.
            branch: The branch name.
            
        Returns:
            File creation/update result.
        """
        return self.call_tool("create_or_update_file", {
            "owner": owner,
            "repo": repo,
            "path": path,
            "message": message,
            "content": content,
            "branch": branch
        })
    
    def create_pull_request(self, owner: str, repo: str, title: str, 
                            body: str, head: str, base: str, 
                            draft: bool = False) -> Dict[str, Any]:
        """Create a pull request.
        
        Args:
            owner: The repository owner.
            repo: The repository name.
            title: The PR title.
            body: The PR body.
            head: The head branch.
            base: The base branch.
            draft: Whether to create a draft PR.
            
        Returns:
            Pull request creation result.
        """
        return self.call_tool("create_pull_request", {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": draft
        })


def start_mock_server(port: int = DEFAULT_PORT) -> Tuple[bool, Optional[subprocess.Popen]]:
    """Start the mock GitHub MCP server.
    
    Args:
        port: The port to run the server on.
        
    Returns:
        A tuple of (success, process). If success is False, process will be None.
    """
    logger.info(f"Starting mock GitHub MCP server on port {port}...")
    
    # Get the path to the mock server script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mock_script_path = os.path.join(script_dir, "mock_github_mcp_server.py")
    
    if not os.path.exists(mock_script_path):
        logger.error(f"Mock server script not found at {mock_script_path}")
        return False, None
    
    # Start the mock server
    env = os.environ.copy()
    if "GITHUB_PERSONAL_ACCESS_TOKEN" not in env and "GITHUB_TOKEN" in env:
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = env["GITHUB_TOKEN"]
    
    try:
        cmd = [sys.executable, mock_script_path, "--port", str(port)]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        logger.info("Waiting for mock server to start...")
        for _ in range(10):
            try:
                response = requests.get(f"http://localhost:{port}/mcp/v1/schema", timeout=2)
                if response.status_code == 200:
                    logger.info("Mock GitHub MCP server started successfully")
                    return True, process
            except:
                pass
            time.sleep(1)
        
        logger.error("Failed to start mock GitHub MCP server")
        return False, None
        
    except Exception as e:
        logger.error(f"Error starting mock GitHub MCP server: {str(e)}")
        return False, None


def start_docker_server(token: str, port: int = DEFAULT_PORT) -> Tuple[bool, Optional[str]]:
    """Start the GitHub MCP server using Docker.
    
    Args:
        token: The GitHub personal access token.
        port: The port to run the server on.
        
    Returns:
        A tuple of (success, container_id). If success is False, container_id will be None.
    """
    logger.info(f"Starting GitHub MCP server using Docker on port {port}...")
    
    # Create a unique container name
    container_name = f"github-mcp-server-{int(time.time())}"
    
    try:
        # Pull the image
        logger.info("Pulling GitHub MCP server image...")
        subprocess.run(["docker", "pull", "ghcr.io/github/github-mcp-server"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Start the container
        logger.info(f"Starting container {container_name}...")
        result = subprocess.run(
            ["docker", "run", "-d", "--rm", "--name", container_name,
             "-p", f"{port}:7444", 
             "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={token}",
             "-e", "GITHUB_TOOLSETS=all",
             "ghcr.io/github/github-mcp-server"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        container_id = result.stdout.strip()
        logger.info(f"Container started with ID: {container_id}")
        
        # Wait for server to start
        logger.info("Waiting for server to start...")
        for _ in range(10):
            try:
                response = requests.get(f"http://localhost:{port}/mcp/v1/schema", timeout=2)
                if response.status_code == 200:
                    logger.info("GitHub MCP server started successfully")
                    return True, container_name
            except:
                pass
            time.sleep(1)
        
        # If we get here, the server didn't start properly
        logger.error("Failed to start GitHub MCP server")
        subprocess.run(["docker", "stop", container_name], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return False, None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Docker command: {e.stderr}")
        return False, None
    except Exception as e:
        logger.error(f"Error starting GitHub MCP server: {str(e)}")
        return False, None


def create_pr(args: argparse.Namespace) -> bool:
    """Create a pull request using GitHub MCP server.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if the PR was created successfully, False otherwise.
    """
    # Get GitHub token
    github_token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not github_token and not args.use_mock:
        logger.error("GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment variable not set")
        return False
    
    # Determine server type and start it
    server_process = None
    container_name = None
    
    try:
        if args.use_mock:
            logger.info("Using mock GitHub MCP server")
            success, server_process = start_mock_server(args.port)
            if not success:
                return False
        else:
            logger.info("Using real GitHub MCP server with Docker")
            success, container_name = start_docker_server(github_token, args.port)
            if not success:
                return False
        
        # Create client
        client = GitHubMCPClient(port=args.port)
        
        # Get authenticated user info
        if not args.use_mock:
            try:
                user = client.get_authenticated_user()
                logger.info(f"Authenticated as: {user.get('login', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Failed to get user info: {e}")
        
        # Get repository info
        logger.info(f"Getting repository info for {args.owner}/{args.repo}...")
        try:
            repo_info = client.get_repo(args.owner, args.repo)
            default_branch = repo_info.get("default_branch", "main")
            logger.info(f"Default branch: {default_branch}")
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return False
        
        # Create a branch if specified
        if args.create_branch:
            # Get branch SHA
            logger.info(f"Getting branch info for {args.base or default_branch}...")
            try:
                branch_info = client.get_branch(args.owner, args.repo, args.base or default_branch)
                branch_sha = branch_info.get("commit", {}).get("sha")
                if not branch_sha:
                    logger.error("Failed to get branch SHA")
                    return False
                
                logger.info(f"Base branch SHA: {branch_sha}")
                
                # Create a new branch
                branch_name = args.head or f"fix-issue-mcp-{int(time.time())}"
                logger.info(f"Creating branch {branch_name}...")
                create_branch_result = client.create_branch(
                    args.owner, args.repo, branch_name, branch_sha
                )
                logger.info(f"Created branch: {branch_name}")
                
                # Update file if specified
                if args.file_path:
                    logger.info(f"Updating file {args.file_path}...")
                    file_content = args.file_content or DEFAULT_FILE_CONTENT
                    
                    update_result = client.create_or_update_file(
                        args.owner, args.repo, args.file_path,
                        f"Update {args.file_path} using GitHub MCP",
                        file_content, branch_name
                    )
                    logger.info("File updated successfully")
            except Exception as e:
                logger.error(f"Failed to create branch or update file: {e}")
                return False
        else:
            # Use existing branch
            branch_name = args.head
            if not branch_name:
                logger.error("Head branch name is required when not creating a new branch")
                return False
        
        # Create PR
        logger.info("Creating pull request...")
        pr_title = args.title or f"Fix issue using GitHub MCP Server"
        pr_body = args.body or "This PR fixes an issue by updating a file.\n\nCreated using the GitHub MCP Server."
        
        try:
            pr_result = client.create_pull_request(
                args.owner, args.repo, pr_title, pr_body,
                branch_name, args.base or default_branch,
                args.draft
            )
            
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
            
    finally:
        # Clean up
        if server_process:
            logger.info("Stopping mock GitHub MCP server...")
            server_process.terminate()
            server_process.wait(timeout=5)
        
        if container_name:
            logger.info(f"Stopping Docker container {container_name}...")
            try:
                subprocess.run(["docker", "stop", container_name], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except:
                pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a PR using GitHub MCP Server")
    parser.add_argument("--owner", default=DEFAULT_REPO_OWNER,
                        help=f"Repository owner (default: {DEFAULT_REPO_OWNER})")
    parser.add_argument("--repo", default=DEFAULT_REPO_NAME,
                        help=f"Repository name (default: {DEFAULT_REPO_NAME})")
    parser.add_argument("--title", help="PR title")
    parser.add_argument("--body", help="PR body")
    parser.add_argument("--head", help="Head branch (will be created if --create-branch is specified)")
    parser.add_argument("--base", help="Base branch (defaults to repository default branch)")
    parser.add_argument("--create-branch", action="store_true",
                        help="Create a new branch for the PR")
    parser.add_argument("--file-path", help="Path to the file to update (if creating a branch)")
    parser.add_argument("--file-content", help="Content for the file update (if creating a branch)")
    parser.add_argument("--draft", action="store_true", help="Create a draft PR")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Port for the MCP server (default: {DEFAULT_PORT})")
    parser.add_argument("--use-mock", action="store_true", default=True,
                        help="Use mock GitHub MCP server instead of Docker (default: True)")
    
    args = parser.parse_args()
    
    success = create_pr(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()