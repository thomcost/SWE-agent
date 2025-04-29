# GitHub PR Integration Demo

This guide demonstrates how to use SWE-agent's GitHub PR integration feature with a practical example.

## Demo Scenario

In this demo, we'll:
1. Identify an issue in a GitHub repository
2. Configure SWE-agent to fix the issue
3. Enable the PR integration
4. Run SWE-agent and watch it create a pull request

## Prerequisites

Before starting, make sure you have:
- SWE-agent installed and configured
- A GitHub token with repository write access
- GitHub CLI installed (recommended)

## Step 1: Set Up Your Environment

First, set your GitHub token:

```bash
# In your terminal
export GITHUB_TOKEN=your_personal_access_token

# Or add to .env file
echo "GITHUB_TOKEN=your_personal_access_token" > .env
```

## Step 2: Create a Test Repository

For this demo, we'll create a simple test repository with a bug:

```bash
# Run the provided script to create a test repository
python simple_pr_test.py
```

This script:
1. Creates a temporary git repository
2. Adds a simple Python application with a bug
3. Creates a test file that fails because of the bug
4. Creates a branch with a fix
5. Provides instructions for pushing to GitHub

## Step 3: Create a GitHub Repository

1. Go to GitHub and create a new repository
2. Note the repository URL (e.g., `https://github.com/username/test-repo`)

## Step 4: Push the Test Repository

Follow the instructions output by the script:

```bash
# Add the remote
cd /tmp/tmpXXXXXXXX && git remote add origin https://github.com/username/test-repo.git

# Push the main branch
git push -u origin main

# Push the fix branch
git push -u origin fix-hello-world-XXXX
```

## Step 5: Create an Issue

1. Go to your GitHub repository
2. Create a new issue titled "Fix hello_world function to return a string"
3. In the description, add:
   ```
   The hello_world function currently only prints a message but doesn't return anything.
   This causes the tests to fail. The function should return the "Hello, World!" string.
   ```
4. Note the issue number (e.g., `#1`)

## Step 6: Configure SWE-agent

Create a configuration file for SWE-agent:

```yaml
# config/pr_demo.yaml
agent:
  # [Your standard agent configuration]
  tools:
    # [Your tools configuration]
    
# Enable PR integration through the OpenPR hook
run:
  hooks:
    - type: open_pr
      config:
        skip_if_commits_reference_issue: false
```

## Step 7: Run SWE-agent

Run SWE-agent against the issue:

```bash
python -m sweagent.run.run_single \
  --github_url https://github.com/username/test-repo/issues/1 \
  --config config/pr_demo.yaml
```

## Step 8: Observe the PR Creation

When SWE-agent completes:

1. Go to your GitHub repository
2. Look at the "Pull requests" tab
3. You should see a new PR created by SWE-agent
4. The PR will:
   - Have a title referencing the issue
   - Contain a description linking to the issue
   - Include the agent's thought process in a collapsible section
   - Be created as a draft PR

## Step 9: Review and Merge

1. Review the changes in the PR
2. Mark the PR as "Ready for review" if it looks good
3. Merge the PR
4. Observe that the issue is automatically closed

## How It Works

Behind the scenes:

1. SWE-agent identifies the issue and generates a fix
2. The `OpenPRHook` is triggered when the agent successfully completes
3. The hook:
   - Creates a new branch
   - Commits the changes
   - Pushes to the remote repository
   - Creates a pull request via the GitHub API
   - Includes the agent's thought process in the PR description

## Next Steps

After completing this demo, you can:

1. Try with real, more complex repositories
2. Customize the PR creation behavior through `OpenPRConfig`
3. Combine with other SWE-agent features for a complete workflow