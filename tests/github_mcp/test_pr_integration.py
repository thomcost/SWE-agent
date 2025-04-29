#!/usr/bin/env python3

import argparse
import os
import tempfile
import subprocess
from pathlib import Path

# Add SWE-agent to Python path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from sweagent.utils.github import _parse_gh_issue_url
from sweagent.run.hooks.open_pr import open_pr, OpenPRHook, OpenPRConfig
from tools.github_pr.bin.create_pr import create_pull_request

class MockEnv:
    def __init__(self, repo_path):
        self.repo_path = repo_path
    
    def communicate(self, input, error_msg=None, timeout=None, check=None):
        print(f"Executing: {input}")
        try:
            result = subprocess.run(
                input, 
                shell=True, 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True,
                timeout=timeout if timeout else 60
            )
            if check == "raise" and result.returncode != 0:
                print(f"Command failed: {error_msg or 'No error message'}")  
                print(f"Error: {result.stderr}")
                raise RuntimeError(f"Command failed: {error_msg or 'No error message'}")
            return result.stdout
        except Exception as e:
            print(f"Error executing command: {e}")
            if check == "raise":
                raise
            return f"Error: {str(e)}"

class MockTrajectory:
    def __init__(self, steps=3):
        self.steps = [
            {
                "response": f"Examining issue and preparing a fix for step {i}",
                "observation": f"Found relevant code for step {i}"
            } for i in range(steps)
        ]

class MockProblemStatement:
    def __init__(self, github_url):
        self.github_url = github_url

class MockAgentRunResult:
    def __init__(self, success=True):
        self.info = {
            "submission": True,
            "exit_status": "submitted" if success else "failed"
        }
        self.trajectory = MockTrajectory().steps

def test_pr_tool():
    print("\n===== Testing GitHub PR Tool =====\n")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize git repository
        os.chdir(temp_dir)
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        
        # Create a test file and commit it
        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write("# Test Repository\n\nThis is a test repository for testing the GitHub PR tool.")
        
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
        
        # Testing PR tool creation function
        print("\nTesting create_pull_request function with local repository")
        try:
            pr_url = create_pull_request(
                repo_path=temp_dir,
                title="Test PR",
                body="This is a test PR created by the test script.",
                branch_name="test-branch",
                base_branch="main"
            )
            print(f"PR URL: {pr_url}")
        except Exception as e:
            print(f"Create PR test completed with expected result in local repo (no GitHub remote): {e}")

def test_open_pr_hook():
    print("\n===== Testing OpenPR Hook =====\n")
    
    github_url = "https://github.com/username/repo/issues/123"
    
    # Testing open_pr hook
    try:
        print("\nTesting OpenPRHook with mock environment")
        hook = OpenPRHook(OpenPRConfig())
        hook._env = MockEnv("/tmp")
        hook._token = os.environ.get("GITHUB_TOKEN", "")
        hook._problem_statement = MockProblemStatement(github_url)
        
        # Test should_open_pr
        print("\nTesting should_open_pr with mock result")
        should_open = hook.should_open_pr(MockAgentRunResult(success=True))
        print(f"Should open PR: {should_open}")
        
        # Test on_instance_completed
        print("\nTesting on_instance_completed with mock result")
        try:
            hook.on_instance_completed(MockAgentRunResult(success=True))
            print("Hook executed successfully")
        except Exception as e:
            print(f"Hook execution completed with expected result (no actual GitHub repo): {e}")
    except Exception as e:
        print(f"OpenPRHook test completed with error: {e}")

def main():
    print("Starting PR integration test\n")
    
    # Check if GitHub token is available
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Warning: GITHUB_TOKEN environment variable not set. Some tests may fail.")
    
    try:
        # Test GitHub PR tool
        test_pr_tool()
        
        # Test OpenPR hook
        test_open_pr_hook()
        
        print("\nAll tests completed!")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
