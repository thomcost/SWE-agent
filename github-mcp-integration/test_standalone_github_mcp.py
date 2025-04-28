#!/usr/bin/env python3
"""
Standalone test for GitHub MCP integration.

This script tests basic functionality of the GitHub MCP client without
requiring the full SWE-agent package. It implements the core functionality
needed to interact with the GitHub MCP Server.
"""

import os
import sys
import json
import time
import logging
import subprocess
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-standalone-test")

# Load environment variables from .env file
load_dotenv()


class GitHubMCPConfig:
    """Configuration for GitHub MCP."""
    
    def __init__(
        self,
        github_token: str,
        enabled_toolsets: List[str] = ["all"],
        use_docker: bool = True,
        server_port: int = 9127,
        docker_image: str = "ghcr.io/github/github-mcp-server",
        github_host: Optional[str] = None,
        dynamic_toolsets: bool = False,
        server_path: Optional[str] = None
    ):
        self.github_token = github_token
        self.enabled_toolsets = enabled_toolsets
        self.use_docker = use_docker
        self.server_port = server_port
        self.docker_image = docker_image
        self.github_host = github_host
        self.dynamic_toolsets = dynamic_toolsets
        self.server_path = server_path
    
    @property
    def toolsets_string(self) -> str:
        """Get toolsets as a comma-separated string."""
        return ",".join(self.enabled_toolsets)


