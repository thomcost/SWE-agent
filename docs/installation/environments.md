# Installation for Different Environments

This guide provides detailed setup instructions for SWE-agent in various environments.

## Table of Contents
- [Windows](#windows)
- [macOS](#macos)
- [Linux](#linux)
- [Docker](#docker)
- [AWS Cloud](#aws-cloud)
- [Azure Cloud](#azure-cloud)
- [GitHub Codespaces](#github-codespaces)

## Windows

### Prerequisites
- Python 3.9+ (we recommend using the [official Python installer](https://www.python.org/downloads/windows/))
- Git for Windows (install from [git-scm.com](https://git-scm.com/download/win))
- (Optional) Windows Terminal for a better CLI experience

### Installation Steps

1. Open Command Prompt or PowerShell as administrator

2. Clone the repository:
   ```powershell
   git clone https://github.com/SWE-agent/SWE-agent.git
   cd SWE-agent
   ```

3. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

4. Install the package:
   ```powershell
   pip install -e .
   ```

5. Set up API keys:
   ```powershell
   # For PowerShell
   $env:OPENAI_API_KEY = "your-openai-api-key"
   $env:ANTHROPIC_API_KEY = "your-anthropic-api-key"
   
   # For Command Prompt
   set OPENAI_API_KEY=your-openai-api-key
   set ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

### Windows Subsystem for Linux (WSL)

For better compatibility, consider using WSL:

1. Install WSL by running in PowerShell as administrator:
   ```powershell
   wsl --install
   ```

2. Once installed and set up, follow the [Linux](#linux) installation steps within your WSL environment.

## macOS

### Prerequisites
- Python 3.9+ (we recommend using [Homebrew](https://brew.sh/))
- Git

### Installation Steps

1. Install prerequisites (if not already installed):
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Python and Git
   brew install python git
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/SWE-agent/SWE-agent.git
   cd SWE-agent
   ```

3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the package:
   ```bash
   pip install -e .
   ```

5. Set up API keys:
   ```bash
   # For current session
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   
   # To persist across sessions, add to your shell profile (~/.zshrc or ~/.bash_profile)
   echo 'export OPENAI_API_KEY="your-openai-api-key"' >> ~/.zshrc
   echo 'export ANTHROPIC_API_KEY="your-anthropic-api-key"' >> ~/.zshrc
   ```

## Linux

### Prerequisites
- Python 3.9+
- Git
- Build essentials (for some dependencies)

### Installation Steps

1. Install prerequisites (Ubuntu/Debian example):
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv git build-essential
   ```

   For Red Hat/Fedora:
   ```bash
   sudo dnf install -y python3 python3-pip git gcc gcc-c++ make
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/SWE-agent/SWE-agent.git
   cd SWE-agent
   ```

3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the package:
   ```bash
   pip install -e .
   ```

5. Set up API keys:
   ```bash
   # For current session
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   
   # To persist across sessions, add to your shell profile (~/.bashrc)
   echo 'export OPENAI_API_KEY="your-openai-api-key"' >> ~/.bashrc
   echo 'export ANTHROPIC_API_KEY="your-anthropic-api-key"' >> ~/.bashrc
   ```

## Docker

Using Docker provides an isolated environment with all dependencies pre-installed.

### Prerequisites
- Docker Engine installed ([Installation guide](https://docs.docker.com/engine/install/))

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/SWE-agent/SWE-agent.git
   cd SWE-agent
   ```

2. Build the Docker image:
   ```bash
   docker build -t swe-agent .
   ```

3. Run the container with your API keys:
   ```bash
   docker run -it \
     -e OPENAI_API_KEY="your-openai-api-key" \
     -e ANTHROPIC_API_KEY="your-anthropic-api-key" \
     swe-agent python -m sweagent run -c config/beginner_friendly.yaml
   ```

4. For persistent storage, mount a volume:
   ```bash
   docker run -it \
     -v $(pwd)/data:/app/data \
     -e OPENAI_API_KEY="your-openai-api-key" \
     -e ANTHROPIC_API_KEY="your-anthropic-api-key" \
     swe-agent python -m sweagent run -c config/beginner_friendly.yaml
   ```

## AWS Cloud

Running SWE-agent on AWS EC2 or AWS Lambda for serverless operations.

### EC2 Installation

1. Launch an EC2 instance (Ubuntu recommended)
   - Use at least a t2.medium instance type for reasonable performance
   - Ensure you have at least 8GB of RAM and 20GB of storage

2. SSH into your instance and follow the [Linux](#linux) installation steps

3. To run SWE-agent as a service, create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/swe-agent.service
   ```

4. Add the following content:
   ```
   [Unit]
   Description=SWE-agent Service
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/SWE-agent
   Environment="OPENAI_API_KEY=your-openai-api-key"
   Environment="ANTHROPIC_API_KEY=your-anthropic-api-key"
   ExecStart=/home/ubuntu/SWE-agent/venv/bin/python -m sweagent.api.server
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable swe-agent
   sudo systemctl start swe-agent
   ```

### AWS Lambda (Serverless)

For serverless operation, you can use AWS Lambda with API Gateway:

1. Package SWE-agent as a Lambda function (simplified example):
   ```bash
   # Create a deployment package
   pip install -t package -e .
   cd package
   zip -r ../lambda_function.zip .
   ```

2. Create an AWS Lambda function with Python 3.9+ runtime
   - Upload the ZIP package
   - Set environment variables for your API keys
   - Set the handler to `sweagent.api.lambda_handler.handler`

3. Configure API Gateway to trigger your Lambda function

## Azure Cloud

### Azure VM Installation

1. Create an Azure VM (Ubuntu recommended)
   - Choose at least Standard_D2s_v3 (2 vCPUs, 8 GB RAM)

2. SSH into your VM and follow the [Linux](#linux) installation steps

### Azure App Service

1. Create an Azure App Service (Linux) with Python 3.9+

2. Configure the app settings to include your API keys:
   - `OPENAI_API_KEY`: your-openai-api-key
   - `ANTHROPIC_API_KEY`: your-anthropic-api-key

3. Set up deployment using Azure DevOps or GitHub Actions

## GitHub Codespaces

The easiest way to get started is with GitHub Codespaces, which provides a fully-configured environment in the browser.

1. Go to the [SWE-agent repository](https://github.com/SWE-agent/SWE-agent)

2. Click the "Code" button, select the "Codespaces" tab, and click "Create codespace on main"

3. Once the Codespace launches, set up your API keys:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

4. Run SWE-agent:
   ```bash
   python -m sweagent run -c config/beginner_friendly.yaml
   ```

## Troubleshooting Common Issues

### API Key Issues
- Ensure your API keys are correctly set in environment variables
- Check that your API keys have sufficient quota and are valid
- For persistent access, add keys to your shell profile or environment configuration

### Python Version Problems
- SWE-agent requires Python 3.9 or higher
- Check your Python version: `python --version` or `python3 --version`
- If you have multiple Python installations, ensure you're using the correct one

### Dependency Conflicts
- If you encounter package conflicts, create a fresh virtual environment
- Some packages may require system-level dependencies. On Ubuntu/Debian:
  ```bash
  sudo apt install -y python3-dev build-essential
  ```

### Memory Issues
- SWE-agent can require significant memory when processing large repositories
- Ensure you have at least 4GB of RAM available
- For large repositories, increase the available memory or use a larger VM instance