#!/usr/bin/env python3
"""
Test script for GitHub MCP PR integration with SWE-agent.

This script simulates a SWE-agent run that fixes an issue and creates a PR
using the GitHub MCP integration.

Requirements:
- Docker installed (for running GitHub MCP Server)
- GITHUB_TOKEN environment variable set with a valid token
- A GitHub repository where you have write access
- An open issue in that repository
"""

import os
import time
import logging
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github-mcp-pr-test")

# Load environment variables from .env file
load_dotenv()


# Import required modules
from sweagent.run.hooks.github_mcp_pr import GitHubMCPPRHook, GitHubMCPPRConfig
from sweagent.integrations.github_mcp import GitHubMCPClient, GitHubMCPConfig, start_github_mcp_server
from sweagent.types import AgentRunResult


# Mock classes for testing
@dataclass
class MockTrajectoryStep:
    response: str
    observation: str


@dataclass
class MockProblemStatement:
    github_url: str


class MockSWEEnv:
    """Mock SWE environment for testing."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.modified_files = {}
    
    def communicate(self, input: str, error_msg: str = "", timeout: int = 10, check: str = ""):
        """Mock communicate method."""
        logger.info(f"Mock ENV: {input}")
        
        if input == "git diff --name-only":
            return "\n".join(self.modified_files.keys())
        
        if input.startswith("cat "):
            file_path = input[4:].strip()
            return self.modified_files.get(file_path, "")
        
        return ""
    
    def add_modified_file(self, path: str, content: str):
        """Add a modified file to the mock environment."""
        self.modified_files[path] = content


def create_mock_run_result(success: bool = True) -> AgentRunResult:
    """Create a mock AgentRunResult for testing."""
    # Create mock trajectory
    trajectory = [
        {
            "response": "I'll analyze the issue and see what needs to be fixed.",
            "observation": "Looking at the code to understand the problem..."
        },
        {
            "response": "I found the bug! It's in the file.py module.",
            "observation": "The issue is that we're not handling the case when input is None."
        },
        {
            "response": "I'll fix the bug by adding a null check.",
            "observation": "Modified file.py to add null check before processing input."
        }
    ]
    
    # Create mock info
    info = {
        "submission": True,
        "exit_status": "submitted" if success else "failed"
    }
    
    return AgentRunResult(trajectory=trajectory, info=info)


def test_github_mcp_pr_hook():
    """Test GitHub MCP PR hook functionality."""
    logger.info("Testing GitHub MCP PR hook...")
    
    # Get GitHub token and repository details
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # Get repository details from environment or use defaults
    repo_owner = os.environ.get("TEST_REPO_OWNER", "")
    repo_name = os.environ.get("TEST_REPO_NAME", "")
    issue_number = os.environ.get("TEST_ISSUE_NUMBER", "")
    
    # Prompt for repository details if not provided
    if not repo_owner:
        repo_owner = input("Enter GitHub repository owner: ")
    
    if not repo_name:
        repo_name = input("Enter GitHub repository name: ")
    
    if not issue_number:
        issue_number = input("Enter GitHub issue number: ")
    
    # Ensure we have valid input
    if not repo_owner or not repo_name or not issue_number:
        logger.error("Repository owner, name, and issue number are required.")
        return 1
    
    # Create GitHub issue URL
    github_url = f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}"
    logger.info(f"Using GitHub issue URL: {github_url}")
    
    # Create PR hook configuration
    pr_config = GitHubMCPPRConfig(
        skip_if_commits_reference_issue=False,  # For testing, don't skip if commits reference issue
        use_docker=True,
        enabled_toolsets=["repos", "issues", "pull_requests", "users"]
    )
    
    # Create PR hook
    pr_hook = GitHubMCPPRHook(pr_config)
    
    # Initialize mock objects
    problem_statement = MockProblemStatement(github_url=github_url)
    env = MockSWEEnv(repo_path="/tmp/mock-repo")
    
    # Add some modified files
    env.add_modified_file("README.md", "# Test Repository\n\nThis is a test repository with a fix.")
    env.add_modified_file("test.py", """def test_function(value=None):
    # Fixed: Added null check to prevent errors
    if value is None:
        return None
    return value.upper()
""")
    
    # Create mock run object
    class MockRun:
        env = env
        problem_statement = problem_statement
    
    # Initialize hook
    pr_hook.on_init(run=MockRun())
    
    # Create mock result
    result = create_mock_run_result(success=True)
    
    # Test hook
    try:
        logger.info("Executing PR hook...")
        pr_hook.on_instance_completed(result)
        logger.info("PR hook executed successfully.")
        
    except Exception as e:
        logger.error(f"Error executing PR hook: {e}")
        raise
    finally:
        # Clean up
        pr_hook.on_cleanup()


def main():
    """Run PR hook test."""
    logger.info("Starting GitHub MCP PR hook test...")
    
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
        # Run test
        test_github_mcp_pr_hook()
        
        logger.info("Test completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())