#!/usr/bin/env python
"""
CLI script to run the dashboard server.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sweagent.dashboard.app import app
from sweagent.dashboard.logger import add_sample_data, initialize_db


def main():
    """Run the dashboard server."""
    parser = argparse.ArgumentParser(description="Run the SWE-agent dashboard server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8050, help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Run the server in debug mode")
    parser.add_argument("--sample-data", action="store_true", help="Add sample data to the dashboard")
    parser.add_argument("--sample-count", type=int, default=100, help="Number of sample data entries to add")

    args = parser.parse_args()

    # Initialize the database
    initialize_db()

    # Add sample data if requested
    if args.sample_data:
        add_sample_data(args.sample_count)
        print(f"Added {args.sample_count} sample data entries")

    # Run the server
    print(f"Starting dashboard server at http://{args.host}:{args.port}")
    app.run_server(debug=args.debug, host=args.host, port=args.port)


if __name__ == "__main__":
    main()