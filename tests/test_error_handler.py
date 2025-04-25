#!/usr/bin/env python3

import os
import sys
import logging
import tempfile
from unittest import mock
from pathlib import Path

# Add parent directory to import path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sweagent.utils.error_handler import (
    SWEAgentError,
    APIError,
    NetworkError,
    FileSystemError,
    ModelError,
    ConfigError,
    ErrorCategory,
    ErrorSeverity,
    retry,
    log_errors,
    validate_input,
    safe_execute,
    format_exception,
    get_recovery_action,
    initialize
)


class TestErrorTypes:
    """Test cases for error types."""
    
    def test_swe_agent_error(self):
        """Test SWEAgentError class."""
        error = SWEAgentError("Test error")
        assert error.message == "Test error"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.ERROR
        assert error.recovery_hint is None
        assert error.original_exception is None
        
        # Test with all parameters
        original = ValueError("Original error")
        error = SWEAgentError(
            message="Test error",
            category=ErrorCategory.API,
            severity=ErrorSeverity.WARNING,
            recovery_hint="Try again",
            original_exception=original
        )
        assert error.message == "Test error"
        assert error.category == ErrorCategory.API
        assert error.severity == ErrorSeverity.WARNING
        assert error.recovery_hint == "Try again"
        assert error.original_exception == original
        
        # Test string representation
        assert "Test error" in str(error)
        assert "Try again" in str(error)
        assert "Original error" in str(error)
    
    def test_api_error(self):
        """Test APIError class."""
        error = APIError("API failed")
        assert error.message == "API failed"
        assert error.category == ErrorCategory.API
        assert error.provider is None
        assert error.status_code is None
        
        # Test with all parameters
        error = APIError(
            message="Rate limit exceeded",
            recovery_hint="Wait and try again",
            status_code=429,
            provider="openai"
        )
        assert error.message.startswith("[openai]")
        assert "Rate limit exceeded" in error.message
        assert "Status code: 429" in error.message
        assert error.status_code == 429
        assert error.provider == "openai"
        assert error.recovery_hint == "Wait and try again"
    
    def test_network_error(self):
        """Test NetworkError class."""
        error = NetworkError("Connection failed")
        assert error.message == "Connection failed"
        assert error.category == ErrorCategory.NETWORK
        assert "Check network connectivity" in error.recovery_hint
        assert error.url is None
        
        # Test with URL
        error = NetworkError(
            message="Failed to connect",
            url="https://api.example.com"
        )
        assert "URL: https://api.example.com" in error.message
        assert error.url == "https://api.example.com"
    
    def test_filesystem_error(self):
        """Test FileSystemError class."""
        error = FileSystemError("File not found")
        assert error.message == "File not found"
        assert error.category == ErrorCategory.FILESYSTEM
        assert error.path is None
        assert error.operation is None
        
        # Test with path and operation
        error = FileSystemError(
            message="Cannot read file",
            path="/path/to/file.txt",
            operation="read"
        )
        assert "during read operation on '/path/to/file.txt'" in error.message
        assert error.path == "/path/to/file.txt"
        assert error.operation == "read"
    
    def test_model_error(self):
        """Test ModelError class."""
        error = ModelError("Model failed")
        assert error.message == "Model failed"
        assert error.category == ErrorCategory.MODEL
        assert error.model is None
        assert error.provider is None
        
        # Test with model and provider
        error = ModelError(
            message="Failed to generate response",
            model="gpt-4",
            provider="openai"
        )
        assert "(Provider: openai, Model: gpt-4)" in error.message
        assert error.model == "gpt-4"
        assert error.provider == "openai"
    
    def test_config_error(self):
        """Test ConfigError class."""
        error = ConfigError("Invalid configuration")
        assert error.message == "Invalid configuration"
        assert error.category == ErrorCategory.CONFIG
        assert "Check your configuration file" in error.recovery_hint
        assert error.config_path is None
        assert error.config_key is None
        
        # Test with config path and key
        error = ConfigError(
            message="Missing required config",
            config_path="/path/to/config.yaml",
            config_key="api_key"
        )
        assert "(Config: '/path/to/config.yaml', Key: 'api_key')" in error.message
        assert error.config_path == "/path/to/config.yaml"
        assert error.config_key == "api_key"


