"""
GitHub MCP hook for opening PRs from SWE-agent solutions.

This hook uses the GitHub MCP Server to create pull requests when SWE-agent
successfully fixes an issue.
"""

import os
import random
import re
import logging
from typing import Optional, Dict, Any, List, Set

from pydantic import BaseModel, Field

from sweagent.environment.swe_env import SWEEnv
from sweagent.run.hooks.abstract import RunHook
from sweagent.types import AgentRunResult
from sweagent.utils.github import _parse_gh_issue_url
from sweagent.integrations.github_mcp import (
    GitHubMCPClient,
    GitHubMCPConfig,
    start_github_mcp_server,
    stop_github_mcp_server
)

_logger = logging.getLogger(__name__)


class GitHubMCPPRConfig(BaseModel):
    """Configuration for the GitHub MCP PR hook."""
    
    # GitHub token for authentication
    github_token: str = Field(
        default_factory=lambda: os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", ""),
        description="GitHub personal access token"
    )
    
    # The port to run the GitHub MCP Server on
    server_port: int = Field(
        default=9127,
        description="Port to run the GitHub MCP Server on"
    )
    
    # Whether to use Docker to run the GitHub MCP Server
    use_docker: bool = Field(
        default=True,
        description="Whether to use Docker to run the GitHub MCP Server"
    )
    
    # Path to local GitHub MCP Server binary (if not using Docker)
    server_path: Optional[str] = Field(
        default=None,
        description="Path to local GitHub MCP Server binary (if not using Docker)"
    )
    
    # Docker image for GitHub MCP Server
    docker_image: str = Field(
        default="ghcr.io/github/github-mcp-server",
        description="Docker image for GitHub MCP Server"
    )
    
    # GitHub Enterprise Server hostname (if using GitHub Enterprise)
    github_host: Optional[str] = Field(
        default=None,
        description="GitHub Enterprise Server hostname (if using GitHub Enterprise)"
    )
    
    # GitHub PR toolsets to enable
    enabled_toolsets: List[str] = Field(
        default=["repos", "issues", "pull_requests", "users"],
        description="GitHub PR toolsets to enable"
    )
    
    # Whether to use mock server for testing
    mock_for_testing: bool = Field(
        default=False,
        description="Whether to use mock server for testing"
    )
    
    # Whether to make the PR a draft PR
    create_draft_pr: bool = Field(
        default=True,
        description="Whether to make the PR a draft PR"
    )
    
    # Include the agent trajectory in the PR description
    include_trajectory: bool = Field(
        default=True,
        description="Include the agent trajectory in the PR description"
    )
    
    # PR title template
    pr_title_template: str = Field(
        default="Fix {issue_title} (#{issue_number})",
        description="PR title template"
    )
    
    # PR body template
    pr_body_template: str = Field(
        default=(
            "This is a PR opened by [SWE Agent](https://github.com/SWE-agent/SWE-agent/) "
            "to fix an issue.\n\n"
            "## Issue\n"
            "[#{issue_number}]({issue_url}) - {issue_title}\n\n"
            "## Changes\n"
            "{changes_summary}\n\n"
            "Closes #{issue_number}."
        ),
        description="PR body template"
    )


