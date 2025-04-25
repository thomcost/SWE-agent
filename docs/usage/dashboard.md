---
title: "Monitoring Dashboard"
---

# SWE-Agent Dashboard

SWE-agent includes a real-time monitoring dashboard to track agent activities and performance metrics. This dashboard provides valuable insights into how your agents are performing, helping you optimize their configuration and troubleshoot issues.

## Starting the Dashboard

To start the dashboard server, run:

```bash
python -m sweagent.dashboard.run
```

Then open your browser and navigate to [http://localhost:8050](http://localhost:8050).

## Command Line Options

The dashboard server supports several command line options:

```bash
python -m sweagent.dashboard.run --help

# Options:
#   --host HOST         Host to bind the server to (default: 0.0.0.0)
#   --port PORT         Port to bind the server to (default: 8050)
#   --debug             Run the server in debug mode
#   --sample-data       Add sample data to the dashboard
#   --sample-count COUNT  Number of sample data entries to add (default: 100)
```

## Dashboard Features

The dashboard provides the following metrics and visualizations:

### Task Success Rate

Tracks the percentage of successfully completed tasks over time.

### Token Usage

Displays token consumption by your agents, helping you monitor API costs.

### Execution Time

Shows the average execution time for agent tasks, allowing you to identify performance bottlenecks.

### Task Distribution

Visualizes the distribution of different task types, giving you insights into your agents' workload.

### Model Performance

Compares different language models based on success rate and execution time, helping you choose the most effective model for your tasks.

### Recent Activities

Lists recent agent activities with details such as status, model used, tokens consumed, and execution time.

## Integrating with Your Agents

To log agent activities to the dashboard, use the `DashboardHook` in your agent configuration:

```python
from sweagent.agent.hooks import DashboardHook

# Create the hook
dashboard_hook = DashboardHook(agent_id="my-agent")

# Add the hook to your agent
agent.add_hook(dashboard_hook)
```

All agent activities will be automatically logged to the dashboard database.

## Manual Logging

You can also log activities manually using the logger module:

```python
from sweagent.dashboard.logger import log_activity

# Log a successful task
log_activity(
    agent_id="agent-1",
    task_id="task-123",
    task_type="Code Fix",
    status="success",
    model="GPT-4",
    tokens_used=2500,
    execution_time=18.5
)

# Log a failed task
log_activity(
    agent_id="agent-2",
    task_id="task-124",
    task_type="Vulnerability Scan",
    status="failure",
    model="Claude-3",
    tokens_used=1800,
    execution_time=12.3,
    error="API rate limit exceeded"
)
```

## Testing with Sample Data

For testing or demonstration purposes, you can generate sample data:

```bash
python -m sweagent.dashboard.run --sample-data --sample-count 200
```

Or programmatically:

```python
from sweagent.dashboard.logger import add_sample_data

# Add 100 sample data entries
add_sample_data(num_entries=100)
```

## Dashboard Architecture

The dashboard consists of the following components:

- **app.py**: Main Dash application file
- **logger.py**: Logging module for recording agent activities
- **assets/styles.css**: CSS styles for the dashboard
- **activity_logs.db**: SQLite database for storing logs and metrics

The dashboard uses a SQLite database with two main tables:

1. **activities**: Stores individual agent activities
2. **metrics**: Stores aggregated daily metrics