class MCPToolError(Exception):
    """Exception raised when a GitHub MCP tool fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class GitHubMCPClient:
    """Client for interacting with GitHub MCP Server."""
    
    def __init__(self, config: GitHubMCPConfig):
        self.config = config
        # When using host networking, use port 7444 (the default server port)
        self.base_url = "http://localhost:7444" if config.use_docker else f"http://localhost:{config.server_port}"
    
    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a GitHub MCP tool."""
        url = f"{self.base_url}/mcp/v1/tools/{tool_name}"
        logger.info(f"Calling GitHub MCP tool: {tool_name} at URL: {url}")
        
        try:
            payload = {
                "arguments": params
            }
            logger.debug(f"Request payload: {payload}")
            
            # Add better timeout handling and retry logic
            for attempt in range(3):
                try:
                    logger.debug(f"Attempt {attempt+1} to call tool {tool_name}")
                    response = requests.post(url, json=payload, timeout=10)
                    break
                except requests.exceptions.Timeout:
                    if attempt < 2:  # Don't log on last attempt
                        logger.warning(f"Timeout calling {tool_name}, retrying...")
                        time.sleep(1)
                except requests.exceptions.ConnectionError:
                    if attempt < 2:  # Don't log on last attempt
                        logger.warning(f"Connection error calling {tool_name}, retrying...")
                        time.sleep(1)
            else:
                # This executes if the for loop completes without breaking
                raise MCPToolError(f"Failed to connect to GitHub MCP Server after 3 attempts")
            
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                error_message = f"GitHub MCP tool call failed: {response.status_code}"
                error_details = {"status_code": response.status_code}
                
                try:
                    error_json = response.json()
                    logger.debug(f"Error response JSON: {error_json}")
                    error_message = error_json.get("message", error_message)
                    error_details["response"] = error_json
                except:
                    error_details["response"] = response.text
                    logger.debug(f"Error response text: {response.text}")
                
                raise MCPToolError(error_message, error_details)
            
            result = response.json()
            logger.debug(f"Successful response: {result}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Request exception when calling {tool_name}: {str(e)}")
            raise MCPToolError(f"GitHub MCP request failed: {str(e)}")
    
    def get_me(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        return self._call_tool("get_authenticated_user", {})
    
    def list_branches(self, owner: str, repo: str, page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """List branches in a repository."""
        params = {
            "owner": owner,
            "repo": repo,
            "page": page,
            "perPage": per_page
        }
        
        return self._call_tool("list_branches", params)
    
    def get_file_contents(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """Get contents of a file in a repository."""
        params = {
            "owner": owner,
            "repo": repo,
            "path": path
        }
        
        if ref:
            params["ref"] = ref
            
        return self._call_tool("get_file_contents", params)


# Global variable to track server process
_mcp_server_process: Optional[subprocess.Popen] = None


def start_github_mcp_server(config: GitHubMCPConfig) -> bool:
    """Start the GitHub MCP Server."""
    global _mcp_server_process
    
    if _mcp_server_process is not None:
        logger.warning("GitHub MCP Server is already running")
        return True
    
    # Prepare environment variables
    env = os.environ.copy()
    env["GITHUB_PERSONAL_ACCESS_TOKEN"] = config.github_token
    env["GITHUB_TOOLSETS"] = config.toolsets_string
    
    if config.dynamic_toolsets:
        env["GITHUB_DYNAMIC_TOOLSETS"] = "1"
    
    if config.github_host:
        env["GITHUB_HOST"] = config.github_host
    
    try:
        # Check if we should use the mock server
        use_mock = os.environ.get("USE_MOCK_SERVER", "").lower() in ("1", "true", "yes")
        
        if use_mock:
            # Start the mock GitHub MCP Server
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_github_mcp_server.py")
            logger.info(f"Starting mock GitHub MCP Server from {script_path}")
            
            cmd = [sys.executable, script_path]
            
            _mcp_server_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        elif config.use_docker:
            # Start the server using Docker with host network to avoid connection issues in WSL
            cmd = [
                "docker", "run", "-i", "--rm",
                "--network=host",  # Use host network to avoid port mapping issues
                "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={config.github_token}",
                "-e", f"GITHUB_TOOLSETS={config.toolsets_string}",
                "-e", f"GITHUB_MCP_SERVER_PORT=7444",  # Default port
            ]
            
            if config.dynamic_toolsets:
                cmd.extend(["-e", "GITHUB_DYNAMIC_TOOLSETS=1"])
            
            if config.github_host:
                cmd.extend(["-e", f"GITHUB_HOST={config.github_host}"])
            
            cmd.append(config.docker_image)
            
            logger.info(f"Starting GitHub MCP Server using Docker: {' '.join(cmd)}")
            
            _mcp_server_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            # Start the server using local binary
            if not config.server_path:
                logger.error("Server path must be specified when not using Docker")
                return False
                
            cmd = [
                config.server_path,
                "stdio",
                "--toolsets", config.toolsets_string
            ]
            
            if config.dynamic_toolsets:
                cmd.append("--dynamic-toolsets")
            
            if config.github_host:
                cmd.extend(["--gh-host", config.github_host])
            
            logger.info(f"Starting GitHub MCP Server using local binary: {' '.join(cmd)}")
            
            _mcp_server_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Wait longer for server to start and be ready to accept connections
        time.sleep(5)
        
        # Check if process is still running
        if _mcp_server_process.poll() is not None:
            stderr = _mcp_server_process.stderr.read() if _mcp_server_process.stderr else "No error output"
            logger.error(f"GitHub MCP Server failed to start: {stderr}")
            _mcp_server_process = None
            return False
        
        # Check if server is responding to HTTP requests
        server_ready = False
        port = 7444 if config.use_docker else config.server_port
        
        # Try multiple endpoints to see if the server is responding
        for endpoint in ["/mcp/v1/ping", "/mcp/v1/schema", "/"]:
            url = f"http://localhost:{port}{endpoint}"
            logger.info(f"Trying to connect to {url}...")
            
            for attempt in range(5):  # Try more times with longer waits
                try:
                    response = requests.get(url, timeout=3)
                    logger.info(f"Server responded to {endpoint} with status {response.status_code}")
                    server_ready = True
                    break
                except requests.RequestException as e:
                    logger.warning(f"Server not responding to {endpoint} (attempt {attempt+1}/5): {e}")
                    time.sleep(3)
            
            if server_ready:
                break
                
        if not server_ready:
            logger.warning("Could not establish connection to GitHub MCP Server, but proceeding anyway")
            
        # Wait a bit more to ensure the server is fully initialized
        logger.info("Waiting 5 more seconds for server to fully initialize...")
        time.sleep(5)
        
        logger.info("GitHub MCP Server started successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error starting GitHub MCP Server: {e}")
        _mcp_server_process = None
        return False


def stop_github_mcp_server() -> bool:
    """Stop the GitHub MCP Server."""
    global _mcp_server_process
    
    if _mcp_server_process is None:
        logger.warning("GitHub MCP Server is not running")
        return True
    
    try:
        # Check if there are any logs to capture
        if _mcp_server_process.stdout or _mcp_server_process.stderr:
            try:
                # Print any server logs for debugging
                if _mcp_server_process.stdout:
                    stdout_output = _mcp_server_process.stdout.read()
                    if stdout_output:
                        logger.info(f"Server stdout logs:\n{stdout_output}")
                
                if _mcp_server_process.stderr:
                    stderr_output = _mcp_server_process.stderr.read()
                    if stderr_output:
                        logger.info(f"Server stderr logs:\n{stderr_output}")
            except Exception as e:
                logger.warning(f"Failed to read server logs: {e}")
        
        # Try to terminate gracefully
        logger.info("Stopping GitHub MCP Server")
        _mcp_server_process.terminate()
        
        # Wait for process to terminate
        try:
            _mcp_server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If still running after 5 seconds, force kill
            logger.warning("GitHub MCP Server did not terminate gracefully, forcing kill")
            _mcp_server_process.kill()
            _mcp_server_process.wait(timeout=5)
        
        _mcp_server_process = None
        logger.info("GitHub MCP Server stopped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error stopping GitHub MCP Server: {e}")
        return False


def test_github_mcp():
    """Run GitHub MCP tests."""
    # Get GitHub token
    github_token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment variable not set")
        return 1
    
    # Create config
    config = GitHubMCPConfig(
        github_token=github_token,
        enabled_toolsets=["all"],
        use_docker=True
    )
    
    # Start server
    if not start_github_mcp_server(config):
        logger.error("Failed to start GitHub MCP Server")
        return 1
    
    try:
        logger.info("First, check server is running and accessible with a basic HTTP request")
        try:
            port = 7444 if config.use_docker else config.server_port
            response = requests.get(f"http://localhost:{port}/mcp/v1/schema", timeout=5)
            logger.info(f"Server schema endpoint status: {response.status_code}")
            if response.status_code == 200:
                logger.info("Server is responding to basic HTTP requests")
                schema = response.json()
                available_tools = []
                if "tools" in schema:
                    available_tools = [tool["name"] for tool in schema["tools"]]
                    logger.info(f"Available tools according to schema: {', '.join(available_tools)}")
            else:
                logger.warning(f"Server responded with non-200 status: {response.status_code}")
        except Exception as e:
            logger.warning(f"Error checking server schema: {e}")
        
        # Create client
        client = GitHubMCPClient(config)
        
        # Test get_me
        logger.info("Testing get_me...")
        user = client.get_me()
        logger.info(f"Authenticated as: {user.get('login', 'Unknown')}")
        
        # Test list_branches for a public repository
        logger.info("Testing list_branches...")
        branches = client.list_branches("github", "github-mcp-server")
        logger.info(f"Found {len(branches.get('items', []))} branches")
        
        # Test get_file_contents for a public repository
        logger.info("Testing get_file_contents...")
        readme = client.get_file_contents("github", "github-mcp-server", "README.md")
        content_length = len(readme.get('content', ""))
        logger.info(f"README content length: {content_length} characters")
        
        logger.info("All tests passed!")
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1
    finally:
        # Stop server
        stop_github_mcp_server()


if __name__ == "__main__":
    exit(test_github_mcp())