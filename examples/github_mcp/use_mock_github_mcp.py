#!/usr/bin/env python3
"""
This script demonstrates how to use the mock GitHub MCP server
instead of Docker for creating PRs with SWE-agent.
"""

import os
from sweagent.run.hooks.github_mcp_pr import GitHubMCPPRConfig, GitHubMCPPRHook

def create_mock_mcp_config():
    """Create a GitHubMCPPRConfig that uses the mock server."""
    
    # Set environment variable to use mock server
    os.environ["USE_MOCK_SERVER"] = "true"
    
    # Create configuration with mock_for_testing=True and use_docker=False
    config = GitHubMCPPRConfig(
        # Your GitHub token (or it will use GITHUB_TOKEN env var)
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        
        # Use the mock server instead of Docker
        mock_for_testing=True,
        use_docker=False,
        
        # Port the mock server is running on
        server_port=7444,
        
        # Other optional settings
        create_draft_pr=True,
        include_trajectory=True
    )
    
    return config

def main():
    """Main function to demonstrate mock MCP configuration."""
    config = create_mock_mcp_config()
    print("Mock GitHub MCP configuration created:")
    print(f"  mock_for_testing: {config.mock_for_testing}")
    print(f"  use_docker: {config.use_docker}")
    print(f"  server_port: {config.server_port}")
    print("")
    print("To use this configuration:")
    print("1. Start the mock server: ./run_mock_github_mcp.sh")
    print("2. Configure your application to use the GitHubMCPPRHook with this config")
    print("3. Create PRs without needing Docker permissions")

if __name__ == "__main__":
    main()