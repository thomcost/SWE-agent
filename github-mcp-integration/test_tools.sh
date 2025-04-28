#!/bin/bash
# Test the GitHub MCP Server tools

# Get GitHub token
GITHUB_TOKEN=$(gh auth token)
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GitHub token not found. Please run 'gh auth login' first."
  exit 1
fi

# Test function
test_mcp_command() {
  local name="$1"
  local payload="$2"
  
  echo -e "\n----- Testing '$name' -----"
  echo "Request:"
  echo "$payload" | jq
  
  echo -e "\nSending to MCP server..."
  RESPONSE=$(echo "$payload" | docker run -i --rm \
    -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN \
    -e GITHUB_TOOLSETS=all \
    ghcr.io/github/github-mcp-server 2>/dev/null | tail -n 1)
    
  echo "Response:"
  echo "$RESPONSE" | jq
}

# Test various commands
echo "===== GITHUB MCP SERVER TOOL TESTS ====="

# Test "ping" method
test_mcp_command "ping" '{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "ping"
}'

# Test with no method
test_mcp_command "plain POST" '{
  "jsonrpc": "2.0",
  "id": "1"
}'

# Test with direct arguments
test_mcp_command "direct arguments" '{
  "arguments": {
    "owner": "thomcost",
    "repo": "mcp-test-repo"
  }
}'

# Try to create an issue
test_mcp_command "create_issue" '{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "create_issue",
  "params": {
    "owner": "thomcost",
    "repo": "mcp-test-repo",
    "title": "Test Issue via RPC",
    "body": "Testing direct issue creation"
  }
}'