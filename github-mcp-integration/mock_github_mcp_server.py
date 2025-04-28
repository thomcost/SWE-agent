#!/usr/bin/env python3
"""
Mock GitHub MCP Server for development and testing.

This is a lightweight implementation of the GitHub Model Context Protocol (MCP) Server API
that can be used for development and testing when the official GitHub
MCP Server container doesn't work in your environment.
"""

import os
import json
import logging
import argparse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mock-github-mcp-server")

# Store GitHub token for auth
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
if not GITHUB_TOKEN:
    logger.warning("No GITHUB_PERSONAL_ACCESS_TOKEN set, authentication will fail")

# Mock data for responses
MOCK_USER = {
    "login": "mock-github-user",
    "id": 12345,
    "name": "Mock GitHub User",
    "email": "mock@example.com",
    "avatar_url": "https://example.com/avatar.png"
}

MOCK_BRANCHES = {
    "items": [
        {
            "name": "main",
            "protected": True,
            "commit": {
                "sha": "abc123main"
            }
        },
        {
            "name": "develop",
            "protected": False,
            "commit": {
                "sha": "abc123dev"
            }
        }
    ],
    "total_count": 2
}

MOCK_FILE_CONTENT = {
    "content": "IyBHaXRIdWIgTUNQIFNlcnZlcgoKVGhpcyBpcyBhIG1vY2sgUkVBRE1FIGZpbGUgZm9yIHRlc3RpbmcuCg==",  # Base64 encoded
    "encoding": "base64",
    "size": 50,
    "name": "README.md",
    "path": "README.md",
    "sha": "abc123"
}

MOCK_ISSUE = {
    "number": 123,
    "title": "Sample Issue Title",
    "body": "This is a sample issue description.",
    "state": "open",
    "assignee": None,
    "locked": False,
    "html_url": "https://github.com/mock-owner/mock-repo/issues/123"
}

MOCK_PR = {
    "number": 456,
    "title": "Sample PR Title",
    "body": "This is a sample PR description.",
    "state": "open",
    "html_url": "https://github.com/mock-owner/mock-repo/pull/456",
    "head": {
        "ref": "feature-branch"
    },
    "base": {
        "ref": "main"
    }
}

MOCK_REPO = {
    "name": "mock-repo",
    "full_name": "mock-owner/mock-repo",
    "default_branch": "main",
    "html_url": "https://github.com/mock-owner/mock-repo"
}

# In-memory storage for created resources
MOCK_STORAGE = {
    "branches": {},  # name -> branch data
    "files": {},     # path -> file content
    "issues": {},    # number -> issue data
    "prs": {}        # number -> PR data
}

# Define available tools for schema
AVAILABLE_TOOLS = [
    # User tools
    {
        "name": "get_authenticated_user",
        "description": "Get information about the authenticated user"
    },
    
    # Repository tools
    {
        "name": "get_repo",
        "description": "Get information about a repository"
    },
    {
        "name": "list_branches",
        "description": "List branches in a repository"
    },
    {
        "name": "get_branch",
        "description": "Get information about a branch"
    },
    {
        "name": "create_branch",
        "description": "Create a new branch in a repository"
    },
    
    # File tools
    {
        "name": "get_file_contents",
        "description": "Get contents of a file in a repository"
    },
    {
        "name": "create_or_update_file",
        "description": "Create or update a file in a repository"
    },
    
    # Issue tools
    {
        "name": "get_issue",
        "description": "Get information about an issue"
    },
    {
        "name": "create_issue",
        "description": "Create a new issue in a repository"
    },
    {
        "name": "add_issue_comment",
        "description": "Add a comment to an issue"
    },
    
    # Pull request tools
    {
        "name": "create_pull_request",
        "description": "Create a new pull request"
    },
    {
        "name": "get_pull_request",
        "description": "Get information about a pull request"
    },
    {
        "name": "merge_pull_request",
        "description": "Merge a pull request"
    }
]

class MockGitHubMCPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock GitHub MCP Server."""
    
    def _set_headers(self, status_code=200, content_type="application/json"):
        """Set response headers."""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
    
    def _verify_auth(self):
        """Verify GitHub token in Authorization header."""
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False
        
        token = auth_header.split(" ")[1]
        return token == GITHUB_TOKEN
    
    def _handle_ping(self):
        """Handle ping request."""
        self._set_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def _handle_schema(self):
        """Handle schema request."""
        schema = {
            "tools": AVAILABLE_TOOLS
        }
        self._set_headers()
        self.wfile.write(json.dumps(schema).encode())
        
    # Repository tool handlers
    def _handle_get_repo(self, args):
        """Handle get_repo tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        return MOCK_REPO
    
    def _handle_list_branches(self, args):
        """Handle list_branches tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        
        # Check if we have custom branches for this repo
        repo_key = f"{owner}/{repo}"
        if repo_key in MOCK_STORAGE["branches"]:
            return {
                "items": list(MOCK_STORAGE["branches"][repo_key].values()),
                "total_count": len(MOCK_STORAGE["branches"][repo_key])
            }
        
        return MOCK_BRANCHES
    
    def _handle_get_branch(self, args):
        """Handle get_branch tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        branch = args.get("branch", "main")
        
        # Check if we have this branch stored
        repo_key = f"{owner}/{repo}"
        if repo_key in MOCK_STORAGE["branches"] and branch in MOCK_STORAGE["branches"][repo_key]:
            return MOCK_STORAGE["branches"][repo_key][branch]
        
        # Return default from mock data
        for branch_data in MOCK_BRANCHES["items"]:
            if branch_data["name"] == branch:
                return branch_data
        
        return {
            "name": branch,
            "protected": False,
            "commit": {
                "sha": "abc123" + branch
            }
        }
    
    def _handle_create_branch(self, args):
        """Handle create_branch tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        branch = args.get("branch", "new-branch")
        sha = args.get("sha", "abc123")
        
        # Store the new branch
        repo_key = f"{owner}/{repo}"
        if repo_key not in MOCK_STORAGE["branches"]:
            MOCK_STORAGE["branches"][repo_key] = {}
            
        MOCK_STORAGE["branches"][repo_key][branch] = {
            "name": branch,
            "protected": False,
            "commit": {
                "sha": sha
            }
        }
        
        return {
            "name": branch,
            "protected": False,
            "commit": {
                "sha": sha
            }
        }
    
    # File tool handlers
    def _handle_get_file_contents(self, args):
        """Handle get_file_contents tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        path = args.get("path", "README.md")
        ref = args.get("ref")
        
        # Check if we have this file stored
        repo_key = f"{owner}/{repo}"
        file_key = f"{repo_key}/{path}"
        if file_key in MOCK_STORAGE["files"]:
            return MOCK_STORAGE["files"][file_key]
        
        # Return mock data
        return MOCK_FILE_CONTENT
    
    def _handle_create_or_update_file(self, args):
        """Handle create_or_update_file tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        path = args.get("path", "README.md")
        message = args.get("message", "Update file")
        content = args.get("content", "")
        branch = args.get("branch", "main")
        sha = args.get("sha")
        
        # Store the file
        repo_key = f"{owner}/{repo}"
        file_key = f"{repo_key}/{path}"
        
        import base64
        import hashlib
        
        # Generate a sha for the content
        content_sha = hashlib.sha1(content.encode()).hexdigest()
        
        MOCK_STORAGE["files"][file_key] = {
            "content": base64.b64encode(content.encode()).decode(),
            "encoding": "base64",
            "size": len(content),
            "name": path.split("/")[-1],
            "path": path,
            "sha": content_sha
        }
        
        return {
            "content": MOCK_STORAGE["files"][file_key],
            "commit": {
                "sha": "commit_" + content_sha,
                "message": message
            }
        }
    
    # Issue tool handlers
    def _handle_get_issue(self, args):
        """Handle get_issue tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        issue_number = args.get("issue_number", 123)
        
        # Check if we have this issue stored
        repo_key = f"{owner}/{repo}"
        issue_key = f"{repo_key}/{issue_number}"
        if issue_key in MOCK_STORAGE["issues"]:
            return MOCK_STORAGE["issues"][issue_key]
        
        # Return mock data
        return {
            **MOCK_ISSUE,
            "number": issue_number,
            "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}"
        }
    
    def _handle_create_issue(self, args):
        """Handle create_issue tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        title = args.get("title", "New Issue")
        body = args.get("body", "")
        assignees = args.get("assignees", [])
        labels = args.get("labels", [])
        
        # Generate a new issue number
        import random
        issue_number = random.randint(1000, 9999)
        
        # Store the issue
        repo_key = f"{owner}/{repo}"
        issue_key = f"{repo_key}/{issue_number}"
        
        MOCK_STORAGE["issues"][issue_key] = {
            "number": issue_number,
            "title": title,
            "body": body,
            "state": "open",
            "assignee": assignees[0] if assignees else None,
            "assignees": assignees,
            "labels": labels,
            "locked": False,
            "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}"
        }
        
        return MOCK_STORAGE["issues"][issue_key]
    
    def _handle_add_issue_comment(self, args):
        """Handle add_issue_comment tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        issue_number = args.get("issue_number", 123)
        body = args.get("body", "")
        
        # Generate a comment ID
        import random
        comment_id = random.randint(10000, 99999)
        
        return {
            "id": comment_id,
            "body": body,
            "user": MOCK_USER,
            "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}#comment-{comment_id}"
        }
    
    # PR tool handlers
    def _handle_create_pull_request(self, args):
        """Handle create_pull_request tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        title = args.get("title", "New PR")
        head = args.get("head", "feature-branch")
        base = args.get("base", "main")
        body = args.get("body", "")
        draft = args.get("draft", False)
        
        # Generate a new PR number
        import random
        pr_number = random.randint(100, 999)
        
        # Store the PR
        repo_key = f"{owner}/{repo}"
        pr_key = f"{repo_key}/{pr_number}"
        
        MOCK_STORAGE["prs"][pr_key] = {
            "number": pr_number,
            "title": title,
            "body": body,
            "state": "open",
            "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
            "draft": draft,
            "head": {
                "ref": head
            },
            "base": {
                "ref": base
            }
        }
        
        return MOCK_STORAGE["prs"][pr_key]
    
    def _handle_get_pull_request(self, args):
        """Handle get_pull_request tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        pull_number = args.get("pullNumber", 456)
        
        # Check if we have this PR stored
        repo_key = f"{owner}/{repo}"
        pr_key = f"{repo_key}/{pull_number}"
        if pr_key in MOCK_STORAGE["prs"]:
            return MOCK_STORAGE["prs"][pr_key]
        
        # Return mock data
        return {
            **MOCK_PR,
            "number": pull_number,
            "html_url": f"https://github.com/{owner}/{repo}/pull/{pull_number}"
        }
    
    def _handle_merge_pull_request(self, args):
        """Handle merge_pull_request tool."""
        owner = args.get("owner", "mock-owner")
        repo = args.get("repo", "mock-repo")
        pull_number = args.get("pullNumber", 456)
        commit_title = args.get("commit_title", "")
        commit_message = args.get("commit_message", "")
        merge_method = args.get("merge_method", "merge")
        
        # Check if we have this PR stored
        repo_key = f"{owner}/{repo}"
        pr_key = f"{repo_key}/{pull_number}"
        if pr_key in MOCK_STORAGE["prs"]:
            MOCK_STORAGE["prs"][pr_key]["state"] = "closed"
            MOCK_STORAGE["prs"][pr_key]["merged"] = True
        
        # Generate a merge commit SHA
        import hashlib
        merge_sha = hashlib.sha1(f"{owner}/{repo}#{pull_number}".encode()).hexdigest()
        
        return {
            "merged": True,
            "message": "Pull request successfully merged",
            "sha": merge_sha
        }
    
    def _handle_tool_call(self, tool_name):
        """Handle tool invocation."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        if not post_data:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "No request body"}).encode())
            return
        
        try:
            payload = json.loads(post_data.decode())
            args = payload.get("arguments", {})
            
            # Log tool call for debugging
            logger.info(f"Tool call: {tool_name} with args: {args}")
            
            # Process the tool call based on tool name
            try:
                if tool_name == "get_authenticated_user":
                    response = MOCK_USER
                
                # Repository-related tools
                elif tool_name == "get_repo":
                    response = self._handle_get_repo(args)
                elif tool_name == "list_branches":
                    response = self._handle_list_branches(args)
                elif tool_name == "get_branch":
                    response = self._handle_get_branch(args)
                elif tool_name == "create_branch":
                    response = self._handle_create_branch(args)
                
                # File-related tools
                elif tool_name == "get_file_contents":
                    response = self._handle_get_file_contents(args)
                elif tool_name == "create_or_update_file":
                    response = self._handle_create_or_update_file(args)
                
                # Issue-related tools
                elif tool_name == "get_issue":
                    response = self._handle_get_issue(args)
                elif tool_name == "create_issue":
                    response = self._handle_create_issue(args)
                elif tool_name == "add_issue_comment":
                    response = self._handle_add_issue_comment(args)
                
                # PR-related tools
                elif tool_name == "create_pull_request":
                    response = self._handle_create_pull_request(args)
                elif tool_name == "get_pull_request":
                    response = self._handle_get_pull_request(args)
                elif tool_name == "merge_pull_request":
                    response = self._handle_merge_pull_request(args)
                
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": f"Tool {tool_name} not found"}).encode())
                    return
            except Exception as e:
                logger.error(f"Error handling tool call: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": f"Internal server error: {str(e)}"}).encode())
                return
            
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
    
    def do_GET(self):
        """Handle GET requests."""
        logger.info(f"GET request to {self.path}")
        
        if self.path == "/mcp/v1/ping":
            self._handle_ping()
        elif self.path == "/mcp/v1/schema":
            self._handle_schema()
        elif self.path == "/":
            self._set_headers(200, "text/html")
            self.wfile.write(b"<html><body><h1>Mock GitHub MCP Server</h1></body></html>")
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        logger.info(f"POST request to {self.path}")
        
        # Extract tool name from path
        if self.path.startswith("/mcp/v1/tools/"):
            tool_name = self.path[len("/mcp/v1/tools/"):]
            self._handle_tool_call(tool_name)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

def run_server(port=7444):
    """Run the mock GitHub MCP Server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, MockGitHubMCPHandler)
    
    logger.info(f"Starting mock GitHub MCP Server on port {port}")
    logger.info(f"Available tools: {', '.join(t['name'] for t in AVAILABLE_TOOLS)}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        httpd.server_close()
        logger.info("Server closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a mock GitHub MCP Server")
    parser.add_argument(
        "--port", type=int, default=7444,
        help="Port to run the server on (default: 7444)"
    )
    
    args = parser.parse_args()
    run_server(args.port)