# Creating PRs with GitHub MCP Server

This document explains how to create pull requests using the GitHub MCP Server through the `create_pr_with_github_mcp.py` script.

## Prerequisites

- Python 3.6+
- GitHub personal access token with `repo` scope permissions
- Docker (for running the real GitHub MCP Server)
- Required Python packages:
  - requests
  - python-dotenv

## Installation

1. Install required Python packages:
   ```
   pip install requests python-dotenv
   ```

2. Set your GitHub token as an environment variable:
   ```
   export GITHUB_TOKEN=your_github_token
   ```
   
   Alternatively, create a `.env` file with the following content:
   ```
   GITHUB_TOKEN=your_github_token
   ```

## Usage

### Basic Usage

To create a pull request:

```bash
python create_pr_with_github_mcp.py \
  --owner OWNER \
  --repo REPO \
  --title "PR Title" \
  --body "PR description" \
  --head feature-branch \
  --base main
```

### Creating a New Branch with the PR

To create a branch and a PR:

```bash
python create_pr_with_github_mcp.py \
  --owner OWNER \
  --repo REPO \
  --title "PR Title" \
  --body "PR description" \
  --head new-feature-branch \
  --base main \
  --create-branch
```

### Adding Files to the Branch

To create a branch, add files, and open a PR:

```bash
python create_pr_with_github_mcp.py \
  --owner OWNER \
  --repo REPO \
  --title "PR Title" \
  --body "PR description" \
  --head new-feature-branch \
  --base main \
  --create-branch \
  --file "README.md=# Updated README" \
  --file "example.py=print('Hello, World!')"
```

### Using the Mock Server

For testing without Docker or without a real GitHub repository:

```bash
python create_pr_with_github_mcp.py \
  --owner OWNER \
  --repo REPO \
  --title "PR Title" \
  --body "PR description" \
  --head feature-branch \
  --base main \
  --use-mock
```

### Creating a Draft PR

To create a draft PR:

```bash
python create_pr_with_github_mcp.py \
  --owner OWNER \
  --repo REPO \
  --title "PR Title" \
  --body "PR description" \
  --head feature-branch \
  --base main \
  --draft
```

## How It Works

1. The script starts a GitHub MCP Server (either real or mock)
2. It establishes a connection to the server
3. It creates a branch if requested (using `--create-branch`)
4. It adds files to the branch if provided (using `--file`)
5. It creates a pull request with the specified parameters
6. It properly shuts down the server after completion

## Troubleshooting

- If you get authentication errors, check that your GitHub token is valid and has the correct permissions
- If the server fails to start, check that Docker is running and you have pulled the GitHub MCP Server image
- For connection issues, check that the ports (7444 for Docker, 9127 for local) are not being used by other applications