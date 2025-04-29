#!/usr/bin/env python3
"""
Create GitHub issues using the GitHub MCP Server.

This script demonstrates the correct way to interact with GitHub MCP Server
using JSON-RPC over stdio, which is how the server is designed to be used.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-issue-creator")

def create_issue(title, body, owner="thomcost", repo="mcp-test-repo"):
    """
    Create a GitHub issue using the MCP Server with JSON-RPC over stdio.
    
    This is the correct and intended way to use the GitHub MCP Server.
    """
    # Get GitHub token
    github_token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("No GitHub token found. Set GITHUB_TOKEN environment variable.")
        return None
    
    # Create JSON-RPC request (correct format for MCP Server)
    request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "invoke",
        "params": {
            "name": "create_issue",
            "arguments": {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": body
            }
        }
    }
    
    # Convert request to JSON string
    request_json = json.dumps(request)
    logger.debug(f"Request: {request_json}")
    
    try:
        # Run the MCP server with the request piped to stdin
        logger.info(f"Creating issue: {title}")
        result = subprocess.run(
            [
                "docker", "run", "-i", "--rm",
                "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={github_token}",
                "-e", "GITHUB_TOOLSETS=all",
                "ghcr.io/github/github-mcp-server"
            ],
            input=request_json + "\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Process the response
        response_text = result.stdout.strip()
        
        # Skip the initialization line if present
        if "GitHub MCP Server running on stdio" in response_text:
            lines = response_text.split("\n")
            if len(lines) > 1:
                response_text = lines[1]
        
        try:
            response = json.loads(response_text)
            
            # Check for errors
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                logger.error(f"Error from MCP Server: {error_msg}")
                return None
            
            # Extract issue information
            if "result" not in response:
                logger.error(f"Invalid response format: {response}")
                return None
                
            issue_data = response["result"]
            return {
                "number": issue_data.get("number"),
                "url": issue_data.get("html_url"),
                "title": issue_data.get("title")
            }
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response_text}")
            return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing MCP Server: {e}")
        logger.error(f"STDERR: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create GitHub issues using MCP Server")
    parser.add_argument("--owner", default="thomcost", help="Repository owner")
    parser.add_argument("--repo", default="mcp-test-repo", help="Repository name")
    parser.add_argument("--title", help="Issue title")
    parser.add_argument("--body", help="Issue body")
    parser.add_argument("--count", type=int, default=1, help="Number of issues to create")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set default values if not provided
    if not args.title:
        args.title = f"MCP Issue {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    if not args.body:
        args.body = (
            f"This issue was created using the GitHub MCP Server via JSON-RPC over stdio.\n\n"
            f"Created at: {datetime.now().isoformat()}"
        )
    
    # Create issues
    successful_issues = []
    
    import time
    start_time = time.time()
    
    for i in range(args.count):
        # Add count suffix for multiple issues
        title = args.title
        if args.count > 1:
            title = f"{args.title} #{i+1}"
        
        logger.info(f"Creating issue {i+1}/{args.count}")
        issue = create_issue(title, args.body, args.owner, args.repo)
        
        if issue:
            logger.info(f"Created issue #{issue['number']}: {issue['url']}")
            successful_issues.append(issue)
        else:
            logger.error(f"Failed to create issue: {title}")
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info(f"\n--- Summary ---")
    logger.info(f"Created {len(successful_issues)}/{args.count} issues in {elapsed_time:.2f} seconds")
    
    for issue in successful_issues:
        logger.info(f"  #{issue['number']}: {issue['title']} - {issue['url']}")
    
    return 0 if len(successful_issues) == args.count else 1

if __name__ == "__main__":
    sys.exit(main())