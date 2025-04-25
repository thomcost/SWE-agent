#!/usr/bin/env python
"""
Logger module for the SWE-agent dashboard.
Provides functions to log agent activities to the dashboard database.
"""

import sqlite3
import datetime
import json
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent / "activity_logs.db"

def initialize_db():
    """Initialize the SQLite database if it doesn't exist."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Create activities table
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
        
        # Create metrics table
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
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def log_activity(agent_id, task_id, task_type, status, model, tokens_used, execution_time, error=""):
    """
    Log an agent activity to the database.
    
    Args:
        agent_id (str): Identifier for the agent
        task_id (str): Identifier for the task
        task_type (str): Type of task (e.g., "Code Fix", "Vulnerability Scan")
        status (str): Status of the task ("success" or "failure")
        model (str): Model used for the task
        tokens_used (int): Number of tokens used
        execution_time (float): Execution time in seconds
        error (str, optional): Error message if status is "failure"
    """
    try:
        # Ensure database exists
        if not DB_PATH.exists():
            initialize_db()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Insert activity
        cursor.execute('''
        INSERT INTO activities 
        (timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error))
        
        # Update metrics
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check if entry for today exists
        cursor.execute("SELECT * FROM metrics WHERE date = ?", (today,))
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
            ''', (1 if status == "success" else 0, 1 if status == "failure" else 0, tokens_used, execution_time, today))
        else:
            # Create new entry
            cursor.execute('''
            INSERT INTO metrics
            (date, total_tasks, successful_tasks, failed_tasks, total_tokens, avg_execution_time)
            VALUES (?, 1, ?, ?, ?, ?)
            ''', (today, 1 if status == "success" else 0, 1 if status == "failure" else 0, tokens_used, execution_time))
        
        conn.commit()
        conn.close()
        logger.info(f"Activity logged: {agent_id}, {task_id}, {status}")
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def get_daily_metrics(days=30):
    """
    Get metrics for the last N days.
    
    Args:
        days (int): Number of days to retrieve
    
    Returns:
        list: List of daily metrics
    """
    try:
        if not DB_PATH.exists():
            return []
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT date, total_tasks, successful_tasks, failed_tasks, total_tokens, avg_execution_time
        FROM metrics
        ORDER BY date DESC
        LIMIT ?
        ''', (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "date": row[0],
                "total_tasks": row[1],
                "successful_tasks": row[2],
                "failed_tasks": row[3],
                "total_tokens": row[4],
                "avg_execution_time": row[5],
                "success_rate": (row[2] / row[1]) * 100 if row[1] > 0 else 0
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting daily metrics: {e}")
        return []

def get_model_metrics():
    """
    Get metrics by model.
    
    Returns:
        list: List of model metrics
    """
    try:
        if not DB_PATH.exists():
            return []
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT model,
               COUNT(*) as total,
               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
               AVG(tokens_used) as avg_tokens,
               AVG(execution_time) as avg_execution_time
        FROM activities
        GROUP BY model
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "model": row[0],
                "total_tasks": row[1],
                "successful_tasks": row[2],
                "failed_tasks": row[1] - row[2],
                "avg_tokens": row[3],
                "avg_execution_time": row[4],
                "success_rate": (row[2] / row[1]) * 100 if row[1] > 0 else 0
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        return []

def get_recent_activities(limit=10):
    """
    Get recent activities.
    
    Args:
        limit (int): Number of activities to retrieve
    
    Returns:
        list: List of recent activities
    """
    try:
        if not DB_PATH.exists():
            return []
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT timestamp, agent_id, task_id, task_type, status, model, tokens_used, execution_time, error
        FROM activities
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
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
        
        return result
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        return []

def add_sample_data(num_entries=100):
    """
    Add sample data for testing and demonstration.
    
    Args:
        num_entries (int): Number of sample entries to create
    """
    import random
    
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
    for i in range(num_entries):
        timestamp = datetime.datetime.now() - datetime.timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        agent_id = random.choice(agents)
        task_id = f"task-{random.randint(1, 999)}"
        task_type = random.choice(task_types)
        status = random.choice(statuses)
        status_weights = [0.85, 0.15]  # 85% success, 15% failure
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        model = random.choice(models)
        tokens_used = random.randint(1000, 5000)
        execution_time = random.uniform(10.0, 30.0)
        error = "" if status == "success" else random.choice(errors[1:])
        
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
    
    logger.info(f"Added {num_entries} sample data entries")

# Initialize database when module is imported
if not DB_PATH.exists():
    initialize_db()