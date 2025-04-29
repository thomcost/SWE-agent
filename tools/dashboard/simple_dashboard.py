#!/usr/bin/env python3
"""
Simple web server to view dashboard data from SQLite database.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Path to the database
DB_PATH = Path("./dashboard_demo/activity_logs.db")

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

def get_all_data():
    """Get all dashboard data."""
    return {
        "success_rate": get_success_rate(),
        "token_usage": get_token_usage(),
        "model_performance": get_model_performance(),
        "recent_activities": get_recent_activities()
    }

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""
    
    def _set_headers(self, content_type="text/html"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/":
            # Serve HTML page
            self._set_headers()
            with open(Path(__file__).parent / "dashboard_template.html", "r") as f:
                self.wfile.write(f.read().encode())
        elif self.path == "/data":
            # Serve JSON data
            self._set_headers("application/json")
            data = get_all_data()
            self.wfile.write(json.dumps(data).encode())
        else:
            # Not found
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

def generate_html_template():
    """Generate HTML template for dashboard."""
    html = """<!DOCTYPE html>
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
                <pre id="success-rate-data"></pre>
            </div>
        </div>
        <div class="col-6">
            <div class="card">
                <h4 class="card-title">Token Usage</h4>
                <pre id="token-usage-data"></pre>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h4 class="card-title">Model Performance</h4>
        <pre id="model-performance-data"></pre>
    </div>
    
    <div class="card">
        <h4 class="card-title">Recent Activities</h4>
        <table class="table" id="activities-table">
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
            <tbody id="activities-tbody"></tbody>
        </table>
    </div>

    <script>
        // Function to fetch and display data
        function updateDashboard() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    // Update success rate
                    document.getElementById('success-rate-data').textContent = 
                        JSON.stringify(data.success_rate, null, 2);
                    
                    // Update token usage
                    document.getElementById('token-usage-data').textContent = 
                        JSON.stringify(data.token_usage, null, 2);
                    
                    // Update model performance
                    document.getElementById('model-performance-data').textContent = 
                        JSON.stringify(data.model_performance, null, 2);
                    
                    // Update activities table
                    const tbody = document.getElementById('activities-tbody');
                    tbody.innerHTML = '';
                    
                    data.recent_activities.forEach(activity => {
                        const row = document.createElement('tr');
                        
                        row.innerHTML = `
                            <td>${activity.timestamp}</td>
                            <td>${activity.agent_id}</td>
                            <td>${activity.task_id}</td>
                            <td>${activity.task_type}</td>
                            <td class="${activity.status === 'success' ? 'success' : 'failure'}">${activity.status}</td>
                            <td>${activity.model}</td>
                            <td>${activity.tokens_used.toLocaleString()}</td>
                            <td>${activity.execution_time.toFixed(1)}</td>
                            <td>${activity.error || ''}</td>
                        `;
                        
                        tbody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching data:', error));
        }
        
        // Update dashboard initially and every 5 seconds
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
"""
    
    with open(Path(__file__).parent / "dashboard_template.html", "w") as f:
        f.write(html)

def run_server(host="0.0.0.0", port=8050):
    """Run the HTTP server."""
    generate_html_template()
    
    server = HTTPServer((host, port), DashboardHandler)
    print(f"Starting dashboard server at http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
        server.server_close()

if __name__ == "__main__":
    # Make sure the database exists
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run the dashboard_demo.py script first to generate sample data.")
        sys.exit(1)
    
    # Use a different port (3000)
    run_server(port=3000)