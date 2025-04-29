"""
Client for interacting with the GitHub MCP Server.

This module provides a client for interacting with the GitHub MCP Server
using the Model Context Protocol (MCP).
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union, Tuple, cast
from enum import Enum

from .config import GitHubMCPConfig

_logger = logging.getLogger(__name__)


class MCPToolError(Exception):
    """Exception raised when a GitHub MCP tool fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class GitHubMCPClient:
    """
    Client for interacting with the GitHub MCP Server.
    
    This client provides a Python interface to the GitHub MCP Server,
    which enables interaction with GitHub repositories, issues, pull requests,
    and other GitHub features through the Model Context Protocol (MCP).
    """
    
    def __init__(self, config: GitHubMCPConfig):
        """
        Initialize the GitHub MCP client.
        
        Args:
            config: The GitHub MCP configuration
        """
        self.config = config
        self.base_url = f"http://localhost:{config.server_port}"
        
    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a GitHub MCP tool.
        
        Args:
            tool_name: The name of the tool to call
            params: The parameters to pass to the tool
            
        Returns:
            The response from the tool
            
        Raises:
            MCPToolError: If the tool call fails
        """
        url = f"{self.base_url}/mcp/v1/tools/{tool_name}"
        
        try:
            payload = {
                "arguments": params
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                error_message = f"GitHub MCP tool call failed: {response.status_code}"
                error_details = {"status_code": response.status_code}
                
                try:
                    error_json = response.json()
                    error_message = error_json.get("message", error_message)
                    error_details["response"] = error_json
                except:
                    error_details["response"] = response.text
                
                raise MCPToolError(error_message, error_details)
            
            return response.json()
            
        except requests.RequestException as e:
            raise MCPToolError(f"GitHub MCP request failed: {str(e)}")
    
    # ------------ Repository Tools ------------ #
    
    def get_file_contents(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the contents of a file or directory in a repository.
        
        Args:
            owner: The repository owner
            repo: The repository name
            path: The file or directory path
            ref: The git reference (branch, tag, or commit SHA)
            
        Returns:
            The file or directory contents
        """
        params = {
            "owner": owner,
            "repo": repo,
            "path": path
        }
        
        if ref:
            params["ref"] = ref
            
        return self._call_tool("get_file_contents", params)
    
    def create_or_update_file(self, owner: str, repo: str, path: str, message: str, content: str, 
                             branch: Optional[str] = None, sha: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or update a file in a repository.
        
        Args:
            owner: The repository owner
            repo: The repository name
            path: The file path
            message: The commit message
            content: The file content
            branch: The branch name (optional)
            sha: The file SHA if updating (optional)
            
        Returns:
            The result of the operation
        """
        params = {
            "owner": owner,
            "repo": repo,
            "path": path,
            "message": message,
            "content": content
        }
        
        if branch:
            params["branch"] = branch
            
        if sha:
            params["sha"] = sha
            
        return self._call_tool("create_or_update_file", params)
    
    def list_branches(self, owner: str, repo: str, page: int = 1, per_page: int = 30) -> Dict[str, Any]:
        """
        List branches in a repository.
        
        Args:
            owner: The repository owner
            repo: The repository name
            page: The page number (optional)
            per_page: The number of results per page (optional)
            
        Returns:
            The list of branches
        """
        params = {
            "owner": owner,
            "repo": repo,
            "page": page,
            "perPage": per_page
        }
        
        return self._call_tool("list_branches", params)
    
    def create_branch(self, owner: str, repo: str, branch: str, sha: str) -> Dict[str, Any]:
        """
        Create a new branch in a repository.
        
        Args:
            owner: The repository owner
            repo: The repository name
            branch: The new branch name
            sha: The SHA to create the branch from
            
        Returns:
            The result of the operation
        """
        params = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "sha": sha
        }
        
        return self._call_tool("create_branch", params)
    
    # ------------ Issue Tools ------------ #
    
    def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """
        Get the details of an issue.
        
        Args:
            owner: The repository owner
            repo: The repository name
            issue_number: The issue number
            
        Returns:
            The issue details
        """
        params = {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number
        }
        
        return self._call_tool("get_issue", params)
    
    def create_issue(self, owner: str, repo: str, title: str, body: Optional[str] = None,
                    assignees: Optional[List[str]] = None, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new issue in a repository.
        
        Args:
            owner: The repository owner
            repo: The repository name
            title: The issue title
            body: The issue body (optional)
            assignees: The users to assign to the issue (optional)
            labels: The labels to apply to the issue (optional)
            
        Returns:
            The created issue
        """
        params = {
            "owner": owner,
            "repo": repo,
            "title": title
        }
        
        if body:
            params["body"] = body
            
        if assignees:
            params["assignees"] = assignees
            
        if labels:
            params["labels"] = labels
            
        return self._call_tool("create_issue", params)
    
    def add_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            owner: The repository owner
            repo: The repository name
            issue_number: The issue number
            body: The comment text
            
        Returns:
            The created comment
        """
        params = {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number,
            "body": body
        }
        
        return self._call_tool("add_issue_comment", params)
    
    # ------------ Pull Request Tools ------------ #
    
    def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str,
                           body: Optional[str] = None, draft: bool = False) -> Dict[str, Any]:
        """
        Create a new pull request.
        
        Args:
            owner: The repository owner
            repo: The repository name
            title: The pull request title
            head: The branch containing changes
            base: The branch to merge into
            body: The pull request description (optional)
            draft: Whether to create a draft pull request (optional)
            
        Returns:
            The created pull request
        """
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "head": head,
            "base": base
        }
        
        if body:
            params["body"] = body
            
        if draft:
            params["draft"] = draft
            
        return self._call_tool("create_pull_request", params)
    
    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """
        Get the details of a pull request.
        
        Args:
            owner: The repository owner
            repo: The repository name
            pull_number: The pull request number
            
        Returns:
            The pull request details
        """
        params = {
            "owner": owner,
            "repo": repo,
            "pullNumber": pull_number
        }
        
        return self._call_tool("get_pull_request", params)
    
    def merge_pull_request(self, owner: str, repo: str, pull_number: int,
                          commit_title: Optional[str] = None,
                          commit_message: Optional[str] = None,
                          merge_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Merge a pull request.
        
        Args:
            owner: The repository owner
            repo: The repository name
            pull_number: The pull request number
            commit_title: The title for the merge commit (optional)
            commit_message: The message for the merge commit (optional)
            merge_method: The merge method (optional)
            
        Returns:
            The result of the operation
        """
        params = {
            "owner": owner,
            "repo": repo,
            "pullNumber": pull_number
        }
        
        if commit_title:
            params["commit_title"] = commit_title
            
        if commit_message:
            params["commit_message"] = commit_message
            
        if merge_method:
            params["merge_method"] = merge_method
            
        return self._call_tool("merge_pull_request", params)
    
    # ------------ User Tools ------------ #
    
    def get_me(self) -> Dict[str, Any]:
        """
        Get the authenticated user's details.
        
        Returns:
            The authenticated user's details
        """
        return self._call_tool("get_me", {})
    
    # ------------ Convenience Methods ------------ #
    
    def fix_issue_and_create_pr(self, issue_url: str, files_to_change: List[Dict[str, str]],
                               branch_name: Optional[str] = None, 
                               commit_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Fix an issue by changing files and create a pull request.
        
        Args:
            issue_url: The GitHub issue URL
            files_to_change: List of files to change, each with 'path' and 'content'
            branch_name: The name of the branch to create (optional)
            commit_message: The commit message (optional)
            
        Returns:
            The created pull request
        """
        # Parse the issue URL to get owner, repo, and issue number
        import re
        match = re.match(r"https://github.com/([^/]+)/([^/]+)/issues/(\d+)", issue_url)
        if not match:
            raise ValueError(f"Invalid GitHub issue URL: {issue_url}")
            
        owner, repo, issue_number = match.groups()
        issue_number = int(issue_number)
        
        # Get the issue details
        issue = self.get_issue(owner, repo, issue_number)
        
        # Get the default branch (main/master) if branch_name not provided
        if not branch_name:
            repo_info = self._call_tool("search_repositories", {"query": f"repo:{owner}/{repo}"})
            default_branch = repo_info["items"][0]["default_branch"]
            branch_name = f"fix-issue-{issue_number}"
            
        # Get the SHA of the default branch
        branches = self.list_branches(owner, repo)
        default_branch_info = next((b for b in branches["items"] if b["name"] == "main" or b["name"] == "master"), None)
        if not default_branch_info:
            raise ValueError("Could not determine default branch")
            
        sha = default_branch_info["commit"]["sha"]
        
        # Create a new branch
        self.create_branch(owner, repo, branch_name, sha)
        
        # Update files
        for file_info in files_to_change:
            path = file_info["path"]
            content = file_info["content"]
            
            # Check if file exists first
            try:
                existing_file = self.get_file_contents(owner, repo, path, branch_name)
                file_sha = existing_file["sha"]
                self.create_or_update_file(
                    owner, repo, path, 
                    commit_message or f"Fix issue #{issue_number}: {issue['title']}", 
                    content, branch_name, file_sha
                )
            except MCPToolError:
                # File doesn't exist, create it
                self.create_or_update_file(
                    owner, repo, path, 
                    commit_message or f"Fix issue #{issue_number}: {issue['title']}",
                    content, branch_name
                )
        
        # Create pull request
        pr_body = f"Fixes #{issue_number}\n\n{issue['body']}"
        pr = self.create_pull_request(
            owner, repo,
            title=f"Fix issue #{issue_number}: {issue['title']}",
            head=branch_name,
            base=default_branch_info["name"],
            body=pr_body
        )
        
        return pr