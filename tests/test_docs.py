#!/usr/bin/env python3

import os
import re
import pytest
from pathlib import Path

# Add parent directory to import path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

class TestDocs:
    """Test cases for documentation files."""

    def test_quickstart_exists(self):
        """Test that the QUICKSTART.md file exists."""
        quickstart_path = Path(__file__).resolve().parent.parent / "QUICKSTART.md"
        assert quickstart_path.exists(), "QUICKSTART.md file does not exist"

    def test_quickstart_content(self):
        """Test that the QUICKSTART.md file contains required sections."""
        quickstart_path = Path(__file__).resolve().parent.parent / "QUICKSTART.md"
        with open(quickstart_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# SWE-agent Quick Start Guide",
            "## Prerequisites",
            "## Installation",
            "## Using SWE-agent",
            "## Troubleshooting"
        ]
        for section in required_sections:
            assert section in content, f"QUICKSTART.md missing section: {section}"

    def test_improvements_exists(self):
        """Test that the IMPROVEMENTS.md file exists."""
        improvements_path = Path(__file__).resolve().parent.parent / "IMPROVEMENTS.md"
        assert improvements_path.exists(), "IMPROVEMENTS.md file does not exist"

    def test_improvements_content(self):
        """Test that the IMPROVEMENTS.md file contains required sections."""
        improvements_path = Path(__file__).resolve().parent.parent / "IMPROVEMENTS.md"
        with open(improvements_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# SWE-agent Improvements",
            "## 1. Enhanced Documentation",
            "## 2. New Tools and Features",
            "## 3. README Enhancements",
            "## Next Steps"
        ]
        for section in required_sections:
            assert section in content, f"IMPROVEMENTS.md missing section: {section}"

    def test_whats_new_exists(self):
        """Test that the whats_new.md file exists."""
        whats_new_path = Path(__file__).resolve().parent.parent / "docs" / "usage" / "whats_new.md"
        assert whats_new_path.exists(), "whats_new.md file does not exist"

    def test_whats_new_content(self):
        """Test that the whats_new.md file contains required sections."""
        whats_new_path = Path(__file__).resolve().parent.parent / "docs" / "usage" / "whats_new.md"
        with open(whats_new_path, 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            "# What's New in SWE-agent",
            "## Latest Enhancements",
            "### Beginner-Friendly Configuration",
            "### Quick Start Guide",
            "### Model Comparison Tool",
            "### GitHub PR Integration"
        ]
        for section in required_sections:
            assert re.search(section, content, re.IGNORECASE), f"whats_new.md missing section: {section}"

    def test_readme_updated(self):
        """Test that the README.md file has been updated with new features."""
        readme_path = Path(__file__).resolve().parent.parent / "README.md"
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for updates
        assert "Quick Start Guide" in content, "README.md missing Quick Start Guide reference"
        assert "QUICKSTART.md" in content, "README.md missing QUICKSTART.md reference"