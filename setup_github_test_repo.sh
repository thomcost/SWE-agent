#!/bin/bash
# Script to set up a private GitHub repo for testing GitHub MCP integration

# Check if the user is authenticated
if ! gh auth status &>/dev/null; then
  echo "You need to authenticate with GitHub first."
  echo "Run: gh auth login"
  exit 1
fi

# Get GitHub username
USERNAME=$(gh api user | grep login | cut -d'"' -f4)
if [ -z "$USERNAME" ]; then
  echo "Failed to get GitHub username."
  exit 1
fi

# Create a private repository
echo "Creating private repository 'mcp-test-repo'..."
gh repo create mcp-test-repo --private --clone --description "Test repository for GitHub MCP integration" --add-readme

# Change to the repository directory
cd mcp-test-repo || exit 1

# Create a test issue
echo "Creating a test issue..."
gh issue create --title "Test issue for MCP integration" --body "This is a test issue for testing the GitHub MCP integration."

# Generate a personal access token with appropriate permissions
echo "Creating a personal access token..."
echo "Note: GitHub CLI doesn't support creating fine-grained tokens directly."
echo "Opening the token creation page in your browser..."
gh auth token-create --scopes repo,workflow

# Print next steps
echo ""
echo "========================================================="
echo "Repository 'mcp-test-repo' created successfully!"
echo ""
echo "Next steps:"
echo "1. Copy the personal access token you just created"
echo "2. Set it as an environment variable:"
echo "   export GITHUB_PERSONAL_ACCESS_TOKEN=your_token"
echo ""
echo "3. Run the integration test:"
echo "   cd /mnt/c/Users/thoma/SWE-agent"
echo "   source .venv/bin/activate"
echo "   python test_github_mcp_integration.py --owner $USERNAME --repo mcp-test-repo"
echo "========================================================="