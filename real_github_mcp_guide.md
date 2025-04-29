# Using GitHub MCP with Real GitHub Repositories

This guide walks you through the process of setting up GitHub MCP to work with real GitHub repositories and create actual pull requests.

## Prerequisites

1. **Docker**: You need Docker installed (which you already have).
2. **GitHub Account**: You need a GitHub account.
3. **GitHub Personal Access Token**: You need a token with appropriate permissions.

## Step 1: Create a GitHub Personal Access Token

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Name: "SWE-agent GitHub MCP"
4. Expiration: Choose an appropriate expiration (e.g., 30 days)
5. Repository access: Select "Only select repositories" and choose the repositories you want to test with
6. Permissions:
   - Repository permissions:
     - Contents: Read and write
     - Issues: Read and write
     - Pull requests: Read and write
     - Metadata: Read-only
7. Click "Generate token"
8. **Copy your token immediately**

## Step 2: Set Up Environment Variables

Set your GitHub token as an environment variable:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
```

## Step 3: Run the Integration Test with a Real Repository

Run the integration test with a real GitHub repository:

```bash
cd /mnt/c/Users/thoma/SWE-agent
source .venv/bin/activate
python test_github_mcp_integration.py --owner your-username --repo your-repo-name
```

Replace `your-username` with your GitHub username and `your-repo-name` with the name of your repository.

## Step 4: Check the Results

Go to your GitHub repository and check:
- New branches created by the test
- New issues created by the test
- New pull requests created by the test

## Step 5: Running Just the PR Creation

If you want to test just the PR creation functionality:

```bash
cd /mnt/c/Users/thoma/SWE-agent
source .venv/bin/activate
export USE_MOCK_SERVER=false  # Make sure we're using the real GitHub MCP Server

# Run this Python code
python -c "
from sweagent.integrations.github_mcp import GitHubMCPClient, GitHubMCPConfig, start_github_mcp_server, stop_github_mcp_server
import os

# Get GitHub token
github_token = os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN')
if not github_token:
    print('GITHUB_PERSONAL_ACCESS_TOKEN not set')
    exit(1)

# Configure GitHub MCP
config = GitHubMCPConfig(
    github_token=github_token,
    enabled_toolsets=['repos', 'issues', 'pull_requests', 'users']
)

# Start GitHub MCP Server
if start_github_mcp_server(config):
    try:
        # Create client
        client = GitHubMCPClient(config)
        
        # Create a branch
        branch_name = 'test-branch-' + os.urandom(4).hex()
        repo_owner = 'your-username'  # Replace with your GitHub username
        repo_name = 'your-repo'       # Replace with your repository name
        
        # Get main branch SHA
        branches = client.list_branches(repo_owner, repo_name)
        main_branch = next((b for b in branches['items'] if b['name'] == 'main' or b['name'] == 'master'), None)
        
        if not main_branch:
            print('Could not find main or master branch')
            exit(1)
            
        # Create branch
        client.create_branch(
            owner=repo_owner,
            repo=repo_name,
            branch=branch_name,
            sha=main_branch['commit']['sha']
        )
        
        # Create a file
        client.create_or_update_file(
            owner=repo_owner,
            repo=repo_name,
            path='test-file.md',
            message='Add test file',
            content='# Test File\\n\\nThis is a test file created by GitHub MCP.',
            branch=branch_name
        )
        
        # Create PR
        pr = client.create_pull_request(
            owner=repo_owner,
            repo=repo_name,
            title='Test PR from GitHub MCP',
            head=branch_name,
            base=main_branch['name'],
            body='This is a test PR created using GitHub MCP.',
            draft=True
        )
        
        print(f'Created PR: {pr[\"html_url\"]}')
        
    finally:
        # Stop GitHub MCP Server
        stop_github_mcp_server()
else:
    print('Failed to start GitHub MCP Server')
"
```

Remember to replace `your-username` and `your-repo` with your GitHub username and repository name.

## Troubleshooting

If you encounter issues:

1. **Docker issues**: Make sure Docker is running:
   ```bash
   docker ps
   ```

2. **Token issues**: Verify your token has the necessary permissions.

3. **Connection issues**: Try using the mock server first to make sure the code works:
   ```bash
   export USE_MOCK_SERVER=true
   ```

4. **Log output**: Check the log output for specific error messages.

## Cleanup

After testing, you may want to clean up:

1. Delete test branches
2. Close test issues
3. Close or merge test PRs