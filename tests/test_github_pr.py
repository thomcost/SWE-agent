#!/usr/bin/env python3

import os
import pytest
import tempfile
from unittest import mock
from pathlib import Path

# Add parent directory to import path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import the module functions to test
from tools.github_pr.bin.create_pr import (
    parse_args,
    run_command,
    is_repo_clean,
    create_branch,
    commit_changes,
    push_branch,
    create_pull_request
)

class TestGitHubPR:
    """Test cases for the GitHub PR tool."""

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_parse_args(self, mock_args):
        """Test argument parsing."""
        # Setup mock
        mock_args.return_value = mock.Mock(
            repo_path="/path/to/repo",
            branch_name="fix-issue-123",
            title="Fix issue #123",
            body="This PR fixes the issue",
            base_branch="main"
        )
        
        # Test parsing arguments
        args = parse_args()
        
        # Verify arguments
        assert args.repo_path == "/path/to/repo"
        assert args.branch_name == "fix-issue-123"
        assert args.title == "Fix issue #123"
        assert args.body == "This PR fixes the issue"
        assert args.base_branch == "main"

    @mock.patch('subprocess.run')
    def test_run_command(self, mock_subprocess):
        """Test running a shell command."""
        # Setup mock for successful command
        process_mock = mock.Mock()
        process_mock.returncode = 0
        process_mock.stdout = "Command output"
        mock_subprocess.return_value = process_mock
        
        # Test successful command
        result = run_command(["echo", "test"])
        assert result == "Command output"
        
        # Setup mock for failed command
        mock_subprocess.side_effect = Exception("Command failed")
        
        # Test failed command
        result = run_command(["invalid", "command"])
        assert result is None

    @mock.patch('tools.github_pr.bin.create_pr.run_command')
    def test_is_repo_clean(self, mock_run_command):
        """Test checking if a repository is clean."""
        # Test clean repository
        mock_run_command.return_value = ""
        assert is_repo_clean("/path/to/repo") is True
        
        # Test dirty repository
        mock_run_command.return_value = " M file.txt"
        assert is_repo_clean("/path/to/repo") is False

    @mock.patch('tools.github_pr.bin.create_pr.run_command')
    def test_create_branch(self, mock_run_command):
        """Test creating a new branch."""
        # Setup mock for successful branch creation
        mock_run_command.return_value = "Switched to a new branch 'fix-issue-123'"
        
        # Test successful branch creation
        result = create_branch("/path/to/repo", "fix-issue-123", "main")
        assert result is True
        
        # Verify git commands were called correctly
        assert mock_run_command.call_count == 3
        checkout_call = mock_run_command.call_args_list[0]
        assert checkout_call[0][0] == ["git", "checkout", "main"]
        pull_call = mock_run_command.call_args_list[1]
        assert pull_call[0][0] == ["git", "pull"]
        branch_call = mock_run_command.call_args_list[2]
        assert branch_call[0][0] == ["git", "checkout", "-b", "fix-issue-123"]
        
        # Setup mock for failed branch creation
        mock_run_command.reset_mock()
        mock_run_command.return_value = None
        
        # Test failed branch creation
        result = create_branch("/path/to/repo", "fix-issue-123", "main")
        assert result is False

    @mock.patch('tools.github_pr.bin.create_pr.run_command')
    @mock.patch('tools.github_pr.bin.create_pr.is_repo_clean')
    def test_commit_changes(self, mock_is_repo_clean, mock_run_command):
        """Test committing changes."""
        # Setup mocks for successful commit
        mock_is_repo_clean.return_value = False
        mock_run_command.return_value = "Changes committed"
        
        # Test successful commit
        result = commit_changes("/path/to/repo", "Fix issue #123")
        assert result is True
        
        # Verify git commands were called correctly
        assert mock_run_command.call_count == 2
        add_call = mock_run_command.call_args_list[0]
        assert add_call[0][0] == ["git", "add", "."]
        commit_call = mock_run_command.call_args_list[1]
        assert commit_call[0][0][0:3] == ["git", "commit", "-m"]
        
        # Setup mocks for clean repository (nothing to commit)
        mock_run_command.reset_mock()
        mock_is_repo_clean.return_value = True
        
        # Test commit with no changes
        result = commit_changes("/path/to/repo", "Fix issue #123")
        assert result is False
        
        # Setup mocks for failed commit
        mock_run_command.reset_mock()
        mock_is_repo_clean.return_value = False
        mock_run_command.return_value = None
        
        # Test failed commit
        result = commit_changes("/path/to/repo", "Fix issue #123")
        assert result is False

    @mock.patch('tools.github_pr.bin.create_pr.run_command')
    def test_push_branch(self, mock_run_command):
        """Test pushing a branch."""
        # Setup mock for successful push
        mock_run_command.return_value = "Branch pushed"
        
        # Test successful push
        result = push_branch("/path/to/repo", "fix-issue-123")
        assert result is True
        
        # Verify git command was called correctly
        assert mock_run_command.call_count == 1
        push_call = mock_run_command.call_args
        assert push_call[0][0] == ["git", "push", "-u", "origin", "fix-issue-123"]
        
        # Setup mock for failed push
        mock_run_command.reset_mock()
        mock_run_command.return_value = None
        
        # Test failed push
        result = push_branch("/path/to/repo", "fix-issue-123")
        assert result is False

    @mock.patch('tools.github_pr.bin.create_pr.run_command')
    @mock.patch('subprocess.run')
    def test_create_pull_request(self, mock_subprocess, mock_run_command):
        """Test creating a pull request."""
        # Setup mocks for successful PR creation
        mock_run_command.return_value = "https://github.com/owner/repo.git"
        process_mock = mock.Mock()
        process_mock.returncode = 0
        process_mock.stdout = "https://github.com/owner/repo/pull/123"
        mock_subprocess.return_value = process_mock
        
        # Test successful PR creation
        result = create_pull_request(
            "/path/to/repo",
            "Fix issue #123",
            "This PR fixes the issue",
            "fix-issue-123",
            "main"
        )
        assert result == "https://github.com/owner/repo/pull/123"
        
        # Verify commands were called correctly
        assert mock_run_command.call_count == 1
        get_url_call = mock_run_command.call_args
        assert get_url_call[0][0] == ["git", "remote", "get-url", "origin"]
        
        assert mock_subprocess.call_count == 1
        create_pr_call = mock_subprocess.call_args
        assert create_pr_call[0][0][0:3] == ["gh", "pr", "create"]
        
        # Setup mocks for failed PR creation
        mock_run_command.reset_mock()
        mock_subprocess.reset_mock()
        process_mock.returncode = 1
        process_mock.stderr = "Error creating PR"
        mock_subprocess.return_value = process_mock
        
        # Test failed PR creation
        result = create_pull_request(
            "/path/to/repo",
            "Fix issue #123",
            "This PR fixes the issue",
            "fix-issue-123",
            "main"
        )
        assert result is None