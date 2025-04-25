#!/usr/bin/env python3

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Create a GitHub pull request from SWE-agent's solution")
    parser.add_argument("--repo_path", required=True, help="Path to the repository")
    parser.add_argument("--branch_name", required=True, help="Name of the branch to create")
    parser.add_argument("--title", required=True, help="Pull request title")
    parser.add_argument("--body", required=True, help="Pull request body")
    parser.add_argument("--base_branch", default="main", help="Base branch (default: main)")
    return parser.parse_args()

def run_command(cmd, cwd=None):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(cmd)}")
        print(f"Error message: {e.stderr}")
        return None

def is_repo_clean(repo_path):
    """Check if the repository working directory is clean."""
    return run_command(["git", "status", "--porcelain"], cwd=repo_path) == ""

def create_branch(repo_path, branch_name, base_branch):
    """Create a new branch from the specified base branch."""
    # First checkout base branch
    if run_command(["git", "checkout", base_branch], cwd=repo_path) is None:
        return False
    
    # Pull latest changes
    if run_command(["git", "pull"], cwd=repo_path) is None:
        return False
    
    # Create and checkout new branch
    if run_command(["git", "checkout", "-b", branch_name], cwd=repo_path) is None:
        return False
    
    return True

def commit_changes(repo_path, title):
    """Commit all changes in the repository."""
    # Add all changes
    if run_command(["git", "add", "."], cwd=repo_path) is None:
        return False
    
    # Check if there are changes to commit
    if is_repo_clean(repo_path):
        print("No changes to commit.")
        return False
    
    # Commit changes
    commit_message = f"{title}\n\nCommitted by SWE-agent"
    if run_command(["git", "commit", "-m", commit_message], cwd=repo_path) is None:
        return False
    
    return True

def push_branch(repo_path, branch_name):
    """Push the branch to the remote repository."""
    return run_command(["git", "push", "-u", "origin", branch_name], cwd=repo_path) is not None

def create_pull_request(repo_path, title, body, branch_name, base_branch):
    """Create a pull request using GitHub CLI."""
    try:
        # Get the remote URL
        remote_url = run_command(["git", "remote", "get-url", "origin"], cwd=repo_path)
        if not remote_url:
            return None
        
        # Extract owner and repo from the remote URL
        if "github.com" in remote_url:
            if remote_url.startswith("git@github.com:"):
                # SSH URL format: git@github.com:owner/repo.git
                parts = remote_url.split(":")
                owner_repo = parts[1]
            else:
                # HTTPS URL format: https://github.com/owner/repo.git
                parts = remote_url.split("github.com/")
                owner_repo = parts[1]
            
            owner_repo = owner_repo.strip(".git")
            
            # Create PR using GitHub CLI
            result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", title,
                    "--body", body,
                    "--base", base_branch,
                    "--head", branch_name,
                    "--repo", owner_repo
                ],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Error creating PR: {result.stderr}")
                return None
        else:
            print("Not a GitHub repository URL:", remote_url)
            return None
    except Exception as e:
        print(f"Error creating pull request: {e}")
        return None

def main():
    args = parse_args()
    
    repo_path = os.path.abspath(args.repo_path)
    if not os.path.isdir(repo_path):
        print(f"Error: Repository path '{repo_path}' is not a valid directory.")
        return 1
    
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Error: '{repo_path}' is not a git repository.")
        return 1
    
    print(f"Creating pull request for repository at: {repo_path}")
    print(f"Branch: {args.branch_name}")
    print(f"Base branch: {args.base_branch}")
    print(f"Title: {args.title}")
    
    # Create a new branch
    print("Creating new branch...")
    if not create_branch(repo_path, args.branch_name, args.base_branch):
        print("Failed to create branch.")
        return 1
    
    # Commit changes
    print("Committing changes...")
    if not commit_changes(repo_path, args.title):
        print("Failed to commit changes.")
        return 1
    
    # Push branch
    print("Pushing branch to remote...")
    if not push_branch(repo_path, args.branch_name):
        print("Failed to push branch.")
        return 1
    
    # Create pull request
    print("Creating pull request...")
    pr_url = create_pull_request(repo_path, args.title, args.body, args.branch_name, args.base_branch)
    
    if pr_url:
        print(f"Pull request created successfully: {pr_url}")
        return 0
    else:
        print("Failed to create pull request.")
        return 1

if __name__ == "__main__":
    sys.exit(main())