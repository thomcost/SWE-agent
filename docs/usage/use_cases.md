# Common Use Cases

This guide covers common use cases for SWE-agent and provides step-by-step tutorials for each scenario.

## Table of Contents
- [Fixing GitHub Issues](#fixing-github-issues)
- [Solving Coding Challenges](#solving-coding-challenges)
- [Finding Security Vulnerabilities](#finding-security-vulnerabilities)
- [Code Analysis and Refactoring](#code-analysis-and-refactoring)
- [Custom Workflows](#custom-workflows)
- [Batch Processing](#batch-processing)
- [Integration with CI/CD](#integration-with-cicd)

## Fixing GitHub Issues

SWE-agent excels at fixing issues in real GitHub repositories.

### Basic Issue Resolution

1. **Find a GitHub issue to fix**
   - GitHub issues often describe bugs, feature requests, or other code problems
   - Look for issues with clear reproduction steps and expectations

2. **Run SWE-agent with the issue URL**:
   ```bash
   python -m sweagent run --repo_name owner/repo --issue_number 123
   ```

3. **Review and submit the solution**:
   - SWE-agent will clone the repository, analyze the issue, and develop a fix
   - Use the GitHub PR tool to submit your solution:
   ```bash
   python -m sweagent.tools.github_pr.bin.create_pr \
     --repo_path="/path/to/repo" \
     --branch_name="fix-issue-123" \
     --title="Fix issue #123" \
     --body="This PR fixes the issue by addressing the root cause..."
   ```

### Real-World Example: Fixing a Marshmallow Issue

Let's walk through fixing [marshmallow-code/marshmallow#1867](https://github.com/marshmallow-code/marshmallow/issues/1867):

1. **Run SWE-agent**:
   ```bash
   python -m sweagent run --repo_name marshmallow-code/marshmallow --issue_number 1867
   ```

2. **What happens behind the scenes**:
   - SWE-agent clones the marshmallow repository
   - It reads the issue description and understands the problem: `from_dict` method of Schema is mistakenly loading data in addition to deserializing it
   - It analyzes the relevant code files
   - It identifies and modifies the problematic code
   - It verifies the fix by running tests

3. **Understanding the fix process**:
   - SWE-agent first tests to reproduce the issue
   - It identifies the root cause in the `Schema.from_dict` method
   - It fixes the implementation to ensure it only deserializes without loading
   - It adds or modifies unit tests to verify the fix
   - It explains the reasoning behind the changes

## Solving Coding Challenges

SWE-agent can solve coding challenges and programming puzzles.

### LeetCode-Style Problems

1. **Create a description of the challenge**:
   Create a file called `problem.md` with the challenge description:
   ```markdown
   # Two Sum
   
   Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.
   
   You may assume that each input would have exactly one solution, and you may not use the same element twice.
   
   Example:
   Input: nums = [2,7,11,15], target = 9
   Output: [0,1]
   Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
   ```

2. **Run SWE-agent with the coding challenge configuration**:
   ```bash
   python -m sweagent run -c config/coding_challenge.yaml --problem_file problem.md
   ```

3. **Review the solution**:
   SWE-agent will generate a solution and explain its approach, time complexity, and space complexity.

### Competitive Programming Example

For competitive programming challenges:

1. **Create a problem statement**:
   ```
   # Maximum Subarray Sum
   
   Find the contiguous subarray within an array of integers that has the largest sum.
   
   Example:
   Input: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
   Output: 6
   Explanation: [4, -1, 2, 1] has the largest sum = 6.
   ```

2. **Run SWE-agent with specific test cases**:
   ```bash
   python -m sweagent run -c config/coding_challenge.yaml --problem_file problem.md --test_case_file test_cases.json
   ```
   
   Where `test_cases.json` might look like:
   ```json
   {
     "testCases": [
       {
         "input": [-2, 1, -3, 4, -1, 2, 1, -5, 4],
         "expected": 6
       },
       {
         "input": [1],
         "expected": 1
       },
       {
         "input": [-1],
         "expected": -1
       }
     ]
   }
   ```

## Finding Security Vulnerabilities

SWE-agent's EnIGMA mode is designed for finding security vulnerabilities.

### Analyzing Code for Security Issues

1. **Set up the target code**:
   - Prepare a repository with code you want to analyze
   - Make sure you have appropriate permissions

2. **Run SWE-agent in EnIGMA mode**:
   ```bash
   python -m sweagent run -c config/enigma.yaml --repo_path /path/to/repo
   ```

3. **Review vulnerability findings**:
   - SWE-agent will identify potential security issues
   - It will provide detailed explanations and remediations
   - It can generate proof-of-concept exploits for verification

### CTF Challenge Solving

For Capture The Flag challenges:

1. **Prepare the CTF challenge**:
   - Download the challenge files
   - Understand the challenge category (web, crypto, pwn, etc.)

2. **Run SWE-agent with the CTF configuration**:
   ```bash
   python -m sweagent run -c config/ctf.yaml --challenge_path /path/to/challenge
   ```

3. **Follow the solution process**:
   - SWE-agent will analyze the challenge
   - It will try different approaches to find the flag
   - It will explain its reasoning and techniques

## Code Analysis and Refactoring

SWE-agent can help analyze and refactor existing code.

### Code Quality Improvement

1. **Identify code that needs refactoring**:
   - Complex functions with high cyclomatic complexity
   - Repeated code patterns
   - Poorly organized code

2. **Run SWE-agent with the refactoring configuration**:
   ```bash
   python -m sweagent run -c config/refactoring.yaml --file_path /path/to/file.py
   ```

3. **Review and apply the suggestions**:
   - SWE-agent will identify code smells and suggest improvements
   - It will provide refactored versions of the code
   - It will ensure tests still pass after refactoring

### Dependency Updates

1. **Prepare your project**:
   - Ensure all dependencies are in requirements.txt or package.json
   - Make sure tests are available

2. **Run SWE-agent with the dependency update configuration**:
   ```bash
   python -m sweagent run -c config/dependency_update.yaml --repo_path /path/to/repo
   ```

3. **Review the changes**:
   - SWE-agent will analyze dependencies for updates
   - It will update dependencies and fix any compatibility issues
   - It will run tests to ensure everything still works

## Custom Workflows

SWE-agent supports custom workflows for specific needs.

### Creating a Custom Configuration

1. **Create a configuration file**:
   Create a file called `custom_config.yaml`:
   ```yaml
   agent:
     templates:
       system_template: |
         You are an autonomous software developer. Your task is to {{custom_task}}.
         Follow these guidelines:
         1. Analyze the existing code
         2. Understand the requirements
         3. Make necessary changes
         4. Test your solution
       instance_template: |
         We're working on a project located at {{repo_path}}.
         The specific task is: {{task_description}}
     tools:
       bundles:
         - path: tools/defaults
         - path: tools/search
         - path: tools/edit_replace
       enable_bash_tool: true
   ```

2. **Run SWE-agent with custom variables**:
   ```bash
   python -m sweagent run -c custom_config.yaml \
     --custom_task "optimize database queries" \
     --repo_path "/path/to/repo" \
     --task_description "Improve the performance of queries in user_service.py"
   ```

### Integration with Custom Tools

1. **Create a custom tool**:
   - Create a directory structure similar to existing tools
   - Implement the tool's functionality
   - Create a config.yaml file defining the tool

2. **Use the custom tool in your workflow**:
   ```yaml
   agent:
     tools:
       bundles:
         - path: tools/defaults
         - path: path/to/your/custom_tool
   ```

3. **Run SWE-agent with your custom configuration**:
   ```bash
   python -m sweagent run -c custom_config.yaml
   ```

## Batch Processing

SWE-agent can process multiple tasks in batch mode.

### Processing Multiple Issues

1. **Create a batch configuration file**:
   Create a file called `batch_issues.yaml`:
   ```yaml
   issues:
     - repo: owner1/repo1
       issue_number: 123
     - repo: owner1/repo1
       issue_number: 124
     - repo: owner2/repo2
       issue_number: 456
   ```

2. **Run SWE-agent in batch mode**:
   ```bash
   python -m sweagent run-batch -c config/default.yaml --instances batch_issues.yaml
   ```

3. **Review the results**:
   - SWE-agent will process each issue sequentially
   - Results will be saved in separate directories
   - A summary report will be generated

### Processing Multiple Files

1. **Create a batch configuration file for files**:
   ```yaml
   files:
     - path: /path/to/file1.py
       task: "Fix performance issues"
     - path: /path/to/file2.py
       task: "Add docstrings"
     - path: /path/to/file3.py
       task: "Refactor to use async/await"
   ```

2. **Run the batch process**:
   ```bash
   python -m sweagent run-batch -c config/default.yaml --instances batch_files.yaml
   ```

## Integration with CI/CD

SWE-agent can be integrated into CI/CD pipelines for automated code improvements.

### GitHub Actions Integration

1. **Create a GitHub Actions workflow file**:
   Create `.github/workflows/swe-agent.yml`:
   ```yaml
   name: SWE-agent Code Improvements
   
   on:
     issues:
       types: [opened, labeled]
     workflow_dispatch:
   
   jobs:
     fix-issue:
       runs-on: ubuntu-latest
       if: contains(github.event.issue.labels.*.name, 'ai-fix')
       steps:
         - uses: actions/checkout@v3
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.9'
             
         - name: Install SWE-agent
           run: |
             python -m pip install --upgrade pip
             git clone https://github.com/SWE-agent/SWE-agent.git
             cd SWE-agent
             pip install -e .
             
         - name: Run SWE-agent
           env:
             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
           run: |
             cd SWE-agent
             python -m sweagent run --repo_name ${{ github.repository }} --issue_number ${{ github.event.issue.number }}
             
         - name: Create Pull Request
           run: |
             cd SWE-agent
             python -m sweagent.tools.github_pr.bin.create_pr \
               --repo_path="${GITHUB_WORKSPACE}" \
               --branch_name="fix-issue-${{ github.event.issue.number }}" \
               --title="Fix #${{ github.event.issue.number }}" \
               --body="This PR was automatically generated by SWE-agent to fix issue #${{ github.event.issue.number }}"
   ```

2. **Use the workflow**:
   - Add the "ai-fix" label to issues you want SWE-agent to solve
   - The workflow will automatically run and create a PR with the fix

### GitLab CI Integration

1. **Create a GitLab CI configuration file**:
   Create `.gitlab-ci.yml`:
   ```yaml
   stages:
     - analyze
     - fix
   
   swe-agent-analyze:
     stage: analyze
     image: python:3.9
     script:
       - pip install git+https://github.com/SWE-agent/SWE-agent.git
       - python -m sweagent analyze --repo_path .
     artifacts:
       paths:
         - swe-agent-report.json
   
   swe-agent-fix:
     stage: fix
     image: python:3.9
     when: manual
     script:
       - pip install git+https://github.com/SWE-agent/SWE-agent.git
       - python -m sweagent run --repo_path . --report swe-agent-report.json
       - git config --global user.name "SWE-agent Bot"
       - git config --global user.email "swe-agent-bot@example.com"
       - git checkout -b fix-issues-$CI_PIPELINE_ID
       - git add .
       - git commit -m "Fix issues identified by SWE-agent"
       - git push origin fix-issues-$CI_PIPELINE_ID
     only:
       - main
   ```

2. **Use the pipeline**:
   - The analyze stage will run automatically
   - You can manually trigger the fix stage when ready