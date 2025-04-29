#!/usr/bin/env python3
"""
Minimal Flask dashboard for SWE-agent without external dependencies.
"""

import sqlite3
import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify

# Path to the database
DB_PATH = Path("./dashboard_demo/activity_logs.db")

# Initialize Flask app
app = Flask(__name__)

# HTML template for the dashboard
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SWE-Agent Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .dashboard-title {
            color: #343a40;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #dee2e6;
        }
        .card {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
            padding: 15px;
        }
        .card-title {
            color: #495057;
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 15px;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .table th, .table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .table th {
            background-color: #f1f3f5;
            color: #495057;
            font-weight: 600;
        }
        .success {
            color: green;
        }
        .failure {
            color: red;
        }
        .row {
            display: flex;
            flex-wrap: wrap;
            margin-right: -15px;
            margin-left: -15px;
        }
        .col-6 {
            flex: 0 0 50%;
            max-width: 50%;
            padding-right: 15px;
            padding-left: 15px;
            box-sizing: border-box;
        }
        .col-12 {
            flex: 0 0 100%;
            max-width: 100%;
            padding-right: 15px;
            padding-left: 15px;
            box-sizing: border-box;
        }
        @media (max-width: 768px) {
            .col-6 {
                flex: 0 0 100%;
                max-width: 100%;
            }
        }
        pre {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1 class="dashboard-title">SWE-Agent Dashboard</h1>
    
    <div class="row">
        <div class="col-6">
            <div class="card">
                <h4 class="card-title">Task Success Rate</h4>
                <pre id="success-rate-data">{{ success_rate_data }}</pre>
            </div>
        </div>
        <div class="col-6">
            <div class="card">
                <h4 class="card-title">Token Usage</h4>
                <pre id="token-usage-data">{{ token_usage_data }}</pre>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h4 class="card-title">Model Performance</h4>
        <pre id="model-performance-data">{{ model_performance_data }}</pre>
    </div>
    
    <div class="card">
        <h4 class="card-title">Recent Activities</h4>
        <table class="table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Agent</th>
                    <th>Task ID</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Model</th>
                    <th>Tokens</th>
                    <th>Time (s)</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
                {% for activity in activities %}
                <tr>
                    <td>{{ activity.timestamp }}</td>
                    <td>{{ activity.agent_id }}</td>
                    <td>{{ activity.task_id }}</td>
                    <td>{{ activity.task_type }}</td>
                    <td class="{{ 'success' if activity.status == 'success' else 'failure' }}">{{ activity.status }}</td>
                    <td>{{ activity.model }}</td>
                    <td>{{ "{:,}".format(activity.tokens_used) }}</td>
                    <td>{{ "%.1f"|format(activity.execution_time) }}</td>
                    <td>{{ activity.error }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <script>
        // Auto-refresh the page every 10 seconds
        setTimeout(function() {
            location.reload();
        }, 10000);
    </script>
</body>
</html>
"""

def get_success_rate():
    """Get success rate data from database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, 
               successful_tasks * 100.0 / CASE WHEN total_tasks = 0 THEN 1 ELSE total_tasks END as success_rate
        FROM metrics
        ORDER BY date
        LIMIT 30
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    data = [{"date": row[0], "success_rate": row[1]} for row in rows]
    return data

def get_token_usage():
    """Get token usage data from database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, total_tokens
        FROM metrics
        ORDER BY date
        LIMIT 30
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    data = [{"date": row[0], "total_tokens": row[1]} for row in rows]
    return data

def get_model_performance():
    """Get model performance data from database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        SELECT model, 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
               AVG(execution_time) as avg_time,
               AVG(tokens_used) as avg_tokens
        FROM activities
        GROUP BY model
        ORDER BY total DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    data = []
    for row in rows:
        success_rate = (row[2] / row[1]) * 100 if row[1] > 0 else 0
        data.append({
            "model": row[0],
            "total": row[1],
            "success": row[2],
            "avg_time": row[3],
            "avg_tokens": row[4],
            "success_rate": success_rate
        })
    
    return data

def get_recent_activities():
    """Get recent activities from database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error
        FROM activities
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    data = []
    for row in rows:
        data.append({
            "timestamp": row[0],
            "agent_id": row[1],
            "task_id": row[2],
            "task_type": row[3],
            "status": row[4],
            "model": row[5],
            "tokens_used": row[6],
            "execution_time": row[7],
            "error": row[8]
        })
    
    return data

@app.route('/')
def dashboard():
    """Dashboard view."""
    success_rate_data = get_success_rate()
    token_usage_data = get_token_usage()
    model_performance_data = get_model_performance()
    activities = get_recent_activities()
    
    return render_template_string(
        HTML_TEMPLATE,
        success_rate_data=json.dumps(success_rate_data, indent=2),
        token_usage_data=json.dumps(token_usage_data, indent=2),
        model_performance_data=json.dumps(model_performance_data, indent=2),
        activities=activities
    )

if __name__ == '__main__':
    # Make sure the database exists
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run the dashboard_demo.py script first to generate sample data.")
        exit(1)
    
    print("Starting dashboard server at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)