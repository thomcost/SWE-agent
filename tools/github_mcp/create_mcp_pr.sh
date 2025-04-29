#!/bin/bash
# Script to create a PR using GitHub MCP Server

# Configuration
REPO_OWNER="thomcost"
REPO_NAME="mcp-test-repo"
BRANCH_NAME="fix-issue-1-real-mcp-$(date +%s)"
MCP_PORT=7444
CONTAINER_NAME="github-mcp-server-$$"

# Get GitHub token
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
  GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token)
  if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "Error: GITHUB_PERSONAL_ACCESS_TOKEN not set and couldn't get token from gh cli"
    exit 1
  fi
fi

echo "Starting GitHub MCP Server..."
# Pull the image if needed
docker pull ghcr.io/github/github-mcp-server

# Start a container to run the MCP server commands in
echo "Starting MCP container..."

# We need a container name for docker exec
CONTAINER_ID=$(docker run -d --name $CONTAINER_NAME --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
  -e GITHUB_TOOLSETS=all \
  ghcr.io/github/github-mcp-server sleep 3600)

if [ -z "$CONTAINER_ID" ]; then
  echo "Error: Failed to start MCP container"
  exit 1
fi

echo "Started MCP container: $CONTAINER_ID"
echo "Waiting for container to start..."
sleep 3

# Helper function to call MCP tools via stdin/stdout
call_mcp_tool() {
  local tool_name=$1
  local arguments=$2
  
  echo "Calling MCP tool: $tool_name"
  echo "Arguments: $arguments"
  
  # Create a temporary file to capture the output
  local tmp_output=$(mktemp)
  
  # Create a JSON-RPC request
  local request=$(cat <<EOF
{"jsonrpc": "2.0", "id": "1", "method": "invoke", "params": {"name": "$tool_name", "arguments": $arguments}}
EOF
)
  
  # Send the request to the MCP server
  echo "$request" | docker exec -i $CONTAINER_NAME /github-mcp-server stdio > $tmp_output
  
  # Extract the result
  result=$(cat $tmp_output | jq -r '.result')
  
  # Clean up
  rm $tmp_output
  
  echo "$result"
}

echo "Testing MCP server with get_schema request..."
schema=$(echo '{"jsonrpc": "2.0", "id": "1", "method": "get_schema"}' | docker exec -i $CONTAINER_NAME /github-mcp-server stdio)
if [ -z "$schema" ]; then
  echo "Error: Failed to get schema"
  docker stop $CONTAINER_NAME
  exit 1
fi
echo "Schema received successfully."

# Get repository info
echo "Getting repository info..."
repo_info=$(call_mcp_tool "get_repo" "{\"owner\": \"$REPO_OWNER\", \"repo\": \"$REPO_NAME\"}")
default_branch=$(echo $repo_info | grep -o '"default_branch":"[^"]*"' | cut -d':' -f2 | tr -d '"')
if [ -z "$default_branch" ]; then
  default_branch="master"
fi
echo "Default branch: $default_branch"

# Get branch SHA
echo "Getting branch info..."
branch_info=$(call_mcp_tool "get_branch" "{\"owner\": \"$REPO_OWNER\", \"repo\": \"$REPO_NAME\", \"branch\": \"$default_branch\"}")
branch_sha=$(echo $branch_info | grep -o '"sha":"[^"]*"' | head -1 | cut -d':' -f2 | tr -d '"')
if [ -z "$branch_sha" ]; then
  echo "Error: Failed to get branch SHA"
  docker stop $CONTAINER_NAME
  exit 1
fi
echo "Branch SHA: $branch_sha"

# Create a new branch
echo "Creating branch $BRANCH_NAME..."
create_branch_result=$(call_mcp_tool "create_branch" "{\"owner\": \"$REPO_OWNER\", \"repo\": \"$REPO_NAME\", \"branch\": \"$BRANCH_NAME\", \"sha\": \"$branch_sha\"}")
if [[ ! $create_branch_result == *"name"* ]]; then
  echo "Error: Failed to create branch"
  docker stop $CONTAINER_NAME
  exit 1
fi
echo "Created branch: $BRANCH_NAME"

# Update file
echo "Updating test file..."
file_content="# Test File\n\nThis file has been fixed using the REAL GitHub MCP Server with Docker!\n\nThe issue is now resolved using the actual MCP Server."
# Manual JSON escape since jq might not be available
content_for_json=$(echo -e "$file_content" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

update_result=$(call_mcp_tool "create_or_update_file" "{\"owner\": \"$REPO_OWNER\", \"repo\": \"$REPO_NAME\", \"path\": \"test-file.md\", \"message\": \"Fix issue #1 using real GitHub MCP\", \"content\": $content_for_json, \"branch\": \"$BRANCH_NAME\"}")
if [[ ! $update_result == *"content"* ]]; then
  echo "Error: Failed to update file"
  docker stop $CONTAINER_NAME
  exit 1
fi
echo "File updated successfully"

# Create PR
echo "Creating pull request..."
pr_body="This PR fixes issue #1 by updating the test file.\n\nCreated using the REAL GitHub MCP Server running in Docker.\n\nCloses #1"
pr_body_json=$(echo -e "$pr_body" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

pr_result=$(call_mcp_tool "create_pull_request" "{\"owner\": \"$REPO_OWNER\", \"repo\": \"$REPO_NAME\", \"title\": \"Fix issue #1 using REAL GitHub MCP Server\", \"head\": \"$BRANCH_NAME\", \"base\": \"$default_branch\", \"body\": $pr_body_json}")
pr_number=$(echo $pr_result | grep -o '"number":[0-9]*' | cut -d':' -f2)
pr_url=$(echo $pr_result | grep -o '"html_url":"[^"]*"' | cut -d':' -f2- | tr -d '"')

if [ -z "$pr_number" ]; then
  echo "Error: Failed to create PR"
  docker stop $CONTAINER_NAME
  exit 1
fi

echo "Created PR #$pr_number: $pr_url"

# Stop MCP container
echo "Stopping MCP container..."
docker stop $CONTAINER_NAME
echo "MCP container stopped"

echo "Pull request created successfully!"