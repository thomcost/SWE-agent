#!/usr/bin/env python3

import os
import pytest
from pathlib import Path

# Add parent directory to import path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

class TestDirectoryStructure:
    """Test cases for directory structure."""
    
    def test_model_comparison_structure(self):
        """Test that the model comparison tool has the correct directory structure."""
        base_path = Path(__file__).resolve().parent.parent / "tools" / "model_comparison"
        
        # Check that required files exist
        assert (base_path / "config.yaml").exists(), "model_comparison/config.yaml is missing"
        assert (base_path / "install.sh").exists(), "model_comparison/install.sh is missing"
        assert (base_path / "bin").exists(), "model_comparison/bin directory is missing"
        assert (base_path / "bin" / "compare_models.py").exists(), "model_comparison/bin/compare_models.py is missing"
    
    def test_github_pr_structure(self):
        """Test that the GitHub PR tool has the correct directory structure."""
        base_path = Path(__file__).resolve().parent.parent / "tools" / "github_pr"
        
        # Check that required files exist
        assert (base_path / "config.yaml").exists(), "github_pr/config.yaml is missing"
        assert (base_path / "install.sh").exists(), "github_pr/install.sh is missing"
        assert (base_path / "bin").exists(), "github_pr/bin directory is missing"
        assert (base_path / "bin" / "create_pr.py").exists(), "github_pr/bin/create_pr.py is missing"
    
    def test_config_directory(self):
        """Test that the config directory has the required files."""
        config_path = Path(__file__).resolve().parent.parent / "config"
        
        # Check that required files exist
        assert (config_path / "default.yaml").exists(), "config/default.yaml is missing"
        assert (config_path / "beginner_friendly.yaml").exists(), "config/beginner_friendly.yaml is missing"
    
    def test_docs_directory(self):
        """Test that the docs directory has the required files."""
        docs_path = Path(__file__).resolve().parent.parent / "docs" / "usage"
        
        # Check that required files exist
        assert (docs_path / "whats_new.md").exists(), "docs/usage/whats_new.md is missing"