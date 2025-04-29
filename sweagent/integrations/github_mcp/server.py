"""
GitHub MCP Server management module for SWE-agent.

This module provides functions to start and stop the GitHub MCP Server.
"""

import os
import subprocess
import time
import atexit
import signal
import logging
from typing import Optional, Dict, Any, List

from .config import GitHubMCPConfig

# Global variables to track server process
_mcp_server_process: Optional[subprocess.Popen] = None
_logger = logging.getLogger(__name__)


def start_github_mcp_server(config: GitHubMCPConfig) -> bool:
    """
    Start the GitHub MCP Server.
    
    Args:
        config: GitHub MCP configuration
        
    Returns:
        bool: True if the server was started successfully, False otherwise
    """
    global _mcp_server_process
    
    if _mcp_server_process is not None:
        _logger.warning("GitHub MCP Server is already running")
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
        if config.use_docker:
            # Start the server using Docker
            cmd = [
                "docker", "run", "-i", "--rm",
                "-p", f"{config.server_port}:7444",
                "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                "-e", "GITHUB_TOOLSETS",
            ]
            
            if config.dynamic_toolsets:
                cmd.extend(["-e", "GITHUB_DYNAMIC_TOOLSETS"])
            
            if config.github_host:
                cmd.extend(["-e", "GITHUB_HOST"])
            
            cmd.append(config.docker_image)
            
            _logger.info(f"Starting GitHub MCP Server using Docker: {' '.join(cmd)}")
            
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
                _logger.error("Server path must be specified when not using Docker")
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
            
            _logger.info(f"Starting GitHub MCP Server using local binary: {' '.join(cmd)}")
            
            _mcp_server_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        # Register cleanup function to ensure server is shut down on exit
        atexit.register(stop_github_mcp_server)
        
        # Wait a moment for server to start
        time.sleep(1)
        
        # Check if process is still running
        if _mcp_server_process.poll() is not None:
            stderr = _mcp_server_process.stderr.read() if _mcp_server_process.stderr else "No error output"
            _logger.error(f"GitHub MCP Server failed to start: {stderr}")
            _mcp_server_process = None
            return False
        
        _logger.info("GitHub MCP Server started successfully")
        return True
        
    except Exception as e:
        _logger.error(f"Error starting GitHub MCP Server: {e}")
        _mcp_server_process = None
        return False


def stop_github_mcp_server() -> bool:
    """
    Stop the GitHub MCP Server.
    
    Returns:
        bool: True if the server was stopped successfully, False otherwise
    """
    global _mcp_server_process
    
    if _mcp_server_process is None:
        _logger.warning("GitHub MCP Server is not running")
        return True
    
    try:
        # Try to terminate gracefully
        _logger.info("Stopping GitHub MCP Server")
        _mcp_server_process.terminate()
        
        # Wait for process to terminate
        try:
            _mcp_server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If still running after 5 seconds, force kill
            _logger.warning("GitHub MCP Server did not terminate gracefully, forcing kill")
            _mcp_server_process.kill()
            _mcp_server_process.wait(timeout=5)
        
        _mcp_server_process = None
        _logger.info("GitHub MCP Server stopped successfully")
        return True
        
    except Exception as e:
        _logger.error(f"Error stopping GitHub MCP Server: {e}")
        return False


def is_server_running() -> bool:
    """
    Check if the GitHub MCP Server is running.
    
    Returns:
        bool: True if the server is running, False otherwise
    """
    global _mcp_server_process
    
    if _mcp_server_process is None:
        return False
    
    # Check if process is still running
    return _mcp_server_process.poll() is None