class TestDecorators:
    """Test cases for decorator functions."""
    
    def test_retry_decorator(self):
        """Test retry decorator."""
        # Mock function that fails twice then succeeds
        mock_func = mock.Mock(side_effect=[ValueError("Fail 1"), ValueError("Fail 2"), "success"])
        
        # Apply decorator
        decorated = retry(max_attempts=3, backoff_factor=0.01)(mock_func)
        
        # Call decorated function
        result = decorated()
        
        # Check result
        assert result == "success"
        assert mock_func.call_count == 3
        
        # Test with function that always fails
        mock_func = mock.Mock(side_effect=ValueError("Always fail"))
        decorated = retry(max_attempts=2, backoff_factor=0.01)(mock_func)
        
        # Should raise error after max attempts
        try:
            decorated()
            assert False, "Expected exception not raised"
        except SWEAgentError as e:
            assert "failed after 2 attempts" in str(e)
            assert mock_func.call_count == 2
    
    def test_log_errors_decorator(self):
        """Test log_errors decorator."""
        # Create logger for testing
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)
        
        # Create mock handler
        mock_handler = mock.Mock()
        logger.addHandler(mock_handler)
        
        # Mock the logger in error_handler module
        with mock.patch("sweagent.utils.error_handler.logger", logger):
            # Create test function
            @log_errors(level=logging.ERROR, reraise=False)
            def test_func():
                raise ValueError("Test error")
            
            # Call function
            result = test_func()
            
            # Check that error was logged
            assert mock_handler.handle.call_count == 1
            record = mock_handler.handle.call_args[0][0]
            assert "Test error" in record.getMessage()
            assert result is None
            
            # Test with transform=True
            @log_errors(level=logging.ERROR, reraise=True, transform=True)
            def test_func2():
                raise ValueError("Test error 2")
            
            # Should raise SWEAgentError
            try:
                test_func2()
                assert False, "Expected exception not raised"
            except SWEAgentError as e:
                assert "Test error 2" in str(e)
                assert mock_handler.handle.call_count == 2
    
    def test_validate_input_decorator(self):
        """Test validate_input decorator."""
        # Validator function
        def validator(x, y=None):
            return x > 0 and (y is None or y > 0)
        
        # Apply decorator
        @validate_input(validator, "Invalid input values")
        def test_func(x, y=None):
            return x + (y or 0)
        
        # Test with valid input
        assert test_func(1) == 1
        assert test_func(1, 2) == 3
        
        # Test with invalid input
        try:
            test_func(-1)
            assert False, "Expected exception not raised"
        except SWEAgentError as e:
            assert "Invalid input values" in str(e)
        
        try:
            test_func(1, -1)
            assert False, "Expected exception not raised"
        except SWEAgentError as e:
            assert "Invalid input values" in str(e)


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_safe_execute(self):
        """Test safe_execute function."""
        # Test with function that succeeds
        def success_func():
            return "success"
        
        result = safe_execute(success_func)
        assert result == "success"
        
        # Test with function that fails
        def fail_func():
            raise ValueError("Fail")
        
        result = safe_execute(fail_func, default_value="default")
        assert result == "default"
        
        # Test with specific exception type
        result = safe_execute(fail_func, default_value="default", exceptions=ValueError)
        assert result == "default"
        
        # Test with wrong exception type
        try:
            safe_execute(fail_func, default_value="default", exceptions=TypeError)
            assert False, "Expected exception not raised"
        except ValueError:
            pass
    
    def test_format_exception(self):
        """Test format_exception function."""
        # Test with regular exception
        e = ValueError("Test error")
        result = format_exception(e)
        assert result == "Error: Test error"
        
        # Test with SWEAgentError
        e = SWEAgentError("Test error", recovery_hint="Try again")
        result = format_exception(e)
        assert "Error: Test error" in result
        assert "Recovery hint: Try again" in result
    
    def test_get_recovery_action(self):
        """Test get_recovery_action function."""
        # Test with regular exception
        e = ValueError("Test error")
        result = get_recovery_action(e)
        assert "Consider restarting" in result
        
        # Test with SWEAgentError with recovery hint
        e = SWEAgentError("Test error", recovery_hint="Custom hint")
        result = get_recovery_action(e)
        assert result == "Custom hint"
        
        # Test with SWEAgentError without recovery hint but with category
        e = SWEAgentError("Test error", category=ErrorCategory.API)
        result = get_recovery_action(e)
        assert "Check your API keys" in result
        
        e = SWEAgentError("Test error", category=ErrorCategory.NETWORK)
        result = get_recovery_action(e)
        assert "Check your network connection" in result


class TestInitialization:
    """Test cases for initialization function."""
    
    def test_initialize(self):
        """Test initialize function."""
        # Test with console logging only
        with mock.patch("logging.StreamHandler") as mock_stream_handler:
            initialize(log_level=logging.DEBUG, console_logging=True)
            assert mock_stream_handler.call_count == 1
            
            # Check that root logger was configured
            logger = logging.getLogger("sweagent")
            assert logger.level == logging.DEBUG
            assert len(logger.handlers) == 1
        
        # Test with file logging
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            with mock.patch("logging.FileHandler") as mock_file_handler:
                initialize(log_file=log_file, log_level=logging.INFO, console_logging=False)
                assert mock_file_handler.call_count == 1
                mock_file_handler.assert_called_with(log_file)
                
                # Check that root logger was configured
                logger = logging.getLogger("sweagent")
                assert logger.level == logging.INFO
                assert len(logger.handlers) == 1