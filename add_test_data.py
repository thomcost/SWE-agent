#!/usr/bin/env python3
"""
Script to add test data to the dashboard database.
"""

import sqlite3
import datetime
import random
from pathlib import Path

# Path to the database
DB_PATH = Path("./dashboard_demo/activity_logs.db")

def add_activity(agent_id, task_id, task_type, status, model, tokens_used, execution_time, error=""):
    """Add a new activity to the database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert activity
    cursor.execute('''
    INSERT INTO activities 
    (timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error))
    
    # Update metrics table (by date)
    date = datetime.datetime.now().strftime("%Y-%m-%d")
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
    print(f"Added new activity: {task_id} ({status})")

def main():
    """Add some test activities."""
    # Check if database exists
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run the dashboard_demo.py script first to generate sample data.")
        return
    
    # Test activities to add
    activities = [
        {
            "agent_id": "test-agent-1",
            "task_id": f"test-task-{datetime.datetime.now().strftime('%H%M%S')}",
            "task_type": "Code Fix",
            "status": "success",
            "model": "GPT-4",
            "tokens_used": 2850,
            "execution_time": 19.3,
            "error": ""
        },
        {
            "agent_id": "test-agent-2",
            "task_id": f"test-task-{datetime.datetime.now().strftime('%H%M%S')}",
            "task_type": "Vulnerability Scan",
            "status": "failure",
            "model": "Claude-3",
            "tokens_used": 2100,
            "execution_time": 15.7,
            "error": "Model context window exceeded"
        },
        {
            "agent_id": "test-agent-1",
            "task_id": f"test-task-{datetime.datetime.now().strftime('%H%M%S')}",
            "task_type": "Documentation",
            "status": "success",
            "model": "Gemini",
            "tokens_used": 3150,
            "execution_time": 22.1,
            "error": ""
        }
    ]
    
    # Add activities to database
    for activity in activities:
        add_activity(**activity)
    
    print(f"Added {len(activities)} test activities. Check the dashboard to see them.")

if __name__ == "__main__":
    main()