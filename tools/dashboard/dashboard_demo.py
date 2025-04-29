#!/usr/bin/env python
"""
Simple demo of the SWE-agent dashboard without external dependencies.
"""

import os
import sys
import random
import sqlite3
import datetime
from pathlib import Path

# Create database directory
DB_DIR = Path("./dashboard_demo")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "activity_logs.db"

def initialize_db():
    """Initialize the SQLite database with necessary tables."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        agent_id TEXT,
        task_id TEXT,
        task_type TEXT,
        status TEXT,
        model TEXT,
        tokens_used INTEGER,
        execution_time REAL,
        error TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        total_tasks INTEGER,
        successful_tasks INTEGER,
        failed_tasks INTEGER,
        total_tokens INTEGER,
        avg_execution_time REAL
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def add_sample_data(num_entries=100):
    """Add sample data for testing and demonstration."""
    # Sample data parameters
    models = ["GPT-4", "Claude-3", "Gemini", "Cohere", "LLaMA-3"]
    task_types = ["Code Fix", "Vulnerability Scan", "Code Review", "Documentation", "Testing", "Other"]
    statuses = ["success", "failure"]
    agents = [f"agent-{i}" for i in range(1, 6)]
    errors = [
        "",
        "API rate limit exceeded",
        "Model context window exceeded",
        "Authentication failed",
        "Network error",
        "Invalid input format"
    ]
    
    # Generate random activities over the last 30 days
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    for i in range(num_entries):
        # Generate random data
        timestamp = datetime.datetime.now() - datetime.timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        agent_id = random.choice(agents)
        task_id = f"task-{random.randint(1, 999)}"
        task_type = random.choice(task_types)
        status_weights = [0.85, 0.15]  # 85% success, 15% failure
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        model = random.choice(models)
        tokens_used = random.randint(1000, 5000)
        execution_time = random.uniform(10.0, 30.0)
        error = "" if status == "success" else random.choice(errors[1:])
        
        # Insert activity
        cursor.execute('''
        INSERT INTO activities 
        (timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp.strftime("%Y-%m-%d %H:%M:%S"), agent_id, task_id, task_type, status, model, tokens_used, execution_time, error))
        
        # Update metrics table (by date)
        date = timestamp.strftime("%Y-%m-%d")
        cursor.execute("SELECT * FROM metrics WHERE date = ?", (date,))
        row = cursor.fetchone()
        
        if row:
            # Update existing entry
            cursor.execute('''
            UPDATE metrics
            SET total_tasks = total_tasks + 1,
                successful_tasks = successful_tasks + ?,
                failed_tasks = failed_tasks + ?,
                total_tokens = total_tokens + ?,
                avg_execution_time = (avg_execution_time * total_tasks + ?) / (total_tasks + 1)
            WHERE date = ?
            ''', (1 if status == "success" else 0, 1 if status == "failure" else 0, tokens_used, execution_time, date))
        else:
            # Create new entry
            cursor.execute('''
            INSERT INTO metrics
            (date, total_tasks, successful_tasks, failed_tasks, total_tokens, avg_execution_time)
            VALUES (?, 1, ?, ?, ?, ?)
            ''', (date, 1 if status == "success" else 0, 1 if status == "failure" else 0, tokens_used, execution_time))
    
    conn.commit()
    conn.close()
    print(f"Added {num_entries} sample data entries")

def print_instructions():
    """Print instructions for viewing the dashboard."""
    print("\n===== SWE-Agent Dashboard Demo =====")
    print(f"Sample data has been generated in {DB_PATH}")
    print("\nTo start the dashboard, you need to install the required packages:")
    print("  pip install dash dash-bootstrap-components plotly pandas")
    print("\nThen create a file called 'run_dashboard.py' with the following content:")
    
    dashboard_code = """#!/usr/bin/env python
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime
import sqlite3
from pathlib import Path

# Path to the database
DB_PATH = Path("./dashboard_demo/activity_logs.db")

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# Dashboard layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("SWE-Agent Dashboard", className="dashboard-title"), width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Task Success Rate", className="card-title"),
                    dcc.Graph(id="success-rate-chart")
                ])
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Token Usage", className="card-title"),
                    dcc.Graph(id="token-usage-chart")
                ])
            ])
        ], width=6)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Model Performance", className="card-title"),
                    dcc.Graph(id="model-performance-chart")
                ])
            ])
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Recent Activities", className="card-title"),
                    html.Div(id="activity-log-table")
                ])
            ])
        ], width=12)
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds (5 seconds)
        n_intervals=0
    )
], fluid=True)

