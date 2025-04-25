#!/usr/bin/env python
"""
Dashboard for monitoring SWE-agent activities and performance.
Provides real-time metrics, visualizations, and logs for agent operations.
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import os
import datetime
from collections import defaultdict
import sqlite3
from pathlib import Path

# Initialize the database if it doesn't exist
DB_PATH = Path(__file__).parent / "activity_logs.db"

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

initialize_db()

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

server = app.server

# Define layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("SWE-Agent Dashboard", className="dashboard-title"), width=12)
    ], className="header-row"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Task Success Rate", className="card-title"),
                    dcc.Graph(id="success-rate-chart")
                ])
            ], className="dashboard-card")
        ], width=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Token Usage", className="card-title"),
                    dcc.Graph(id="token-usage-chart")
                ])
            ], className="dashboard-card")
        ], width=4),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Execution Time", className="card-title"),
                    dcc.Graph(id="execution-time-chart")
                ])
            ], className="dashboard-card")
        ], width=4)
    ], className="charts-row"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Task Distribution", className="card-title"),
                    dcc.Graph(id="task-distribution-chart")
                ])
            ], className="dashboard-card")
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Model Performance", className="card-title"),
                    dcc.Graph(id="model-performance-chart")
                ])
            ], className="dashboard-card")
        ], width=6)
    ], className="charts-row"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Recent Activities", className="card-title"),
                    html.Div(id="activity-log-table", className="activity-log")
                ])
            ], className="dashboard-card")
        ], width=12)
    ], className="log-row"),
    
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # in milliseconds (10 seconds)
        n_intervals=0
    )
], fluid=True, className="dashboard-container")

# Callback for updating success rate chart
@callback(
    Output("success-rate-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_success_rate(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("""
        SELECT date, 
               successful_tasks * 100.0 / CASE WHEN total_tasks = 0 THEN 1 ELSE total_tasks END as success_rate
        FROM metrics
        ORDER BY date
        LIMIT 30
    """, conn)
    conn.close()
    
    # If no data, create sample data
    if df.empty:
        dates = [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10, 0, -1)]
        df = pd.DataFrame({
            "date": dates,
            "success_rate": [85, 87, 82, 90, 88, 85, 92, 89, 86, 91]
        })
    
    fig = px.line(
        df, 
        x="date", 
        y="success_rate",
        title="",
        labels={"date": "Date", "success_rate": "Success Rate (%)"}
    )
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(204, 204, 204, 0.2)")
    )
    
    return fig

# Callback for updating token usage chart
@callback(
    Output("token-usage-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_token_usage(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("""
        SELECT date, total_tokens
        FROM metrics
        ORDER BY date
        LIMIT 30
    """, conn)
    conn.close()
    
    # If no data, create sample data
    if df.empty:
        dates = [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10, 0, -1)]
        df = pd.DataFrame({
            "date": dates,
            "total_tokens": [125000, 98000, 156000, 140000, 163000, 145000, 132000, 167000, 152000, 170000]
        })
    
    fig = px.bar(
        df, 
        x="date", 
        y="total_tokens",
        title="",
        labels={"date": "Date", "total_tokens": "Tokens Used"}
    )
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(204, 204, 204, 0.2)")
    )
    
    return fig

# Callback for updating execution time chart
@callback(
    Output("execution-time-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_execution_time(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("""
        SELECT date, avg_execution_time
        FROM metrics
        ORDER BY date
        LIMIT 30
    """, conn)
    conn.close()
    
    # If no data, create sample data
    if df.empty:
        dates = [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10, 0, -1)]
        df = pd.DataFrame({
            "date": dates,
            "avg_execution_time": [23.4, 21.2, 25.7, 19.8, 22.3, 24.5, 20.1, 18.9, 22.7, 21.5]
        })
    
    fig = px.line(
        df, 
        x="date", 
        y="avg_execution_time",
        title="",
        labels={"date": "Date", "avg_execution_time": "Avg. Execution Time (s)"}
    )
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(204, 204, 204, 0.2)")
    )
    
    return fig

# Callback for updating task distribution chart
@callback(
    Output("task-distribution-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_task_distribution(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("""
        SELECT task_type, COUNT(*) as count
        FROM activities
        GROUP BY task_type
        ORDER BY count DESC
    """, conn)
    conn.close()
    
    # If no data, create sample data
    if df.empty:
        df = pd.DataFrame({
            "task_type": ["Code Fix", "Vulnerability Scan", "Code Review", "Documentation", "Testing", "Other"],
            "count": [42, 28, 25, 18, 15, 8]
        })
    
    fig = px.pie(
        df, 
        names="task_type", 
        values="count",
        title="",
        hole=0.4
    )
    
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for updating model performance chart
@callback(
    Output("model-performance-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_model_performance(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("""
        SELECT model, 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
               AVG(execution_time) as avg_time,
               AVG(tokens_used) as avg_tokens
        FROM activities
        GROUP BY model
        ORDER BY total DESC
    """, conn)
    conn.close()
    
    # If no data, create sample data
    if df.empty:
        df = pd.DataFrame({
            "model": ["GPT-4", "Claude-3", "Gemini", "Cohere", "LLaMA-3"],
            "total": [120, 95, 65, 45, 30],
            "success": [108, 86, 58, 38, 24],
            "avg_time": [25.4, 18.2, 22.7, 15.8, 28.3],
            "avg_tokens": [3250, 2980, 3150, 2450, 3450]
        })
    
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
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        yaxis=dict(
            title="Success Rate (%)",
            showgrid=True,
            gridcolor="rgba(204, 204, 204, 0.2)",
            side="left"
        ),
        yaxis2=dict(
            title="Avg. Time (s)",
            overlaying="y",
            side="right"
        )
    )
    
    return fig

# Callback for updating activity log table
@callback(
    Output("activity-log-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_activity_log(n):
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql("""
        SELECT timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error
        FROM activities
        ORDER BY timestamp DESC
        LIMIT 10
    """, conn)
    conn.close()
    
    # If no data, create sample data
    if df.empty:
        now = datetime.datetime.now()
        timestamps = [(now - datetime.timedelta(minutes=i*5)).strftime("%Y-%m-%d %H:%M:%S") for i in range(10)]
        task_types = ["Code Fix", "Vulnerability Scan", "Code Review", "Documentation", "Testing"]
        statuses = ["success", "success", "success", "success", "success", "failure", "success", "success", "failure", "success"]
        models = ["GPT-4", "Claude-3", "GPT-4", "Gemini", "Claude-3", "GPT-4", "Cohere", "LLaMA-3", "GPT-4", "Claude-3"]
        errors = ["", "", "", "", "", "API rate limit exceeded", "", "", "Model context window exceeded", ""]
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "agent_id": [f"agent-{i}" for i in range(1, 11)],
            "task_id": [f"task-{100+i}" for i in range(1, 11)],
            "task_type": [task_types[i % len(task_types)] for i in range(10)],
            "status": statuses,
            "model": models,
            "tokens_used": [2500, 3100, 1800, 2700, 3200, 1500, 2900, 3300, 2100, 2800],
            "execution_time": [18.5, 22.3, 15.7, 20.1, 23.5, 12.8, 19.6, 25.4, 16.3, 21.9],
            "error": errors
        })
    
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
        status_class = "success-status" if row["status"] == "success" else "failure-status"
        rows.append(html.Tr([
            html.Td(row["timestamp"]),
            html.Td(row["agent_id"]),
            html.Td(row["task_id"]),
            html.Td(row["task_type"]),
            html.Td(row["status"], className=status_class),
            html.Td(row["model"]),
            html.Td(f"{row['tokens_used']:,}"),
            html.Td(f"{row['execution_time']:.1f}"),
            html.Td(row["error"])
        ]))
    
    table_body = [html.Tbody(rows)]
    
    return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, className="activity-table")

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)