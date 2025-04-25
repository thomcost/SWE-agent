# What's New in SWE-agent

## Latest Enhancements (April 2024)

### Advanced Error Handling System

We've implemented a comprehensive error handling system that provides:

- Specialized error types for different categories (API, Network, FileSystem, etc.)
- Detailed error messages with recovery hints
- Retry mechanism with exponential backoff for transient errors
- Centralized error logging and reporting

To use this feature:

```python
from sweagent.utils.error_handler import retry, log_errors

# Add retry with exponential backoff to functions that may fail temporarily
@retry(max_attempts=5, backoff_factor=1.0)
def api_call():
    # This function will be retried up to 5 times if it fails
    
# Add error logging to functions
@log_errors(level=logging.ERROR)
def risky_operation():
    # Errors will be logged with full context
```

### Token Management and Optimization

We've added a token management system that helps optimize token usage and reduce API costs:

- Token counting and budgeting to prevent excessive API usage
- Response caching to avoid redundant API calls
- Text chunking and context optimization utilities

To use these features:

```python
from sweagent.utils.token_manager import cache_response, optimize_context

# Cache API responses to avoid redundant calls
@cache_response(ttl=3600)  # Cache for 1 hour
def generate_text(prompt, model="gpt-4"):
    # This function's responses will be cached by prompt and model
    
# Optimize context to fit within token limits
optimized_context = optimize_context(
    content={"system": long_system_prompt, "user": user_query},
    max_tokens=4000,
    priority_keys=["user"]  # Prioritize user queries over system prompt
)
```

### Beginner-Friendly Configuration

We've added a new beginner-friendly configuration file that includes comprehensive comments and explanations to help new users get started more easily. This configuration file includes:

- Detailed explanations for each configuration section
- Model configuration examples for both OpenAI and Anthropic
- Default values optimized for first-time users

To use this configuration:

```bash
python -m sweagent run -c config/beginner_friendly.yaml
```

### Quick Start Guide

We've added a new [QUICKSTART.md](../../QUICKSTART.md) file that provides:

- Simple installation instructions
- Basic usage examples
- Troubleshooting tips
- Common commands and tools reference

This guide is designed to help new users get up and running with SWE-agent as quickly as possible.

### Model Comparison Tool

The new model comparison tool allows you to run the same task with different LLMs and compare their performance. This is useful for:

- Benchmarking different models on the same task
- Testing the impact of different model parameters
- Evaluating new model releases against established baselines

To use this tool:

```bash
python -m sweagent.tools.model_comparison.bin.compare_models \
  --task="https://github.com/owner/repo/issues/123" \
  --models="gpt-4o,claude-3-sonnet-20240229" \
  --config="default.yaml" \
  --output="model_comparison_results"
```

### GitHub PR Integration

The new GitHub PR tool allows you to automatically create pull requests from SWE-agent's solutions. This is useful for:

- Streamlining the workflow from issue to pull request
- Integrating SWE-agent with existing GitHub workflows
- Automating the contribution process

To use this tool:

```bash
python -m sweagent.tools.github_pr.bin.create_pr \
  --repo_path="/path/to/repo" \
  --branch_name="fix-issue-123" \
  --title="Fix issue #123" \
  --body="This PR fixes the issue #123 by..."
```

## Previous Releases

For information about previous releases, please see the [changelog](../installation/changelog.md).