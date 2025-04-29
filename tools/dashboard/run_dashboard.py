#!/usr/bin/env python
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
    app.run_server(debug=True, host="0.0.0.0", port=8050)