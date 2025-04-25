# SWE-agent Quick Start Guide

This guide will help you get up and running with SWE-agent quickly. For more detailed information, please refer to the [full documentation](https://swe-agent.com).

## Prerequisites

Before using SWE-agent, ensure you have:

- Python 3.9+
- Git
- API keys for your preferred LLM provider (OpenAI or Anthropic)

## Installation

### Option 1: Using GitHub Codespaces (Recommended for First-Time Users)

The easiest way to get started is to use GitHub Codespaces:

1. Click [![Open in GitHub Codespaces](https://img.shields.io/badge/Open_in_GitHub_Codespaces-gray?logo=github)](https://codespaces.new/SWE-agent/SWE-agent)
2. Wait for the environment to set up (takes a few minutes)
3. Follow the instructions in the terminal to set up your API keys

### Option 2: Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SWE-agent/SWE-agent.git
   cd SWE-agent
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Set up your API keys:
   ```bash
   # For OpenAI
   export OPENAI_API_KEY=your_openai_api_key

   # For Anthropic
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

## Using SWE-agent

### Basic Usage

1. For first-time users, use our beginner-friendly config:
   ```bash
   python -m sweagent run -c config/beginner_friendly.yaml
   ```

2. To solve a GitHub issue:
   ```bash
   python -m sweagent run --repo_name owner/repo --issue_number 123
   ```

3. To run a coding challenge:
   ```bash
   python -m sweagent run -c config/coding_challenge.yaml
   ```

### Using the Inspector UI

The inspector UI helps you visualize and interact with the AI agent:

```bash
python -m sweagent.inspector.server
```

Then open your browser at http://localhost:8000

### Common Commands and Tools

When SWE-agent is running, it provides these tools to interact with the environment:

- `ls` - List files in the current directory
- `find_file "pattern"` - Search for files matching a pattern
- `search "pattern"` - Search for code containing a pattern
- `open file_path` - Open a file for viewing
- `goto line_number` - Go to a specific line in the open file
- `edit` - Edit the current file
- `submit` - Submit your solution when finished

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure your API keys are correctly set in environment variables
   - Check that you have sufficient credits/quota for your LLM provider

2. **Installation Problems**
   - Make sure you have Python 3.9+ installed: `python --version`
   - If you encounter package conflicts, try using a clean virtual environment

3. **Runtime Errors**
   - Check the logs for detailed error messages
   - Ensure you're using a supported configuration

### Getting Help

- Join our [Discord community](https://discord.gg/AVEFbBn2rH) for real-time support
- Open an [issue on GitHub](https://github.com/SWE-agent/SWE-agent/issues) for bug reports
- Check our [FAQ page](https://swe-agent.com/latest/faq/) for more troubleshooting tips

## Next Steps

- Explore [custom configurations](https://swe-agent.com/latest/config/)
- Learn about [batch mode](https://swe-agent.com/latest/usage/batch_mode/) for handling multiple issues
- Try the [cybersecurity mode](https://enigma-agent.com/) for capturing flags