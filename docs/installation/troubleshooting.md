# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with SWE-agent.

## Table of Contents
- [API Key Issues](#api-key-issues)
- [Installation Problems](#installation-problems)
- [Runtime Errors](#runtime-errors)
- [Model-Related Issues](#model-related-issues)
- [Performance Problems](#performance-problems)
- [GitHub Integration Issues](#github-integration-issues)
- [Docker Issues](#docker-issues)
- [Cloud Deployment Issues](#cloud-deployment-issues)
- [Common Error Messages](#common-error-messages)

## API Key Issues

### Missing or Invalid API Keys

**Symptoms:** "Authentication Error", "Invalid API Key", or "Unauthorized"

**Solution:**
1. Verify your API keys are correctly set:
   ```bash
   # Check if the environment variables are set
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

2. Ensure your keys are correctly formatted:
   - OpenAI keys typically start with "sk-"
   - Anthropic keys typically start with "sk-ant-" 

3. If using a configuration file, check that the API keys are correctly specified.

### API Rate Limits

**Symptoms:** "Rate limit exceeded", "Too many requests", or "Quota exceeded"

**Solution:**
1. Check your API usage on your provider's dashboard
2. Implement rate limiting in your code:
   ```python
   import time
   import random
   
   def call_with_retry(func, max_retries=5):
       for i in range(max_retries):
           try:
               return func()
           except RateLimitError:
               # Exponential backoff with jitter
               time.sleep((2 ** i) + random.random())
       raise Exception("Max retries exceeded")
   ```
3. Consider upgrading your API tier for higher rate limits

## Installation Problems

### Python Version Issues

**Symptoms:** "Python version not supported", "ImportError", or package compatibility errors

**Solution:**
1. Check your Python version:
   ```bash
   python --version
   # or
   python3 --version
   ```

2. Install the correct Python version:
   - Windows: Download from [python.org](https://www.python.org/downloads/windows/)
   - macOS: `brew install python@3.9`
   - Linux: `sudo apt install python3.9`

3. Create a virtual environment with the correct Python version:
   ```bash
   # Example for Python 3.9
   python3.9 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

### Dependency Conflicts

**Symptoms:** "Dependency resolution failed", "Incompatible packages", or "Could not build wheel"

**Solution:**
1. Start with a clean virtual environment:
   ```bash
   python -m venv fresh_venv
   source fresh_venv/bin/activate
   ```

2. Install system dependencies (Ubuntu/Debian):
   ```bash
   sudo apt update
   sudo apt install -y python3-dev build-essential
   ```

3. Install with specific versions:
   ```bash
   pip install -e . --no-deps
   pip install -r requirements.txt
   ```

4. If a specific package is causing issues, try installing it separately:
   ```bash
   pip install problematic-package==specific-version
   ```

### Permission Errors

**Symptoms:** "Permission denied", "Access is denied", or "Operation not permitted"

**Solution:**
1. On Linux/macOS:
   ```bash
   # For system directories
   sudo pip install -e .
   
   # Or install in user space
   pip install --user -e .
   ```

2. On Windows:
   - Run Command Prompt or PowerShell as administrator
   - Use `--user` flag: `pip install --user -e .`

## Runtime Errors

### Missing Module Errors

**Symptoms:** "ModuleNotFoundError", "ImportError", or "No module named X"

**Solution:**
1. Ensure all dependencies are installed:
   ```bash
   pip install -e .
   ```

2. Check if you're running in the correct virtual environment

3. Reinstall the specific missing package:
   ```bash
   pip install missing-package-name
   ```

### Memory Errors

**Symptoms:** "MemoryError", "Killed", or program crashes silently

**Solution:**
1. Increase system swap space (Linux):
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

2. Use a machine with more RAM

3. Process repositories in smaller chunks:
   ```python
   # Instead of processing the entire repo, process files in batches
   files = list_files_in_repo()
   batch_size = 10
   for i in range(0, len(files), batch_size):
       batch = files[i:i+batch_size]
       process_files(batch)
   ```

### File Not Found Errors

**Symptoms:** "FileNotFoundError", "No such file or directory", or "The system cannot find the file specified"

**Solution:**
1. Check that paths are correctly specified and use absolute paths when necessary:
   ```python
   import os
   absolute_path = os.path.abspath("relative/path/to/file")
   ```

2. Verify file permissions:
   ```bash
   # On Linux/macOS
   ls -la /path/to/file
   
   # On Windows
   icacls C:\path\to\file
   ```

3. If working with repositories, ensure the repository was cloned correctly:
   ```bash
   git clone --recursive https://github.com/SWE-agent/SWE-agent.git
   ```

## Model-Related Issues

### Model Not Responding

**Symptoms:** Long delays, timeouts, or "Connection error"

**Solution:**
1. Check your internet connection

2. Verify the model service status:
   - [OpenAI Status](https://status.openai.com/)
   - [Anthropic Status](https://status.anthropic.com/)

3. Implement timeouts in your code:
   ```python
   import requests
   import timeout_decorator
   
   @timeout_decorator.timeout(30)  # 30 seconds timeout
   def call_model(prompt):
       # Your code to call the model
       pass
   ```

### Poor Model Output Quality

**Symptoms:** Irrelevant responses, hallucinations, or nonsensical code

**Solution:**
1. Adjust prompting strategy:
   - Make prompts more specific and detailed
   - Include examples of desired outputs
   - Break complex tasks into smaller steps

2. Use a more capable model:
   ```yaml
   # In your config file
   model:
     provider: anthropic
     model: claude-3-opus-20240229  # Higher capability model
     temperature: 0.1  # Lower temperature for more deterministic outputs
   ```

3. Implement post-processing and validation:
   ```python
   def validate_code_output(code):
       # Run syntax check
       try:
         compile(code, "<string>", "exec")
         return True
       except SyntaxError:
         return False
   ```

## Performance Problems

### Slow Execution

**Symptoms:** Operations taking much longer than expected

**Solution:**
1. Use parallel processing:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   def process_all_files(files):
       with ThreadPoolExecutor(max_workers=5) as executor:
           executor.map(process_file, files)
   ```

2. Optimize model token usage:
   - Use smaller context windows
   - Summarize long files before sending to the model
   - Focus only on relevant code sections

3. Enable caching:
   ```python
   import functools
   
   @functools.lru_cache(maxsize=100)
   def get_model_response(prompt):
       # Call model API
       pass
   ```

### High API Costs

**Symptoms:** Rapid consumption of API credits or high bills

**Solution:**
1. Use token counting to estimate costs:
   ```python
   import tiktoken
   
   def count_tokens(text, model="gpt-4"):
       encoder = tiktoken.encoding_for_model(model)
       return len(encoder.encode(text))
   ```

2. Implement a budget cap:
   ```python
   max_daily_tokens = 100000
   tokens_used_today = 0
   
   def track_token_usage(tokens):
       global tokens_used_today
       tokens_used_today += tokens
       if tokens_used_today > max_daily_tokens:
           raise Exception("Daily token budget exceeded")
   ```

3. Use less expensive models for simpler tasks:
   ```python
   def get_appropriate_model(task_complexity):
       if task_complexity == "low":
           return "gpt-3.5-turbo"  # Less expensive
       else:
           return "gpt-4o"  # More expensive but more capable
   ```

## GitHub Integration Issues

### Authentication Problems

**Symptoms:** "Authentication failed", "No credential helper", or "Permission denied"

**Solution:**
1. Check GitHub credentials:
   ```bash
   # Test GitHub authentication
   gh auth status
   ```

2. Set up token authentication:
   ```bash
   # Create a new token at https://github.com/settings/tokens
   gh auth login --with-token < mytoken.txt
   ```

3. Configure Git credentials:
   ```bash
   git config --global credential.helper store
   # Then perform an operation that requires authentication
   ```

### Repository Access Issues

**Symptoms:** "Repository not found", "Access denied", or "Permission denied"

**Solution:**
1. Verify repository access:
   ```bash
   # Test if you can clone the repository
   git clone https://github.com/owner/repo.git test-clone
   ```

2. Check repository visibility and permissions on GitHub

3. For private repositories, ensure proper authentication:
   ```bash
   # Use SSH instead of HTTPS
   git remote set-url origin git@github.com:owner/repo.git
   ```

## Docker Issues

### Container Build Failures

**Symptoms:** "Build failed", "Error during build", or "Failed to pull image"

**Solution:**
1. Check Dockerfile syntax:
   ```bash
   docker run --rm -i hadolint/hadolint < Dockerfile
   ```

2. Increase Docker resources (memory, CPU)

3. Use a multi-stage build to reduce image size:
   ```dockerfile
   # Build stage
   FROM python:3.9 AS builder
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Runtime stage
   FROM python:3.9-slim
   WORKDIR /app
   COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
   COPY . .
   ```

### Container Runtime Issues

**Symptoms:** "Container exited", "OOMKilled", or "Permission denied"

**Solution:**
1. Increase container resources:
   ```bash
   docker run --memory=4g --cpus=2 -it swe-agent
   ```

2. Fix permission issues:
   ```bash
   # Inside Dockerfile
   RUN chown -R 1000:1000 /app
   USER 1000
   ```

3. Check logs for detailed errors:
   ```bash
   docker logs container_name
   ```

## Cloud Deployment Issues

### AWS Deployment Problems

**Symptoms:** "Deployment failed", "Error creating resource", or "Access denied"

**Solution:**
1. Check IAM permissions:
   ```bash
   aws iam get-user
   aws iam list-attached-user-policies --user-name YOUR_USERNAME
   ```

2. Verify AWS region configuration:
   ```bash
   aws configure get region
   # Set region if needed
   aws configure set region us-west-2
   ```

3. Check CloudFormation or service-specific logs

### Azure Deployment Problems

**Symptoms:** "Deployment failed", "Resource provider not registered", or "Access denied"

**Solution:**
1. Register required providers:
   ```bash
   az provider register --namespace Microsoft.Compute
   az provider register --namespace Microsoft.Storage
   ```

2. Check resource group and location:
   ```bash
   az group show --name YOUR_RESOURCE_GROUP
   ```

3. Review deployment logs:
   ```bash
   az monitor activity-log list --resource-group YOUR_RESOURCE_GROUP
   ```

## Common Error Messages

### "Connection refused"

**Possible causes:**
- Service not running
- Firewall blocking connection
- Incorrect port or host

**Solution:**
1. Check if service is running:
   ```bash
   ps aux | grep service_name
   # or
   netstat -tuln | grep port_number
   ```

2. Check firewall settings:
   ```bash
   # Linux
   sudo ufw status
   
   # Windows
   netsh advfirewall show currentprofile
   ```

3. Verify correct host and port:
   ```bash
   ping hostname
   telnet hostname port
   ```

### "No space left on device"

**Possible causes:**
- Disk full
- Inode limit reached
- Temporary directory full

**Solution:**
1. Check disk space:
   ```bash
   df -h
   ```

2. Check inode usage:
   ```bash
   df -i
   ```

3. Clean up temporary files:
   ```bash
   rm -rf /tmp/*
   docker system prune -a
   ```

### "Too many open files"

**Possible causes:**
- File descriptor limit reached
- Resource leak in application

**Solution:**
1. Check current limits:
   ```bash
   ulimit -n
   ```

2. Increase limits temporarily:
   ```bash
   ulimit -n 8192
   ```

3. Increase limits permanently (Linux):
   ```bash
   echo "* soft nofile 8192" | sudo tee -a /etc/security/limits.conf
   echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
   ```

4. Check for resource leaks:
   ```bash
   lsof -p process_id | wc -l
   ```

## Getting Further Help

If you're still experiencing issues:

1. Check our [GitHub Issues](https://github.com/SWE-agent/SWE-agent/issues) to see if others have reported similar problems

2. Join our [Discord community](https://discord.gg/AVEFbBn2rH) for real-time help

3. Open a new issue with:
   - Detailed description of the problem
   - Steps to reproduce
   - Environment information
   - Logs and error messages

4. For API provider-specific issues, check their documentation:
   - [OpenAI Documentation](https://platform.openai.com/docs/)
   - [Anthropic Documentation](https://docs.anthropic.com/claude/)