class GitHubMCPPRHook(RunHook):
    """
    Hook that creates a PR using GitHub MCP Server when an issue is fixed.
    
    This hook uses the GitHub MCP Server to create a PR when the agent
    successfully completes a task.
    """
    
    def __init__(self, config: GitHubMCPPRConfig):
        """
        Initialize the hook.
        
        Args:
            config: Configuration for the hook
        """
        self._config = config
        self._client: Optional[GitHubMCPClient] = None
        self._env: Optional[SWEEnv] = None
        self._github_url: Optional[str] = None
        self._logger = logging.getLogger("swe-agent-github-mcp-pr")
        self._mcp_server_started = False
    
    def on_init(self, *, run):
        """
        Initialize the hook with the run.
        
        Args:
            run: The run instance
        """
        self._env = run.env
        self._problem_statement = run.problem_statement
        self._github_url = getattr(run.problem_statement, "github_url", None)
        
        # Get GitHub token from environment or config
        github_token = self._config.github_token
        if not github_token:
            github_token = os.getenv("GITHUB_TOKEN", "")
            
        if not github_token:
            self._logger.warning(
                "GitHub token not set. Set GITHUB_TOKEN environment variable "
                "or provide github_token in the config."
            )
            return
        
        # Initialize GitHub MCP Client with config
        mcp_config = GitHubMCPConfig(
            github_token=github_token,
            server_port=self._config.server_port,
            github_host=self._config.github_host,
            enabled_toolsets=self._config.enabled_toolsets,
            dynamic_toolsets=False,
            docker_image=self._config.docker_image,
            server_path=self._config.server_path,
            use_docker=self._config.use_docker
        )
        
        # Set up environment for mock server if needed
        if self._config.mock_for_testing:
            os.environ["USE_MOCK_SERVER"] = "true"
            
        # Start the GitHub MCP Server
        if start_github_mcp_server(mcp_config):
            self._client = GitHubMCPClient(mcp_config)
            self._mcp_server_started = True
            self._logger.info("GitHub MCP Server started successfully")
        else:
            self._logger.error("Failed to start GitHub MCP Server")
    
    def on_instance_completed(self, result: AgentRunResult):
        """
        Called when an instance is completed.
        
        Args:
            result: The result of the run
        """
        if self._client is None:
            self._logger.warning("GitHub MCP Client not initialized. Skipping PR creation.")
            return
            
        if self.should_open_pr(result):
            self._logger.info("Creating PR...")
            
            try:
                # Create the PR using GitHub MCP
                pr = self._open_pr(result)
                if pr:
                    # Add PR URL to result metadata
                    result.info["github_pr_url"] = pr.get("html_url")
                    result.info["github_pr_number"] = pr.get("number")
                    
                    self._logger.info(
                        f"🎉 PR created at {pr['html_url']}. "
                        f"{'It is created as a draft PR. ' if self._config.create_draft_pr else ''}"
                        "Please review it carefully before merging."
                    )
            except Exception as e:
                self._logger.error(f"Failed to create PR: {e}")
    
    def should_open_pr(self, result: AgentRunResult) -> bool:
        """
        Determine if a PR should be opened for this result.
        
        Args:
            result: The result of the run
            
        Returns:
            Whether a PR should be opened
        """
        if not self._github_url:
            self._logger.info("Not opening PR because no GitHub URL was provided.")
            return False
            
        if not self._client:
            self._logger.info("Not opening PR because GitHub MCP Client is not initialized.")
            return False
            
        if not result.info.get("submission"):
            self._logger.info("Not opening PR because no submission was made.")
            return False
            
        if result.info.get("exit_status") != "submitted":
            self._logger.info(
                "Not opening PR because exit status was %s and not submitted.", result.info.get("exit_status")
            )
            return False
        
        try:
            # Parse GitHub URL
            owner, repo, issue_number = _parse_gh_issue_url(self._github_url)
            issue_number = int(issue_number)
            
            # Get issue details
            issue = self._client.get_issue(owner, repo, issue_number)
            
            # Check issue state
            if issue["state"] != "open":
                self._logger.info(f"Issue is not open (state={issue['state']}. Skipping PR creation.")
                return False
                
            # Check if issue is assigned
            if issue.get("assignee"):
                self._logger.info("Issue is already assigned. Skipping PR creation. Be nice :)")
                return False
                
            # Check if issue is locked
            if issue.get("locked"):
                self._logger.info("Issue is locked. Skipping PR creation.")
                return False
            
            # Check for existing PRs referencing the issue
            # This would require additional logic to check PRs
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error checking if PR should be opened: {e}")
            return False
    
    def _open_pr(self, result: AgentRunResult) -> Optional[Dict[str, Any]]:
        """
        Open a PR for the result.
        
        Args:
            result: The result of the run
            
        Returns:
            The created PR data or None if failed
        """
        if not self._client or not self._github_url or not self._env:
            return None
            
        try:
            # Parse GitHub URL
            owner, repo, issue_number = _parse_gh_issue_url(self._github_url)
            issue_number = int(issue_number)
            
            # Create a branch name
            branch_name = f"swe-agent-fix-{issue_number}-{os.urandom(4).hex()}"
            
            # Get the issue details
            issue = self._client.get_issue(owner, repo, issue_number)
            
            # Create a new branch
            # First, we need to get the SHA of the default branch
            branches = self._client.list_branches(owner, repo)
            main_branch_info = next((b for b in branches["items"] if b["name"] == "main"), None)
            if not main_branch_info:
                # Try master branch if main doesn't exist
                main_branch_info = next((b for b in branches["items"] if b["name"] == "master"), None)
                
            if not main_branch_info:
                self._logger.error("Could not find main or master branch")
                return None
                
            base_branch = main_branch_info["name"]
            sha = main_branch_info["commit"]["sha"]
            
            # Create the branch
            self._client.create_branch(owner, repo, branch_name, sha)
            
            # Get modified files from environment
            modified_files = self._get_modified_files()
            
            # Create a changes summary for the PR description
            changes_summary = self._format_changes_summary(modified_files)
            
            # Add all files to the new branch
            for file_path, content in modified_files.items():
                try:
                    self._client.create_or_update_file(
                        owner=owner,
                        repo=repo,
                        path=file_path,
                        message=f"Fix: {issue['title']}\n\nCloses #{issue_number}",
                        content=content,
                        branch=branch_name
                    )
                except Exception as e:
                    self._logger.error(f"Failed to update file {file_path}: {e}")
            
            # Format PR title and body using templates
            pr_title = self._config.pr_title_template.format(
                issue_number=issue_number,
                issue_title=issue["title"]
            )
            
            pr_body = self._config.pr_body_template.format(
                issue_number=issue_number,
                issue_url=self._github_url,
                issue_title=issue["title"],
                changes_summary=changes_summary
            )
            
            # Add trajectory to PR body if configured
            if self._config.include_trajectory and result.trajectory:
                pr_body += "\n\n" + self._format_trajectory_markdown(result.trajectory)
            
            # Create the PR
            pr = self._client.create_pull_request(
                owner=owner,
                repo=repo,
                title=pr_title,
                head=branch_name,
                base=base_branch,
                body=pr_body,
                draft=self._config.create_draft_pr
            )
            
            return pr
            
        except Exception as e:
            self._logger.error(f"Error creating PR: {e}")
            return None
    
    def _get_modified_files(self) -> Dict[str, str]:
        """
        Get the files modified by the agent.
        
        Returns:
            Dictionary of modified files (path -> content)
        """
        if not self._env:
            return {}
            
        # Get modified files from git
        output = self._env.communicate(
            input="git diff --name-only",
            error_msg="Failed to get modified files",
            timeout=10
        )
        
        modified_files = {}
        for file_path in output.splitlines():
            if not file_path.strip():
                continue
                
            # Get file content
            content = self._env.communicate(
                input=f"cat {file_path}",
                error_msg=f"Failed to read file {file_path}",
                timeout=10
            )
            
            modified_files[file_path] = content
            
        return modified_files
    
    def _format_changes_summary(self, modified_files: Dict[str, str]) -> str:
        """
        Format a summary of changes for the PR description.
        
        Args:
            modified_files: Dictionary of modified files
            
        Returns:
            Formatted changes summary
        """
        if not modified_files:
            return "No files were modified."
            
        lines = []
        lines.append(f"Modified {len(modified_files)} files:")
        lines.append("")
        
        for file_path in sorted(modified_files.keys()):
            lines.append(f"- `{file_path}`")
            
        return "\n".join(lines)
    
    def _format_trajectory_markdown(self, trajectory):
        """
        Format a trajectory as a markdown string for use in GitHub PR description.
        
        Args:
            trajectory: The agent's trajectory
            
        Returns:
            Formatted markdown
        """
        prefix = [
            "<details>",
            "<summary>Thought process ('trajectory') of SWE-agent (click to expand)</summary>",
            "",
            "",
        ]
        steps = []
        for i, step in enumerate(trajectory):
            step_strs = [
                f"**🧑‍🚒 Response ({i})**: ",
                f"{step['response'].strip()}",
                f"**👀‍ Observation ({i})**:",
                "```",
                f"{self._remove_triple_backticks(step['observation']).strip()}",
                "```",
            ]
            steps.append("\n".join(step_strs))
        suffix = [
            "",
            "</details>",
        ]
        return "\n".join(prefix) + "\n\n---\n\n".join(steps) + "\n".join(suffix)
    
    def _remove_triple_backticks(self, text: str) -> str:
        """
        Remove triple backticks from text for markdown formatting.
        
        Args:
            text: The text to process
            
        Returns:
            Processed text
        """
        return re.sub(r"```(?:\w+)?\n", "", re.sub(r"\n```", "", text))
    
    def on_cleanup(self):
        """Clean up resources when done."""
        # Stop the GitHub MCP Server
        if self._mcp_server_started:
            stop_github_mcp_server()
            self._mcp_server_started = False