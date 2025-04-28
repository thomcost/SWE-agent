#!/bin/bash
# Run the mock GitHub MCP Server

# Set your GitHub token here or export it before running this script
# export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here

echo "Starting mock GitHub MCP Server on port 7444"
echo "Press Ctrl+C to stop the server"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Run the mock server
python mock_github_mcp_server.py