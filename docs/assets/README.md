# SWE-agent Test Suite for GitHub PR Integration

This directory contains test scripts and examples for testing the GitHub PR integration feature in SWE-agent.

## Overview

The GitHub PR integration allows SWE-agent to automatically create pull requests when it successfully solves GitHub issues. The integration handles branch creation, committing changes, pushing to remote, and creating a well-formatted pull request.

## Available Tests

1. `test_pr_integration.py` - Test script for both the OpenPR hook and the GitHub PR tool
2. `pr_example_output.md` - Example of PR description format

## Running Tests

To run the PR integration tests:

```bash
python test_pr_integration.py
```

## Requirements

- GitHub token (set as GITHUB_TOKEN environment variable)
- GitHub CLI (gh) installed
- Git installed

## Components Tested

1. OpenPR Hook
   - PR creation logic
   - Issue filtering
   - Formatting of PR description

2. GitHub PR Tool
   - Branch creation
   - Committing changes
   - PR creation via GitHub API

## Expected Results

When running the tests, you should see output indicating the PR creation process, including:
- Branch creation
- Commit creation
- PR creation (with simulated URLs)

Note that the tests are designed to run safely without creating actual PRs in remote repositories.

## Configuration

The test script supports the following environment variables:
- GITHUB_TOKEN - GitHub API token
- TEST_REPO_PATH - Custom repository path for testing (optional)
- TEST_ISSUE_URL - Custom issue URL for testing (optional)