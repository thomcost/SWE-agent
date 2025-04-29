#!/bin/bash
# Create GitHub issues using the MCP Server (direct approach)

# Set default values
OWNER="thomcost"
REPO="mcp-test-repo"
TITLE="MCP Issue $(date +%s)"
BODY="This issue was created using the GitHub MCP Server with direct stdin communication."
COUNT=1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner)
      OWNER="$2"
      shift 2
      ;;
    --repo)
      REPO="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --body)
      BODY="$2"
      shift 2
      ;;
    --count)
      COUNT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Get GitHub token
GITHUB_TOKEN=$(gh auth token)
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GitHub token not found. Please run 'gh auth login' first."
  exit 1
fi

echo "Creating $COUNT issues in $OWNER/$REPO"
echo "----------------------------------------"

# Create issues
SUCCESSFUL=0

for i in $(seq 1 $COUNT); do
  # Create issue title with count if multiple issues
  if [ $COUNT -gt 1 ]; then
    ISSUE_TITLE="$TITLE #$i"
  else
    ISSUE_TITLE="$TITLE"
  fi
  
  echo "Creating issue $i/$COUNT: $ISSUE_TITLE"
  
  # Create the JSON-RPC payload
  JSON_PAYLOAD=$(cat <<EOF
{"jsonrpc": "2.0", "id": "1", "method": "invoke", "params": {"name": "create_issue", "arguments": {"owner": "$OWNER", "repo": "$REPO", "title": "$ISSUE_TITLE", "body": "$BODY"}}}
EOF
)
  
  # Run the Docker command and capture output
  RESPONSE=$(echo "$JSON_PAYLOAD" | docker run -i --rm \
    -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN \
    -e GITHUB_TOOLSETS=all \
    ghcr.io/github/github-mcp-server 2>/dev/null | tail -n 1)
  
  # Check for success or error
  if [[ "$RESPONSE" == *"number"* ]]; then
    # Extract issue number and URL
    ISSUE_NUMBER=$(echo "$RESPONSE" | grep -o '"number":[0-9]*' | cut -d':' -f2)
    ISSUE_URL=$(echo "$RESPONSE" | grep -o '"html_url":"[^"]*"' | cut -d'"' -f4)
    
    echo "✅ Created issue #$ISSUE_NUMBER: $ISSUE_URL"
    SUCCESSFUL=$((SUCCESSFUL + 1))
  else
    echo "❌ Failed to create issue: $RESPONSE"
  fi
  
  # Add a small delay between requests
  if [ $i -lt $COUNT ]; then
    sleep 1
  fi
done

echo "----------------------------------------"
echo "Created $SUCCESSFUL/$COUNT issues successfully!"

# Return appropriate exit code
if [ $SUCCESSFUL -eq $COUNT ]; then
  exit 0
else
  exit 1
fi