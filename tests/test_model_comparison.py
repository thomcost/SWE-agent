#!/usr/bin/env python3

import os
import json
import pytest
import tempfile
from unittest import mock
from pathlib import Path

# Add parent directory to import path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import the module functions to test
from tools.model_comparison.bin.compare_models import (
    parse_args,
    parse_issue_url,
    run_model,
    compare_results
)

class TestModelComparison:
    """Test cases for the model comparison tool."""

    def test_parse_issue_url(self):
        """Test parsing GitHub issue URLs."""
        # Test a valid GitHub issue URL
        url = "https://github.com/SWE-agent/SWE-agent/issues/123"
        owner, repo, issue = parse_issue_url(url)
        assert owner == "SWE-agent"
        assert repo == "SWE-agent"
        assert issue == "123"

        # Test a URL with trailing slash
        url = "https://github.com/SWE-agent/SWE-agent/issues/123/"
        owner, repo, issue = parse_issue_url(url)
        assert owner == "SWE-agent"
        assert repo == "SWE-agent"
        assert issue == "123"

        # Test an invalid URL
        url = "https://example.com/not-github"
        owner, repo, issue = parse_issue_url(url)
        assert owner is None
        assert repo is None
        assert issue is None

    @mock.patch('tools.model_comparison.bin.compare_models.subprocess.run')
    def test_run_model(self, mock_subprocess):
        """Test running a model on a task."""
        # Setup mock
        process_mock = mock.Mock()
        process_mock.returncode = 0
        process_mock.stdout = "Success"
        process_mock.stderr = ""
        mock_subprocess.return_value = process_mock

        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Test running a model
            result = run_model("gpt-4", "test-task", "default.yaml", tmp_dir)
            
            # Verify the result
            assert result["model"] == "gpt-4"
            assert result["success"] is True
            
            # Check that files were created
            model_dir = os.path.join(tmp_dir, "gpt-4")
            assert os.path.exists(model_dir)
            assert os.path.exists(os.path.join(model_dir, "run_info.json"))
            assert os.path.exists(os.path.join(model_dir, "stdout.log"))
            assert os.path.exists(os.path.join(model_dir, "stderr.log"))
            
            # Verify subprocess was called with correct arguments
            cmd_args = mock_subprocess.call_args[0][0]
            assert "gpt-4" in cmd_args
            assert "openai" in cmd_args
            assert "test-task" in cmd_args

    def test_compare_results(self):
        """Test comparing results from multiple models."""
        # Create a temporary directory for output
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create mock results
            results = [
                {"model": "model1", "success": True, "duration": 10.5},
                {"model": "model2", "success": False, "duration": 5.2},
                {"model": "model3", "success": True, "duration": 15.8}
            ]
            
            # Setup mock arguments
            with mock.patch('tools.model_comparison.bin.compare_models.args') as mock_args:
                mock_args.task = "test-task"
                mock_args.config = "test-config"
                
                # Test comparing results
                summary = compare_results(results, tmp_dir)
                
                # Verify summary was created
                assert os.path.exists(os.path.join(tmp_dir, "summary.json"))
                assert os.path.exists(os.path.join(tmp_dir, "summary.md"))
                
                # Check that results are sorted correctly (successful models first, then by duration)
                assert summary["results"][0]["model"] == "model1"  # Successful with lowest duration
                assert summary["results"][1]["model"] == "model3"  # Successful but longer duration
                assert summary["results"][2]["model"] == "model2"  # Failed

    @mock.patch('argparse.ArgumentParser.parse_args')
    def test_parse_args(self, mock_args):
        """Test argument parsing."""
        # Setup mock
        mock_args.return_value = mock.Mock(
            task="https://github.com/owner/repo/issues/123",
            models="model1,model2",
            config="test-config.yaml",
            output="test-output"
        )
        
        # Test parsing arguments
        args = parse_args()
        
        # Verify arguments
        assert args.task == "https://github.com/owner/repo/issues/123"
        assert args.models == "model1,model2"
        assert args.config == "test-config.yaml"
        assert args.output == "test-output"