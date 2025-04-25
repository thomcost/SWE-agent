"""
Error handling utilities for SWE-agent.

This module provides centralized error handling capabilities, including:
- Custom exception types
- Error logging
- Recovery mechanisms
- Retry logic
"""

import os
import sys
import time
import random
import logging
import traceback
import functools
from typing import Callable, TypeVar, Any, Optional, Dict, List, Union, Type

# Configure logging
logger = logging.getLogger("sweagent.error_handler")

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Error categories
class ErrorCategory:
    """Categories of errors for classification."""
    API = "api"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    PERMISSION = "permission"
    MODEL = "model"
    CONFIG = "config"
    INTERNAL = "internal"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


class ErrorSeverity:
    """Severity levels for errors."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SWEAgentError(Exception):
    """Base exception class for all SWE-agent errors."""
    
    def __init__(self, 
                 message: str, 
                 category: str = ErrorCategory.UNKNOWN,
                 severity: str = ErrorSeverity.ERROR,
                 recovery_hint: Optional[str] = None,
                 original_exception: Optional[Exception] = None):
        """
        Initialize a SWE-agent error.
        
        Args:
            message: Error message
            category: Error category for classification
            severity: Error severity level
            recovery_hint: Optional hint for recovery actions
            original_exception: Original exception if this is a wrapper
        """
        self.message = message
        self.category = category
        self.severity = severity
        self.recovery_hint = recovery_hint
        self.original_exception = original_exception
        self.timestamp = time.time()
        
        # Format the message
        full_message = f"{message}"
        if recovery_hint:
            full_message += f"\nRecovery hint: {recovery_hint}"
        if original_exception:
            full_message += f"\nOriginal error: {str(original_exception)}"
            
        super().__init__(full_message)


class APIError(SWEAgentError):
    """Errors related to API calls."""
    
    def __init__(self, 
                 message: str, 
                 recovery_hint: Optional[str] = None,
                 original_exception: Optional[Exception] = None,
                 status_code: Optional[int] = None,
                 provider: Optional[str] = None):
        """
        Initialize an API error.
        
        Args:
            message: Error message
            recovery_hint: Optional hint for recovery actions
            original_exception: Original exception if this is a wrapper
            status_code: HTTP status code if applicable
            provider: API provider name (e.g., "openai", "anthropic")
        """
        self.status_code = status_code
        self.provider = provider
        
        # Add provider and status code to message if available
        extended_message = message
        if provider:
            extended_message = f"[{provider}] {extended_message}"
        if status_code:
            extended_message += f" (Status code: {status_code})"
            
        super().__init__(
            message=extended_message,
            category=ErrorCategory.API,
            severity=ErrorSeverity.ERROR,
            recovery_hint=recovery_hint,
            original_exception=original_exception
        )


class NetworkError(SWEAgentError):
    """Errors related to network operations."""
    
    def __init__(self, 
                 message: str, 
                 recovery_hint: Optional[str] = None,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None):
        """
        Initialize a network error.
        
        Args:
            message: Error message
            recovery_hint: Optional hint for recovery actions
            original_exception: Original exception if this is a wrapper
            url: URL that was being accessed when the error occurred
        """
        self.url = url
        
        # Add URL to message if available
        extended_message = message
        if url:
            extended_message += f" (URL: {url})"
            
        super().__init__(
            message=extended_message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            recovery_hint=recovery_hint or "Check network connectivity and try again",
            original_exception=original_exception
        )


class FileSystemError(SWEAgentError):
    """Errors related to file system operations."""
    
    def __init__(self, 
                 message: str, 
                 recovery_hint: Optional[str] = None,
                 original_exception: Optional[Exception] = None,
                 path: Optional[str] = None,
                 operation: Optional[str] = None):
        """
        Initialize a file system error.
        
        Args:
            message: Error message
            recovery_hint: Optional hint for recovery actions
            original_exception: Original exception if this is a wrapper
            path: File or directory path that was being accessed
            operation: Operation being performed (e.g., "read", "write")
        """
        self.path = path
        self.operation = operation
        
        # Add path and operation to message if available
        extended_message = message
        if operation and path:
            extended_message += f" during {operation} operation on '{path}'"
        elif path:
            extended_message += f" on '{path}'"
            
        super().__init__(
            message=extended_message,
            category=ErrorCategory.FILESYSTEM,
            severity=ErrorSeverity.ERROR,
            recovery_hint=recovery_hint,
            original_exception=original_exception
        )


class ModelError(SWEAgentError):
    """Errors related to language model operations."""
    
    def __init__(self, 
                 message: str, 
                 recovery_hint: Optional[str] = None,
                 original_exception: Optional[Exception] = None,
                 model: Optional[str] = None,
                 provider: Optional[str] = None):
        """
        Initialize a model error.
        
        Args:
            message: Error message
            recovery_hint: Optional hint for recovery actions
            original_exception: Original exception if this is a wrapper
            model: Model name that was being used
            provider: Provider name (e.g., "openai", "anthropic")
        """
        self.model = model
        self.provider = provider
        
        # Add model and provider to message if available
        extended_message = message
        if provider and model:
            extended_message += f" (Provider: {provider}, Model: {model})"
        elif model:
            extended_message += f" (Model: {model})"
        elif provider:
            extended_message += f" (Provider: {provider})"
            
        super().__init__(
            message=extended_message,
            category=ErrorCategory.MODEL,
            severity=ErrorSeverity.ERROR,
            recovery_hint=recovery_hint,
            original_exception=original_exception
        )


class ConfigError(SWEAgentError):
    """Errors related to configuration."""
    
    def __init__(self, 
                 message: str, 
                 recovery_hint: Optional[str] = None,
                 original_exception: Optional[Exception] = None,
                 config_path: Optional[str] = None,
                 config_key: Optional[str] = None):
        """
        Initialize a configuration error.
        
        Args:
            message: Error message
            recovery_hint: Optional hint for recovery actions
            original_exception: Original exception if this is a wrapper
            config_path: Path to the configuration file
            config_key: Specific configuration key that caused the error
        """
        self.config_path = config_path
        self.config_key = config_key
        
        # Add config path and key to message if available
        extended_message = message
        if config_path and config_key:
            extended_message += f" (Config: '{config_path}', Key: '{config_key}')"
        elif config_path:
            extended_message += f" (Config: '{config_path}')"
        elif config_key:
            extended_message += f" (Key: '{config_key}')"
            
        super().__init__(
            message=extended_message,
            category=ErrorCategory.CONFIG,
            severity=ErrorSeverity.ERROR,
            recovery_hint=recovery_hint or "Check your configuration file for errors",
            original_exception=original_exception
        )


# Error handling decorators
def retry(max_attempts: int = 3, 
          backoff_factor: float = 1.0,
          jitter: bool = True,
          exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception) -> Callable:
    """
    Decorator that retries a function when specified exceptions occur.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Backoff factor for exponential backoff
        jitter: Whether to add random jitter to backoff times
        exceptions: Exception type(s) to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Don't sleep on the last attempt
                    if attempt < max_attempts:
                        # Calculate sleep time with exponential backoff
                        sleep_time = backoff_factor * (2 ** (attempt - 1))
                        
                        # Add jitter if enabled
                        if jitter:
                            sleep_time += random.uniform(0, 0.1 * sleep_time)
                            
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {sleep_time:.2f} seconds..."
                        )
                        
                        time.sleep(sleep_time)
            
            # If we get here, all attempts failed
            if isinstance(last_exception, SWEAgentError):
                raise last_exception
            else:
                raise SWEAgentError(
                    message=f"Function {func.__name__} failed after {max_attempts} attempts",
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.ERROR,
                    original_exception=last_exception,
                    recovery_hint="Consider increasing max_attempts or investigating the root cause"
                )
                
        return wrapper
    return decorator


