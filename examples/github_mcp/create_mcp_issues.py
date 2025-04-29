#!/usr/bin/env python3
"""
Create GitHub issues using GitHub MCP Server.

This script creates issues in a GitHub repository using either the GitHub MCP Server 
(running in Docker) or the mock GitHub MCP Server (Python implementation).
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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-issue-creator")

# Default configuration
DEFAULT_PORT = 7444
DEFAULT_REPO_OWNER = "thomcost"
DEFAULT_REPO_NAME = "mcp-test-repo"


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
    
    def create_issue(self, owner: str, repo: str, title: str, body: str, 
                    labels: Optional[List[str]] = None, 
                    assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create an issue in a repository.
        
        Args:
            owner: The repository owner.
            repo: The repository name.
            title: The issue title.
            body: The issue body.
            labels: Optional list of labels to add to the issue.
            assignees: Optional list of users to assign to the issue.
            
        Returns:
            Issue creation result.
        """
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body
        }
        
        if labels:
            params["labels"] = labels
            
        if assignees:
            params["assignees"] = assignees
            
        return self.call_tool("create_issue", params)


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
        for attempt in range(20):  # More attempts with longer timeout
            try:
                response = requests.get(f"http://localhost:{port}/mcp/v1/schema", timeout=3)
                if response.status_code == 200:
                    logger.info("GitHub MCP server started successfully")
                    return True, container_name
            except Exception as e:
                logger.debug(f"Server not ready yet (attempt {attempt+1}/20): {e}")
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


def create_issues(args: argparse.Namespace) -> bool:
    """Create GitHub issues using MCP server.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if all issues were created successfully, False otherwise.
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
        
        # Check if the server has the create_issue tool
        schema = client.get_schema()
        tools = [tool.get("name") for tool in schema.get("tools", [])]
        if "create_issue" not in tools:
            logger.error("The MCP server does not support the 'create_issue' tool")
            return False
        
        # Get authenticated user info
        if not args.use_mock:
            try:
                user = client.get_authenticated_user()
                logger.info(f"Authenticated as: {user.get('login', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Failed to get user info: {e}")
        
        # Get repository info to verify it exists
        logger.info(f"Verifying repository {args.owner}/{args.repo}...")
        try:
            repo_info = client.get_repo(args.owner, args.repo)
            logger.info(f"Repository found: {repo_info.get('full_name')}")
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return False
        
        # Create issues
        successful_issues = []
        failed_issues = []
        
        # If no issues were specified, display help
        if not args.titles:
            logger.error("No issues specified. Use --title to specify at least one issue title.")
            return False
        
        # Create each issue
        for i, title in enumerate(args.titles):
            try:
                # Get body for this title if available, or use default
                body = args.bodies[i] if i < len(args.bodies) else "Created using GitHub MCP Server"
                
                # Get labels for this issue if specified
                labels = args.labels if hasattr(args, 'labels') and args.labels else None
                
                # Get assignees for this issue if specified
                assignees = args.assignees if hasattr(args, 'assignees') and args.assignees else None
                
                logger.info(f"Creating issue: {title}")
                if args.verbose:
                    logger.info(f"Body: {body}")
                    if labels:
                        logger.info(f"Labels: {', '.join(labels)}")
                    if assignees:
                        logger.info(f"Assignees: {', '.join(assignees)}")
                
                # Create the issue
                result = client.create_issue(
                    args.owner, args.repo, title, body, labels, assignees
                )
                
                issue_number = result.get("number")
                issue_url = result.get("html_url")
                
                if not issue_number:
                    logger.error(f"Failed to create issue: {title}")
                    failed_issues.append(title)
                else:
                    logger.info(f"Created issue #{issue_number}: {issue_url}")
                    successful_issues.append((issue_number, title, issue_url))
                    
            except Exception as e:
                logger.error(f"Error creating issue '{title}': {str(e)}")
                failed_issues.append(title)
        
        # Summary
        logger.info("\n--- Issue Creation Summary ---")
        if successful_issues:
            logger.info(f"Successfully created {len(successful_issues)} issues:")
            for number, title, url in successful_issues:
                logger.info(f"  #{number}: {title} - {url}")
        
        if failed_issues:
            logger.error(f"Failed to create {len(failed_issues)} issues:")
            for title in failed_issues:
                logger.error(f"  - {title}")
            return False
        
        return True
            
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
    parser = argparse.ArgumentParser(description="Create GitHub issues using GitHub MCP Server")
    parser.add_argument("--owner", default=DEFAULT_REPO_OWNER,
                       help=f"Repository owner (default: {DEFAULT_REPO_OWNER})")
    parser.add_argument("--repo", default=DEFAULT_REPO_NAME,
                       help=f"Repository name (default: {DEFAULT_REPO_NAME})")
    parser.add_argument("--title", dest="titles", action="append", default=[],
                       help="Issue title (can be specified multiple times for multiple issues)")
    parser.add_argument("--body", dest="bodies", action="append", default=[],
                       help="Issue body (can be specified multiple times, one per title)")
    parser.add_argument("--label", dest="labels", action="append",
                       help="Labels to add to the issue (can be specified multiple times)")
    parser.add_argument("--assignee", dest="assignees", action="append",
                       help="Users to assign to the issue (can be specified multiple times)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                       help=f"Port for the MCP server (default: {DEFAULT_PORT})")
    parser.add_argument("--use-mock", action="store_true", default=True,
                       help="Use mock GitHub MCP server instead of Docker (default: True)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show verbose output")
    
    args = parser.parse_args()
    
    success = create_issues(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()