# SWE-Agent Dashboard

A real-time monitoring dashboard for SWE-agent activities and performance metrics.

## Features

- **Real-time monitoring** of agent activities
- **Visual metrics** for success rates, token usage, and execution times
- **Model performance comparison** across different LLM providers
- **Task distribution analysis** to understand workload patterns
- **Activity logs** for tracking recent operations

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages (listed in requirements.txt)

### Installation

1. Install the required packages:

```bash
cd sweagent/dashboard
pip install -r requirements.txt
```

2. Run the dashboard:

```bash
python app.py
```

3. Open your browser and navigate to `http://localhost:8050`

## Usage

### Adding Data to the Dashboard

To log agent activities and have them appear in the dashboard, use the `logger` module:

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

### Generating Sample Data

For testing and demonstration purposes, you can generate sample data:

```python
from sweagent.dashboard.logger import add_sample_data

# Add 100 sample data entries
add_sample_data(num_entries=100)
```

## Development

### Dashboard Structure

- **app.py**: Main dashboard application
- **logger.py**: Module for logging activities and metrics
- **assets/styles.css**: Custom styling for the dashboard
- **activity_logs.db**: SQLite database for storing logs and metrics

### Database Schema

The dashboard uses a SQLite database with two main tables:

1. **activities**: Stores individual agent activities
   - timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error

2. **metrics**: Stores aggregated daily metrics
   - date, total_tasks, successful_tasks, failed_tasks, total_tokens, avg_execution_time

## Integration

To integrate the dashboard with the SWE-agent, import the logger module and call `log_activity()` at appropriate points in your agent's workflow.

Example integration in the agent's main workflow:

```python
from sweagent.dashboard.logger import log_activity

def run_agent_task(agent_id, task_id, task_type, model, **kwargs):
    start_time = time.time()
    tokens_used = 0
    
    try:
        # Run agent task
        result = process_task(**kwargs)
        tokens_used = result.token_usage
        status = "success"
        error = ""
    except Exception as e:
        status = "failure"
        error = str(e)
    
    execution_time = time.time() - start_time
    
    # Log the activity
    log_activity(
        agent_id=agent_id,
        task_id=task_id,
        task_type=task_type,
        status=status,
        model=model,
        tokens_used=tokens_used,
        execution_time=execution_time,
        error=error
    )
    
    if status == "failure":
        raise Exception(error)
    
    return result
```