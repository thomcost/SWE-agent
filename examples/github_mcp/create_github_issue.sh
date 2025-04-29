#!/bin/bash
# Create a GitHub issue using the GitHub MCP Server

# Set default values
PORT=7444
REPO_OWNER="thomcost"
REPO_NAME="mcp-test-repo"
ISSUE_TITLE="Test Issue $(date +%s)"
ISSUE_BODY="This is a test issue created using the GitHub MCP Server."

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift 2
      ;;
    --owner)
      REPO_OWNER="$2"
      shift 2
      ;;
    --repo)
      REPO_NAME="$2"
      shift 2
      ;;
    --title)
      ISSUE_TITLE="$2"
      shift 2
      ;;
    --body)
      ISSUE_BODY="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Verify GitHub MCP Server is running
echo "Verifying GitHub MCP Server is running..."
SCHEMA=$(curl -s --max-time 2 "http://localhost:$PORT/mcp/v1/schema")
if [[ "$SCHEMA" != *"tools"* ]]; then
  echo "Error: GitHub MCP Server is not running. Please start it using run_github_mcp.sh"
  exit 1
fi

# Verify create_issue tool is available
if [[ "$SCHEMA" != *"create_issue"* ]]; then
  echo "Error: The 'create_issue' tool is not available in the MCP Server."
  exit 1
fi

echo "Creating issue:"
echo "- Repository: $REPO_OWNER/$REPO_NAME"
echo "- Title: $ISSUE_TITLE"
echo "- Body length: ${#ISSUE_BODY} characters"

# Create JSON payload for create_issue
PAYLOAD=$(cat <<EOF
{
  "arguments": {
    "owner": "$REPO_OWNER",
    "repo": "$REPO_NAME",
    "title": "$ISSUE_TITLE",
    "body": "$ISSUE_BODY"
  }
}
EOF
)

# Call the create_issue tool
echo "Calling MCP Server create_issue tool..."
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "http://localhost:$PORT/mcp/v1/tools/create_issue")

# Check for errors
if [[ "$RESPONSE" == *"error"* ]]; then
  echo "Error creating issue:"
  echo "$RESPONSE" | jq .
  exit 1
fi

# Extract issue number and URL
ISSUE_NUMBER=$(echo "$RESPONSE" | grep -o '"number":[0-9]*' | cut -d':' -f2)
ISSUE_URL=$(echo "$RESPONSE" | grep -o '"html_url":"[^"]*"' | cut -d':' -f2- | tr -d '"')

if [ -z "$ISSUE_NUMBER" ]; then
  echo "Error: Failed to extract issue number from response."
  echo "Response: $RESPONSE"
  exit 1
fi

echo "Issue created successfully!"
echo "- Issue #$ISSUE_NUMBER"
echo "- URL: $ISSUE_URL"