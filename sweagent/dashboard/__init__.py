"""
Dashboard module for SWE-agent.
Provides a web-based interface for monitoring agent activities and performance.
"""

from pathlib import Path

# Ensure assets directory exists
ASSETS_DIR = Path(__file__).parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

__all__ = ["app", "logger"]