#!/usr/bin/env python3
"""
Test script for GitHub MCP integration.

This script demonstrates how to use the GitHub MCP integration
to perform various GitHub operations.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("github-mcp-test")

# Add the parent directory to sys.path to import sweagent modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sweagent.integrations.github_mcp import (
        GitHubMCPClient,
        GitHubMCPConfig,
        start_github_mcp_server,
        stop_github_mcp_server
    )
except ImportError:
    logger.error("Failed to import GitHub MCP modules. Make sure you're in the SWE-agent directory.")
    sys.exit(1)


def test_user_info(client: GitHubMCPClient) -> Dict[str, Any]:
    """Test getting user information.
    
    Args:
        client: The GitHub MCP client
        
    Returns:
        The user information
    """
    logger.info("Getting authenticated user information...")
    user = client.get_me()
    logger.info(f"Authenticated as: {user.get('login', 'Unknown')}")
    return user


def test_repository_operations(client: GitHubMCPClient, owner: str, repo: str) -> None:
    """Test repository operations.
    
    Args:
        client: The GitHub MCP client
        owner: The repository owner
        repo: The repository name
    """
    logger.info(f"Testing repository operations for {owner}/{repo}...")
    
    # List branches
    logger.info("Listing branches...")
    branches = client.list_branches(owner, repo)
    logger.info(f"Found {len(branches.get('items', []))} branches")
    for branch in branches.get("items", []):
        logger.info(f"  - {branch.get('name', 'Unknown')}")
    
    # Get README.md
    logger.info("Getting README.md...")
    try:
        readme = client.get_file_contents(owner, repo, "README.md")
        logger.info(f"README size: {readme.get('size', 0)} bytes")
    except Exception as e:
        logger.warning(f"Failed to get README.md: {e}")
    
    # Create a branch
    branch_name = f"test-branch-{os.urandom(4).hex()}"
    logger.info(f"Creating branch {branch_name}...")
    
    # Get default branch SHA
    default_branch = branches["items"][0]["name"]
    default_branch_sha = branches["items"][0]["commit"]["sha"]
    
    try:
        branch = client.create_branch(owner, repo, branch_name, default_branch_sha)
        logger.info(f"Created branch: {branch.get('name', 'Unknown')}")
    except Exception as e:
        logger.warning(f"Failed to create branch: {e}")


def test_issue_operations(client: GitHubMCPClient, owner: str, repo: str) -> Dict[str, Any]:
    """Test issue operations.
    
    Args:
        client: The GitHub MCP client
        owner: The repository owner
        repo: The repository name
        
    Returns:
        The created issue
    """
    logger.info(f"Testing issue operations for {owner}/{repo}...")
    
    # Create an issue
    issue_title = f"Test issue {os.urandom(4).hex()}"
    issue_body = "This is a test issue created by the GitHub MCP integration test script."
    
    logger.info(f"Creating issue: {issue_title}...")
    try:
        issue = client.create_issue(owner, repo, issue_title, issue_body)
        logger.info(f"Created issue #{issue.get('number', 'Unknown')}: {issue.get('title', 'Unknown')}")
        
        # Comment on the issue
        comment_body = "This is a test comment created by the GitHub MCP integration test script."
        logger.info("Adding comment to issue...")
        comment = client.add_issue_comment(owner, repo, issue["number"], comment_body)
        logger.info(f"Added comment: {comment.get('id', 'Unknown')}")
        
        return issue
    except Exception as e:
        logger.warning(f"Failed to create issue: {e}")
        return {}


def test_pr_operations(client: GitHubMCPClient, owner: str, repo: str, issue: Dict[str, Any]) -> None:
    """Test PR operations.
    
    Args:
        client: The GitHub MCP client
        owner: The repository owner
        repo: The repository name
        issue: The issue to reference in the PR
    """
    if not issue:
        logger.warning("No issue available, skipping PR operations test")
        return
        
    logger.info(f"Testing PR operations for {owner}/{repo}...")
    
    # Create a branch
    branch_name = f"fix-issue-{issue.get('number', 'unknown')}-{os.urandom(4).hex()}"
    logger.info(f"Creating branch {branch_name}...")
    
    # Get default branch
    branches = client.list_branches(owner, repo)
    default_branch = branches["items"][0]["name"]
    default_branch_sha = branches["items"][0]["commit"]["sha"]
    
    try:
        branch = client.create_branch(owner, repo, branch_name, default_branch_sha)
        logger.info(f"Created branch: {branch.get('name', 'Unknown')}")
        
        # Create a file in the branch
        test_file_path = f"test-file-{os.urandom(4).hex()}.md"
        test_file_content = f"# Test File\n\nThis is a test file created by the GitHub MCP integration test script.\n\nFixing issue #{issue.get('number', 'Unknown')}."
        
        logger.info(f"Creating file {test_file_path}...")
        file = client.create_or_update_file(
            owner, repo, test_file_path,
            f"Add test file for issue #{issue.get('number', 'Unknown')}",
            test_file_content, branch_name
        )
        logger.info(f"Created file: {file.get('content', {}).get('path', 'Unknown')}")
        
        # Create a PR
        pr_title = f"Fix issue #{issue.get('number', 'Unknown')}: {issue.get('title', 'Unknown')}"
        pr_body = f"This is a test PR created by the GitHub MCP integration test script.\n\nFixes #{issue.get('number', 'Unknown')}."
        
        logger.info(f"Creating PR: {pr_title}...")
        pr = client.create_pull_request(
            owner, repo, pr_title, branch_name, default_branch, pr_body, draft=True
        )
        logger.info(f"Created PR #{pr.get('number', 'Unknown')}: {pr.get('title', 'Unknown')}")
        logger.info(f"PR URL: {pr.get('html_url', 'Unknown')}")
        
    except Exception as e:
        logger.warning(f"Failed in PR operations: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test GitHub MCP integration")
    parser.add_argument("--mock", action="store_true", help="Use mock server")
    parser.add_argument("--owner", help="Repository owner", default="test-owner")
    parser.add_argument("--repo", help="Repository name", default="test-repo")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_PERSONAL_ACCESS_TOKEN)")
    args = parser.parse_args()
    
    # Set up mock server if requested
    if args.mock:
        os.environ["USE_MOCK_SERVER"] = "true"
        logger.info("Using mock GitHub MCP Server")
    
    # Get GitHub token
    github_token = args.token or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        if not args.mock:
            logger.error("GitHub token not provided. Use --token or set GITHUB_PERSONAL_ACCESS_TOKEN")
            sys.exit(1)
        else:
            github_token = "mock-token"  # Mock token for testing
    
    # Configure GitHub MCP
    config = GitHubMCPConfig(
        github_token=github_token,
        enabled_toolsets=["repos", "issues", "pull_requests", "users"],
        use_docker=not args.mock,
        mock_for_testing=args.mock
    )
    
    # Start GitHub MCP Server
    logger.info("Starting GitHub MCP Server...")
    if start_github_mcp_server(config):
        try:
            # Create client
            client = GitHubMCPClient(config)
            logger.info("GitHub MCP Server started successfully")
            
            # Run tests
            user = test_user_info(client)
            test_repository_operations(client, args.owner, args.repo)
            issue = test_issue_operations(client, args.owner, args.repo)
            test_pr_operations(client, args.owner, args.repo, issue)
            
            logger.info("Tests completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during tests: {e}")
        finally:
            # Stop GitHub MCP Server
            logger.info("Stopping GitHub MCP Server...")
            stop_github_mcp_server()
    else:
        logger.error("Failed to start GitHub MCP Server")


if __name__ == "__main__":
    main()