def log_errors(level: int = logging.ERROR,
              reraise: bool = True,
              transform: bool = False) -> Callable:
    """
    Decorator that logs exceptions raised by a function.
    
    Args:
        level: Logging level to use
        reraise: Whether to re-raise the exception after logging
        transform: Whether to transform regular exceptions into SWEAgentError
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get traceback
                tb = traceback.format_exc()
                
                # Log the error
                logger.log(level, f"Error in {func.__name__}: {str(e)}\n{tb}")
                
                # Transform the exception if requested
                if transform and not isinstance(e, SWEAgentError):
                    new_exception = SWEAgentError(
                        message=f"Error in {func.__name__}: {str(e)}",
                        category=ErrorCategory.INTERNAL,
                        severity=ErrorSeverity.ERROR,
                        original_exception=e
                    )
                    if reraise:
                        raise new_exception
                    return None
                
                # Re-raise the original exception if requested
                if reraise:
                    raise
                
                return None
                
        return wrapper
    return decorator


def validate_input(validator: Callable[[Any], bool],
                  error_message: str = "Invalid input",
                  error_category: str = ErrorCategory.INTERNAL) -> Callable:
    """
    Decorator that validates function inputs.
    
    Args:
        validator: Function that validates the input
        error_message: Error message to use if validation fails
        error_category: Category of error to raise
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not validator(*args, **kwargs):
                raise SWEAgentError(
                    message=error_message,
                    category=error_category,
                    severity=ErrorSeverity.ERROR
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Error recovery utilities
def safe_execute(func: Callable[..., T], 
                default_value: Optional[R] = None,
                exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception) -> Union[T, R]:
    """
    Safely execute a function and return a default value if it fails.
    
    Args:
        func: Function to execute
        default_value: Default value to return if the function fails
        exceptions: Exception type(s) to catch
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except exceptions:
        return default_value


def format_exception(e: Exception) -> str:
    """
    Format an exception into a user-friendly string.
    
    Args:
        e: Exception to format
        
    Returns:
        Formatted exception string
    """
    if isinstance(e, SWEAgentError):
        message = f"Error: {e.message}"
        if e.recovery_hint:
            message += f"\nRecovery hint: {e.recovery_hint}"
        return message
    else:
        return f"Error: {str(e)}"


def get_recovery_action(error: Exception) -> Optional[str]:
    """
    Get a recovery action for a given error.
    
    Args:
        error: Exception to get recovery action for
        
    Returns:
        Recovery action string or None
    """
    if isinstance(error, SWEAgentError):
        if error.recovery_hint:
            return error.recovery_hint
            
        # Default recovery hints based on category
        if error.category == ErrorCategory.API:
            return "Check your API keys and rate limits"
        elif error.category == ErrorCategory.NETWORK:
            return "Check your network connection and try again"
        elif error.category == ErrorCategory.FILESYSTEM:
            return "Check file permissions and path validity"
        elif error.category == ErrorCategory.PERMISSION:
            return "Check your permissions and credentials"
        elif error.category == ErrorCategory.MODEL:
            return "Try using a different model or provider"
        elif error.category == ErrorCategory.CONFIG:
            return "Check your configuration file for errors"
        elif error.category == ErrorCategory.ENVIRONMENT:
            return "Check your environment variables and system setup"
            
    # Generic recovery action
    return "Consider restarting the application or checking the logs for more details"


# Initialize error handler module
def initialize(log_file: Optional[str] = None, 
              log_level: int = logging.INFO,
              console_logging: bool = True) -> None:
    """
    Initialize the error handler module.
    
    Args:
        log_file: Path to log file, or None for no file logging
        log_level: Logging level
        console_logging: Whether to log to console
    """
    # Configure root logger
    root_logger = logging.getLogger("sweagent")
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Format for logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler if requested
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)