# Setting Up GitHub PR Integration for SWE-agent

This guide explains how to set up and use the GitHub PR integration feature of SWE-agent.

## Prerequisites

1. GitHub account
2. GitHub Personal Access Token
3. GitHub CLI (gh) installed (optional but recommended)

## Setup Steps

### 1. Generate a GitHub Personal Access Token

1. Go to your GitHub account settings
2. Navigate to "Developer settings" > "Personal access tokens" > "Tokens (classic)"
3. Click "Generate new token"
4. Give it a descriptive name like "SWE-agent PR Integration"
5. Select the following permissions:
   - `repo` (Full control of private repositories)
   - `workflow` (if you need to trigger workflows)
6. Click "Generate token"
7. Copy the token (you won't see it again!)

### 2. Configure SWE-agent with Your Token

1. Create or edit the `.env` file in your SWE-agent directory:
   ```
   GITHUB_TOKEN=your_personal_access_token
   ```

2. Make sure the `.env` file is loaded when you run SWE-agent:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### 3. Install GitHub CLI (Optional)

The GitHub CLI makes it easier to work with GitHub from the command line.

#### macOS:
```bash
brew install gh
```

#### Linux (Ubuntu/Debian):
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

#### Windows:
```
winget install --id GitHub.cli
```

After installation, authenticate with:
```bash
gh auth login
```

### 4. Test Your Setup

1. Run the simple PR test script:
   ```bash
   python simple_pr_test.py
   ```

2. Follow the manual steps shown by the script to create a test PR

## Using the PR Integration

### With OpenPR Hook

The OpenPR hook is automatically used when SWE-agent runs against a GitHub issue.

To use it in your code:

```python
from sweagent.run.hooks.open_pr import OpenPRHook, OpenPRConfig

# Create and configure the hook
hook = OpenPRHook(OpenPRConfig(
    skip_if_commits_reference_issue=True
))

# Add the hook to your run configuration
# (This happens automatically in standard SWE-agent runs)
```

### With GitHub PR Tool

For direct PR creation:

```python
from tools.github_pr.bin.create_pr import create_pull_request

# Create a PR programmatically
pr_url = create_pull_request(
    repo_path="/path/to/repo",
    branch_name="fix-issue-123",
    title="Fix issue #123",
    body="This PR fixes the issue #123 by...",
    base_branch="main"
)
```

## Troubleshooting

### Token Issues

If you see authentication errors:
- Verify your token has the correct permissions
- Check that the token is correctly set in the environment
- Ensure the token hasn't expired

### Push Access Issues

If you can't push to a repository:
- Verify you have write access to the repository
- Check if the repository is a fork and you need to specify a different remote

### PR Creation Issues

If PR creation fails:
- Ensure your branch doesn't already exist in the remote repository
- Check if there are already PRs open for the same issue
- Verify the base branch exists in the remote repository