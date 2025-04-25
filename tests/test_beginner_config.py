#!/usr/bin/env python3

import os
import yaml
import pytest
from pathlib import Path

# Add parent directory to import path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

class TestBeginnerConfig:
    """Test cases for the beginner-friendly configuration."""

    def test_config_file_exists(self):
        """Test that the beginner-friendly config file exists."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "beginner_friendly.yaml"
        assert config_path.exists(), "Beginner-friendly config file does not exist"

    def test_config_file_is_valid_yaml(self):
        """Test that the beginner-friendly config file is valid YAML."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "beginner_friendly.yaml"
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            assert config is not None, "Config file is empty"
        except yaml.YAMLError as e:
            pytest.fail(f"Config file contains invalid YAML: {e}")

    def test_config_structure(self):
        """Test that the beginner-friendly config has the required structure."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "beginner_friendly.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Test basic structure
        assert 'agent' in config, "Config missing 'agent' section"
        assert 'templates' in config['agent'], "Config missing 'agent.templates' section"
        assert 'tools' in config['agent'], "Config missing 'agent.tools' section"
        
        # Test templates
        templates = config['agent']['templates']
        required_templates = [
            'system_template',
            'instance_template',
            'next_step_template',
            'next_step_no_output_template'
        ]
        for template in required_templates:
            assert template in templates, f"Config missing '{template}' in agent.templates"
        
        # Test tools configuration
        tools = config['agent']['tools']
        assert 'env_variables' in tools, "Config missing 'agent.tools.env_variables'"
        assert 'bundles' in tools, "Config missing 'agent.tools.bundles'"
        
        # Test model configuration
        assert 'model' in config, "Config missing 'model' section"

    def test_template_variables(self):
        """Test that templates contain required variables."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "beginner_friendly.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Test system template variables
        system_template = config['agent']['templates']['system_template']
        assert "{{WINDOW}}" in system_template, "System template missing WINDOW variable"
        
        # Test instance template variables
        instance_template = config['agent']['templates']['instance_template']
        assert "{{problem_statement}}" in instance_template, "Instance template missing problem_statement variable"
        assert "{{open_file}}" in instance_template, "Instance template missing open_file variable"
        assert "{{working_dir}}" in instance_template, "Instance template missing working_dir variable"
        
        # Test next step template variables
        next_step_template = config['agent']['templates']['next_step_template']
        assert "{{observation}}" in next_step_template, "Next step template missing observation variable"
        assert "{{open_file}}" in next_step_template, "Next step template missing open_file variable"
        assert "{{working_dir}}" in next_step_template, "Next step template missing working_dir variable"