# Callback for success rate chart
@callback(
    Output("success-rate-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_success_rate(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql('''
        SELECT date, 
               successful_tasks * 100.0 / CASE WHEN total_tasks = 0 THEN 1 ELSE total_tasks END as success_rate
        FROM metrics
        ORDER BY date
        LIMIT 30
    ''', conn)
    conn.close()
    
    fig = px.line(
        df, 
        x="date", 
        y="success_rate",
        title="Success Rate Over Time",
        labels={"date": "Date", "success_rate": "Success Rate (%)"}
    )
    
    return fig

# Callback for token usage chart
@callback(
    Output("token-usage-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_token_usage(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql('''
        SELECT date, total_tokens
        FROM metrics
        ORDER BY date
        LIMIT 30
    ''', conn)
    conn.close()
    
    fig = px.bar(
        df, 
        x="date", 
        y="total_tokens",
        title="Token Usage by Day",
        labels={"date": "Date", "total_tokens": "Tokens Used"}
    )
    
    return fig

# Callback for model performance chart
@callback(
    Output("model-performance-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_model_performance(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql('''
        SELECT model, 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
               AVG(execution_time) as avg_time,
               AVG(tokens_used) as avg_tokens
        FROM activities
        GROUP BY model
        ORDER BY total DESC
    ''', conn)
    conn.close()
    
    # Calculate success rate
    df["success_rate"] = df["success"] / df["total"] * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df["model"],
        y=df["success_rate"],
        name="Success Rate (%)",
        marker_color="#4CAF50"
    ))
    
    fig.add_trace(go.Bar(
        x=df["model"],
        y=df["avg_time"],
        name="Avg. Time (s)",
        marker_color="#2196F3",
        yaxis="y2"
    ))
    
    fig.update_layout(
        barmode="group",
        title="Model Performance Comparison",
        yaxis=dict(
            title="Success Rate (%)",
            side="left"
        ),
        yaxis2=dict(
            title="Avg. Time (s)",
            overlaying="y",
            side="right"
        ),
        legend=dict(orientation="h", y=-0.2)
    )
    
    return fig

# Callback for activity log table
@callback(
    Output("activity-log-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_activity_log(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql('''
        SELECT timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error
        FROM activities
        ORDER BY timestamp DESC
        LIMIT 10
    ''', conn)
    conn.close()
    
    # Create the table
    table_header = [
        html.Thead(html.Tr([
            html.Th("Time"),
            html.Th("Agent"),
            html.Th("Task ID"),
            html.Th("Type"),
            html.Th("Status"),
            html.Th("Model"),
            html.Th("Tokens"),
            html.Th("Time (s)"),
            html.Th("Error")
        ]))
    ]
    
    rows = []
    for i, row in df.iterrows():
        status_style = {"color": "green"} if row["status"] == "success" else {"color": "red"}
        rows.append(html.Tr([
            html.Td(row["timestamp"]),
            html.Td(row["agent_id"]),
            html.Td(row["task_id"]),
            html.Td(row["task_type"]),
            html.Td(row["status"], style=status_style),
            html.Td(row["model"]),
            html.Td(f"{row['tokens_used']:,}"),
            html.Td(f"{row['execution_time']:.1f}"),
            html.Td(row["error"])
        ]))
    
    table_body = [html.Tbody(rows)]
    
    return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True)

if __name__ == "__main__":
    print("Starting dashboard server at http://localhost:8050")
    app.run_server(debug=True, host="localhost", port=8050)
"""
    
    print("\n" + "=" * 40)
    print(dashboard_code)
    print("=" * 40)
    
    print("\nRun the dashboard with:")
    print("  python run_dashboard.py")
    print("\nYou'll then be able to view the dashboard at: http://localhost:8050")

if __name__ == "__main__":
    print("Setting up SWE-agent dashboard demo...")
    initialize_db()
    add_sample_data(200)
    print_instructions()