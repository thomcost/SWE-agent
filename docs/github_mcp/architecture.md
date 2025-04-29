# GitHub MCP Integration Architecture

This document provides an overview of the architecture for the GitHub Model Context Protocol (MCP) integration in SWE-agent.

## Architecture Diagram

![GitHub MCP Integration Architecture](https://mermaid.ink/img/pako:eNqFVU1v4jAQ_SsjX1rhFGmLxIVDV1q12u2BlVZVVE6YhFk3NrIdQFH43zsmgYQEXOcU-703M88zY38Ro0gQn-xeJgEGBvJJhXvCOTkx-x3YzUe2PnlvQFCvOWuXoXFHwh9Q-xRvHiuFNVDQICDzLfwuVs4wqt-9R_U7u8K6VVa9QzP_c_mZd3sPtvDRl_I4GbKBIAEMJTxQ_y4PiVg93EZ46vgV7g0yONnLHMNKxiEcVTMuKf7W-r7UVbQa-cU2DKjQR0EuGzAlnARUMfkKTrkgIdBfGPRs8yTjUEpIrVMwIeGTgGlXmF8FZS3Hfmk1vPRWjRtxOsIB7nXTu7FPVnLp4Q_oI3wFTUQZ_AxnOMQbIWOOkkb5LJJbTKM21eApxBD_kJBZHzFsKzj1U-1Fkwy94GGKfwHdKZgEFsVWRECnFGOc5C9eEu1AHvwA6PnmNLjCZyR1_jvOMVJPV_PVNG9R7bwm4bYsLbbDUTrZJtZZWOxJGG_ItdkdL51Nua-p9-qvW_Yw5e7qxzDjz6xGDTXL4pu4f-Gv0L_u3FgvDUqsRa5oawM1O7iFtXfcuaM_r1kOOx0YkNl3_XLwqY_aS78YFm6Gb4aFtwnzcU6tA9K5OqjBHuvU2vJCLp6NRHLZZiGGc4AxkZiFCXa9cmiIwcJNK3bOHDWmadYTjD-nifJO13Z0ncIkSrv6iM1wqU-Gg-ePKOzxK3LnVVw4Fct2Wl6QY-MJCjFsRBzTSOy9T0jVPWOKnl_eo5S2ylYc_-25jPuZjA1Xx8vYcA3Ht8kfYJGt7g?type=png)

## Diagram Description

The architecture diagram illustrates the structure and relationships of the GitHub MCP integration:

### SWE-agent Repository Components

- **Core Components**:
  - Core Agent (sweagent)
  - Monitoring Dashboard
  - Run Hooks System

- **GitHub MCP Integration**:
  - MCP Client: Handles API communication
  - MCP Server: Manages protocol integration
  - MCP Config: Stores configuration settings
  - MCP PR Hooks: Integrates with run hooks
  - Mock MCP Server: Provides testing environment

- **Tools & Examples**:
  - MCP Tools: Utility scripts
  - MCP Examples: Example implementations
  - MCP Tests: Test suite for MCP integration

- **Documentation**:
  - Integration Guide
  - Test Repository Guide
  - Architecture Diagram

### MCP Test Repository

- Test files for PR creation
- Issues for testing MCP integration
- Pull Requests created via MCP
- GitHub configuration templates

### External Components

- GitHub API
- Official GitHub MCP Server Docker container

### Connections

The diagram shows the flow of data and interactions between components, including:
- Integration between SWE-agent and the MCP test repository
- Communication channels to GitHub API
- Documentation references
- Submodule relationship between repositories

## Live Diagram

For an interactive version of the diagram, visit:
[Interactive Diagram](https://mermaid.live/edit#pako:eNqFVU1v4jAQ_SsjX1rhFGmLxIVDV1q12u2BlVZVVE6YhFk3NrIdQFH43zsmgYQEXOcU-703M88zY38Ro0gQn-xeJgEGBvJJhXvCOTkx-x3YzUe2PnlvQFCvOWuXoXFHwh9Q-xRvHiuFNVDQICDzLfwuVs4wqt-9R_U7u8K6VVa9QzP_c_mZd3sPtvDRl_I4GbKBIAEMJTxQ_y4PiVg93EZ46vgV7g0yONnLHMNKxiEcVTMuKf7W-r7UVbQa-cU2DKjQR0EuGzAlnARUMfkKTrkgIdBfGPRs8yTjUEpIrVMwIeGTgGlXmF8FZS3Hfmk1vPRWjRtxOsIB7nXTu7FPVnLp4Q_oI3wFTUQZ_AxnOMQbIWOOkkb5LJJbTKM21eApxBD_kJBZHzFsKzj1U-1Fkwy94GGKfwHdKZgEFsVWRECnFGOc5C9eEu1AHvwA6PnmNLjCZyR1_jvOMVJPV_PVNG9R7bwm4bYsLbbDUTrZJtZZWOxJGG_ItdkdL51Nua-p9-qvW_Yw5e7qxzDjz6xGDTXL4pu4f-Gv0L_u3FgvDUqsRa5oawM1O7iFtXfcuaM_r1kOOx0YkNl3_XLwqY_aS78YFm6Gb4aFtwnzcU6tA9K5OqjBHuvU2vJCLp6NRHLZZiGGc4AxkZiFCXa9cmiIwcJNK3bOHDWmadYTjD-nifJO13Z0ncIkSrv6iM1wqU-Gg-ePKOzxK3LnVVw4Fct2Wl6QY-MJCjFsRBzTSOy9T0jVPWOKnl_eo5S2ylYc_-25jPuZjA1Xx8vYcA3Ht8kfYJGt7g)