# Setting Up Docker for SWE-agent GitHub MCP Integration

This guide explains how to set up Docker in a WSL2 environment to run the GitHub MCP integration for SWE-agent.

## Docker Installation Options

There are several ways to install Docker in a WSL2 environment:

1. **Docker Desktop for Windows** (recommended if available)
   - Provides the most seamless integration between Windows and WSL2
   - Automatically configures WSL2 integration
   - Easy to manage through GUI

2. **Docker Engine directly in WSL2**
   - Works completely within the Linux environment
   - Requires manual installation
   - May have permission issues to resolve

3. **Docker from Microsoft's package repository**
   - Official method for installing on Ubuntu/Debian systems
   - Uses Microsoft's package repository

## Option 1: Docker Desktop for Windows (Recommended)

1. Download Docker Desktop for Windows from https://www.docker.com/products/docker-desktop/
2. Run the installer and follow the instructions
3. Ensure "Use WSL 2 instead of Hyper-V" is selected
4. After installation, open Docker Desktop settings
5. Go to "Resources" > "WSL Integration"
6. Enable integration with your Ubuntu distribution
7. Restart Docker Desktop

After installation, you should be able to run Docker commands in your WSL2 terminal.

## Option 2: Docker Engine directly in WSL2

1. Install Docker's prerequisites:
   ```bash
   sudo apt update
   sudo apt install -y \
       apt-transport-https \
       ca-certificates \
       curl \
       gnupg \
       lsb-release
   ```

2. Add Docker's official GPG key:
   ```bash
   sudo install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   sudo chmod a+r /etc/apt/keyrings/docker.gpg
   ```

3. Set up the Docker repository:
   ```bash
   echo \
     "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
     "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

4. Install Docker Engine:
   ```bash
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io
   ```

5. Add your user to the docker group to run Docker without sudo:
   ```bash
   sudo usermod -aG docker $USER
   ```

6. Restart your WSL session or log out and back in for the group changes to take effect

## Option 3: Using the Docker Installation Script

1. Download the installation script:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   ```

2. Run the script:
   ```bash
   sudo sh get-docker.sh
   ```

3. Add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```

4. Restart your WSL session

## Troubleshooting Docker in WSL2

### Docker Daemon Not Starting

If the Docker daemon doesn't start automatically:

```bash
sudo service docker start
```

Add this to your .bashrc or .zshrc to start Docker automatically:

```bash
if service docker status 2>&1 | grep -q "not running"; then
    sudo service docker start
fi
```

### Permission Denied Errors

If you see "permission denied" errors:

1. Verify your user is in the docker group:
   ```bash
   groups $USER
   ```

2. If not, add yourself again:
   ```bash
   sudo usermod -aG docker $USER
   ```

3. Apply group changes without logging out:
   ```bash
   newgrp docker
   ```

### WSL2 Networking Issues

If Docker can't connect to the internet:

1. Check your WSL2 networking:
   ```bash
   ping 8.8.8.8
   ```

2. If that doesn't work, restart the WSL service from PowerShell (as Administrator):
   ```powershell
   wsl --shutdown
   ```

## Testing Docker Installation

To verify Docker is working:

1. Check Docker version:
   ```bash
   docker --version
   ```

2. Run a test container:
   ```bash
   docker run hello-world
   ```

3. Try pulling the GitHub MCP Server image:
   ```bash
   docker pull ghcr.io/github/github-mcp-server
   ```

## Running GitHub MCP Tests

Once Docker is properly installed and running, you can test the GitHub MCP integration:

```bash
cd /mnt/c/Users/thoma/SWE-agent
source .venv/bin/activate
python test_standalone_github_mcp.py
```

This should successfully start the GitHub MCP Server in a Docker container and run the tests.