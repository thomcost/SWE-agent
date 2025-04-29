# GitHub PR Integration

The SWE-agent GitHub PR integration allows your agent to automatically create pull requests when it successfully solves an issue. This feature streamlines the contribution process by handling branch creation, commits, and PR submission.

## Overview

When enabled, the PR integration will:

1. Create a new branch with a name based on the issue number
2. Commit the changes with a message referencing the issue
3. Push the branch to the remote repository
4. Create a pull request that includes:
   - A title referencing the issue
   - A description linking to the original issue
   - The agent's thought process (trajectory) as a collapsible section

## Requirements

To use the GitHub PR integration, you need:

1. A valid GitHub token with appropriate permissions
2. The `gh` command-line tool installed
3. A GitHub issue URL as the target for SWE-agent

## Configuration

### Setting Up GitHub Token

Store your GitHub token in the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=your_github_token
```

For persistent storage, add it to your `.env` file:

```
GITHUB_TOKEN=your_github_token
```

### Using the PR Integration

There are two ways to enable PR integration:

1. **Using the OpenPR Hook**: This is activated when running SWE-agent against a GitHub issue

2. **Using the GitHub PR Tool**: This can be used programmatically for more control

## Using the OpenPR Hook

The OpenPR hook is automatically available when running SWE-agent against a GitHub issue. It will create a PR when the agent successfully completes a task.

You can customize its behavior through the `OpenPRConfig` class:

```python
from sweagent.run.hooks.open_pr import OpenPRHook, OpenPRConfig

# Configure the hook
config = OpenPRConfig(
    skip_if_commits_reference_issue=True  # Skip PR creation if commits already reference the issue
)

# Create and use the hook
hook = OpenPRHook(config)
```

## Using the GitHub PR Tool

For more control, you can use the GitHub PR tool directly:

```python
from tools.github_pr.bin.create_pr import create_pull_request

# Create a PR programmatically
pr_url = create_pull_request(
    repo_path="/path/to/repo",
    branch_name="fix-issue-123",
    title="Fix issue #123",
    body="This PR fixes the issue #123 by...",
    base_branch="main"  # Optional, defaults to "main"
)
```

## Testing the PR Integration

You can test the PR integration using the provided test script:

```bash
python test_pr_integration.py
```

This script tests both the OpenPR hook and the GitHub PR tool without actually creating PRs in a real repository.

## PR Content

The created pull request will include:

- **Title**: "SWE-agent[bot] PR to fix: {issue.title}"
- **Description**: A brief message linking to the original issue
- **Thought Process**: The agent's trajectory (step-by-step reasoning) in a collapsible section

Example PR description:

```markdown
This is a PR opened by AI tool [SWE Agent](https://github.com/SWE-agent/SWE-agent/) 
to close [#123](https://github.com/username/repo/issues/123) (Fix memory leak in cache manager).

Closes #123.

<details>
<summary>Thought process ('trajectory') of SWE-agent (click to expand)</summary>

**🧑‍🚒 Response (0)**: 
First, let me understand the issue by reading the cache manager implementation.

**👀‍ Observation (0)**:
Found the cache manager code in src/cache/manager.py.

...additional steps...

</details>
```

## Troubleshooting

- **Error: No token provided**: Make sure the `GITHUB_TOKEN` environment variable is set
- **Error: Command failed: Failed to push branch**: Check that your token has push access to the repository
- **PR not created**: Check the logs for specific reason - it might be due to issue state or existing commits

## Advanced Usage

For advanced scenarios, you can customize the PR creation process by:

1. Modifying the `format_trajectory_markdown` function to change how the agent's trajectory is presented
2. Extending the `OpenPRHook` class to implement custom logic for when to create PRs
3. Using the `create_pull_request` function directly with custom parameters

## Limitations

- The PR integration currently only supports GitHub (not GitLab, Bitbucket, etc.)
- PRs are created as drafts by default to allow for human review
- The fork workflow is currently not fully supported (PRs are created in the same repository)