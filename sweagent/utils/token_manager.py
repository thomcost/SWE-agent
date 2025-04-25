"""
Token management utilities for SWE-agent.

This module provides utilities for managing token usage with language models:
- Token counting for different models
- Token usage tracking and budgeting
- Response caching to avoid redundant API calls
- Token usage optimization strategies
"""

import os
import json
import time
import hashlib
import logging
import functools
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, cast
from datetime import datetime, timedelta

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Configure logging
logger = logging.getLogger("sweagent.token_manager")

# Type variables for generic functions
T = TypeVar('T')

# Token counting utilities
def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: Text to count tokens for
        model: Model to use for tokenization
        
    Returns:
        Number of tokens
    """
    if not text:
        return 0
        
    if not TIKTOKEN_AVAILABLE:
        # Fallback to approximate counting
        return len(text.split()) + int(len(text) / 4)
        
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        # Model not found, use cl100k_base as default
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Fallback to approximate counting
            return len(text.split()) + int(len(text) / 4)


def truncate_to_token_limit(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """
    Truncate text to a maximum token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens
        model: Model to use for tokenization
        
    Returns:
        Truncated text
    """
    if not TIKTOKEN_AVAILABLE:
        # Fallback to approximate truncation
        words = text.split()
        approx_tokens_per_word = 1.3
        max_words = int(max_tokens / approx_tokens_per_word)
        return " ".join(words[:max_words])
        
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens])
    except Exception as e:
        logger.warning(f"Error truncating text to token limit: {e}")
        # Fallback to approximate truncation
        words = text.split()
        approx_tokens_per_word = 1.3
        max_words = int(max_tokens / approx_tokens_per_word)
        return " ".join(words[:max_words])


# Token budget management
class TokenBudget:
    """Manages token usage budgets and limits."""
    
    def __init__(self, 
                daily_budget: Optional[int] = None,
                hourly_budget: Optional[int] = None,
                total_budget: Optional[int] = None):
        """
        Initialize a token budget.
        
        Args:
            daily_budget: Maximum tokens per day
            hourly_budget: Maximum tokens per hour
            total_budget: Maximum tokens overall
        """
        self.daily_budget = daily_budget
        self.hourly_budget = hourly_budget
        self.total_budget = total_budget
        
        self.usage_log: List[Dict[str, Any]] = []
        self.total_tokens_used = 0
        
        # Load previous usage if available
        self._load_usage()
    
    def _load_usage(self) -> None:
        """Load usage data from disk if available."""
        usage_file = os.path.expanduser("~/.sweagent/token_usage.json")
        if os.path.exists(usage_file):
            try:
                with open(usage_file, 'r') as f:
                    data = json.load(f)
                    self.usage_log = data.get("usage_log", [])
                    self.total_tokens_used = data.get("total_tokens_used", 0)
            except Exception as e:
                logger.warning(f"Error loading token usage data: {e}")
    
    def _save_usage(self) -> None:
        """Save usage data to disk."""
        usage_dir = os.path.expanduser("~/.sweagent")
        usage_file = os.path.join(usage_dir, "token_usage.json")
        
        # Create directory if it doesn't exist
        if not os.path.exists(usage_dir):
            os.makedirs(usage_dir, exist_ok=True)
            
        try:
            with open(usage_file, 'w') as f:
                json.dump({
                    "usage_log": self.usage_log,
                    "total_tokens_used": self.total_tokens_used
                }, f)
        except Exception as e:
            logger.warning(f"Error saving token usage data: {e}")
    
    def track_usage(self, 
                   tokens: int, 
                   model: str, 
                   operation: str = "completion") -> bool:
        """
        Track token usage and check if budgets are exceeded.
        
        Args:
            tokens: Number of tokens used
            model: Model used
            operation: Operation type (e.g., "completion", "embedding")
            
        Returns:
            False if budget is exceeded, True otherwise
        """
        # Add usage to log
        now = datetime.now()
        self.usage_log.append({
            "tokens": tokens,
            "model": model,
            "operation": operation,
            "timestamp": now.isoformat()
        })
        
        # Update total
        self.total_tokens_used += tokens
        
        # Check total budget
        if self.total_budget and self.total_tokens_used > self.total_budget:
            logger.warning(f"Total token budget exceeded: {self.total_tokens_used}/{self.total_budget}")
            self._save_usage()
            return False
            
        # Check daily budget
        if self.daily_budget:
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            day_tokens = sum(entry["tokens"] for entry in self.usage_log 
                             if datetime.fromisoformat(entry["timestamp"]) >= day_start)
            if day_tokens > self.daily_budget:
                logger.warning(f"Daily token budget exceeded: {day_tokens}/{self.daily_budget}")
                self._save_usage()
                return False
                
        # Check hourly budget
        if self.hourly_budget:
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            hour_tokens = sum(entry["tokens"] for entry in self.usage_log 
                              if datetime.fromisoformat(entry["timestamp"]) >= hour_start)
            if hour_tokens > self.hourly_budget:
                logger.warning(f"Hourly token budget exceeded: {hour_tokens}/{self.hourly_budget}")
                self._save_usage()
                return False
        
        # Save current usage
        self._save_usage()
        return True
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get token usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        now = datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        day_tokens = sum(entry["tokens"] for entry in self.usage_log 
                         if datetime.fromisoformat(entry["timestamp"]) >= day_start)
        hour_tokens = sum(entry["tokens"] for entry in self.usage_log 
                          if datetime.fromisoformat(entry["timestamp"]) >= hour_start)
        
        # Group by model
        model_usage = {}
        for entry in self.usage_log:
            model = entry["model"]
            tokens = entry["tokens"]
            if model not in model_usage:
                model_usage[model] = 0
            model_usage[model] += tokens
        
        return {
            "total_tokens": self.total_tokens_used,
            "daily_tokens": day_tokens,
            "hourly_tokens": hour_tokens,
            "daily_budget": self.daily_budget,
            "hourly_budget": self.hourly_budget,
            "total_budget": self.total_budget,
            "model_usage": model_usage
        }


# Response caching
class ResponseCache:
    """Cache for model responses to avoid redundant API calls."""
    
    def __init__(self, 
                cache_dir: Optional[str] = None,
                ttl: Optional[int] = None,
                max_size: Optional[int] = None):
        """
        Initialize a response cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds for cache entries
            max_size: Maximum number of entries to keep in memory
        """
        self.cache_dir = cache_dir or os.path.expanduser("~/.sweagent/cache")
        self.ttl = ttl or 3600 * 24  # Default: 1 day
        self.max_size = max_size or 1000
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, 
                      prompt: str, 
                      model: str, 
                      temperature: float = 0.0,
                      max_tokens: Optional[int] = None) -> str:
        """
        Generate a cache key for a prompt and parameters.
        
        Args:
            prompt: Prompt text
            model: Model name
            temperature: Temperature parameter
            max_tokens: Maximum tokens parameter
            
        Returns:
            Cache key string
        """
        # Create a string with all parameters
        key_parts = [
            prompt,
            model,
            str(temperature)
        ]
        
        if max_tokens is not None:
            key_parts.append(str(max_tokens))
            
        # Join and hash
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key."""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, 
           prompt: str, 
           model: str,
           temperature: float = 0.0,
           max_tokens: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get a cached response if available.
        
        Args:
            prompt: Prompt text
            model: Model name
            temperature: Temperature parameter
            max_tokens: Maximum tokens parameter
            
        Returns:
            Cached response or None if not found
        """
        key = self._get_cache_key(prompt, model, temperature, max_tokens)
        
        # Check memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            # Check if entry is expired
            if self.ttl and time.time() - entry["timestamp"] > self.ttl:
                del self.memory_cache[key]
                return None
            return entry["response"]
        
        # Check file cache
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    entry = json.load(f)
                    
                # Check if entry is expired
                if self.ttl and time.time() - entry["timestamp"] > self.ttl:
                    os.remove(cache_path)
                    return None
                    
                # Add to memory cache
                self.memory_cache[key] = entry
                
                return entry["response"]
            except Exception as e:
                logger.warning(f"Error reading cache file: {e}")
                return None
        
        return None
    
    def set(self, 
           prompt: str, 
           model: str,
           response: Dict[str, Any],
           temperature: float = 0.0,
           max_tokens: Optional[int] = None) -> None:
        """
        Cache a response.
        
        Args:
            prompt: Prompt text
            model: Model name
            response: Response data
            temperature: Temperature parameter
            max_tokens: Maximum tokens parameter
        """
        key = self._get_cache_key(prompt, model, temperature, max_tokens)
        entry = {
            "timestamp": time.time(),
            "response": response
        }
        
        # Add to memory cache
        self.memory_cache[key] = entry
        
        # Add to file cache
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(entry, f)
        except Exception as e:
            logger.warning(f"Error writing cache file: {e}")
        
        # Limit memory cache size
        if self.max_size and len(self.memory_cache) > self.max_size:
            # Remove oldest entries
            items = sorted(self.memory_cache.items(), key=lambda x: x[1]["timestamp"])
            self.memory_cache = dict(items[-self.max_size:])
    
    def clear(self, age: Optional[int] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            age: Clear entries older than this many seconds
            
        Returns:
            Number of entries cleared
        """
        count = 0
        
        # Clear memory cache
        if age:
            cutoff = time.time() - age
            keys_to_remove = [k for k, v in self.memory_cache.items() if v["timestamp"] < cutoff]
            for k in keys_to_remove:
                del self.memory_cache[k]
            count += len(keys_to_remove)
        else:
            count += len(self.memory_cache)
            self.memory_cache = {}
        
        # Clear file cache
        if age:
            cutoff = time.time() - age
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith(".json"):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        entry = json.load(f)
                    if entry["timestamp"] < cutoff:
                        os.remove(filepath)
                        count += 1
                except Exception as e:
                    logger.warning(f"Error processing cache file {filepath}: {e}")
        else:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, filename))
                    count += 1
        
        return count


# Caching decorator
def cache_response(ttl: Optional[int] = None,
                  cache_instance: Optional[ResponseCache] = None) -> Callable:
    """
    Decorator that caches function responses.
    
    Args:
        ttl: Time-to-live in seconds
        cache_instance: Optional ResponseCache instance to use
        
    Returns:
        Decorated function
    """
    cache = cache_instance or ResponseCache(ttl=ttl)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Extract relevant parameters for cache key
            prompt = None
            model = "default"
            temperature = 0.0
            max_tokens = None
            
            # Try to extract from args and kwargs
            if args and isinstance(args[0], str):
                prompt = args[0]
            elif "prompt" in kwargs:
                prompt = kwargs["prompt"]
            elif "messages" in kwargs:
                # For chat completions
                messages = kwargs["messages"]
                if messages and isinstance(messages, list):
                    prompt = json.dumps(messages)
            
            if "model" in kwargs:
                model = kwargs["model"]
            
            if "temperature" in kwargs:
                temperature = kwargs["temperature"]
                
            if "max_tokens" in kwargs:
                max_tokens = kwargs["max_tokens"]
            
            # Skip caching if no prompt
            if not prompt:
                return func(*args, **kwargs)
            
            # Try to get from cache
            cached = cache.get(prompt, model, temperature, max_tokens)
            if cached is not None:
                logger.debug(f"Cache hit for {model}")
                return cast(T, cached)
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(prompt, model, result, temperature, max_tokens)
            
            return result
            
        return wrapper
    return decorator


# Token optimization strategies
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100, model: str = "gpt-4") -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Text to split
        chunk_size: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks
        model: Model to use for tokenization
        
    Returns:
        List of text chunks
    """
    if not TIKTOKEN_AVAILABLE:
        # Fallback to approximate chunking
        words = text.split()
        approx_tokens_per_word = 1.3
        chunk_word_size = int(chunk_size / approx_tokens_per_word)
        overlap_word_size = int(overlap / approx_tokens_per_word)
        
        chunks = []
        for i in range(0, len(words), chunk_word_size - overlap_word_size):
            chunk = " ".join(words[i:i + chunk_word_size])
            chunks.append(chunk)
        return chunks
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        
        chunks = []
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk = encoding.decode(chunk_tokens)
            chunks.append(chunk)
        return chunks
    except Exception as e:
        logger.warning(f"Error chunking text: {e}")
        # Fallback
        return [text]


def summarize_text(text: str, target_length: int = 1000, model: str = "gpt-4") -> str:
    """
    This is a placeholder function that would use an LLM to summarize text.
    In a real implementation, this would make an API call to a model.
    
    Args:
        text: Text to summarize
        target_length: Target length in tokens
        model: Model to use for summarization
        
    Returns:
        Summarized text
    """
    # This would make an actual API call in a real implementation
    # For now, just truncate the text
    return truncate_to_token_limit(text, target_length, model)


def optimize_context(content: Dict[str, Any], 
                    max_tokens: int = 4000,
                    priority_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Optimize a context dictionary to fit within token limits.
    
    Args:
        content: Content dictionary
        max_tokens: Maximum tokens
        priority_keys: Keys to prioritize (will not be trimmed if possible)
        
    Returns:
        Optimized context dictionary
    """
    priority_keys = priority_keys or []
    result = content.copy()
    
    # Count tokens for each key
    token_counts = {}
    total_tokens = 0
    
    for key, value in result.items():
        if isinstance(value, str):
            tokens = count_tokens(value)
            token_counts[key] = tokens
            total_tokens += tokens
    
    # If within limits, return as is
    if total_tokens <= max_tokens:
        return result
    
    # Calculate how many tokens to trim
    tokens_to_trim = total_tokens - max_tokens
    
    # First try trimming non-priority keys
    non_priority_keys = [k for k in result.keys() if k not in priority_keys and isinstance(result[k], str)]
    
    # Sort by token count, largest first
    non_priority_keys.sort(key=lambda k: token_counts.get(k, 0), reverse=True)
    
    # Trim non-priority keys
    for key in non_priority_keys:
        if tokens_to_trim <= 0:
            break
            
        current_tokens = token_counts[key]
        if tokens_to_trim >= current_tokens:
            # Remove this key entirely
            result[key] = "[Content trimmed to reduce token usage]"
            tokens_to_trim -= current_tokens
        else:
            # Partially trim this key
            result[key] = truncate_to_token_limit(result[key], current_tokens - tokens_to_trim)
            tokens_to_trim = 0
    
    # If we still need to trim, trim priority keys
    if tokens_to_trim > 0:
        priority_text_keys = [k for k in priority_keys if k in result and isinstance(result[k], str)]
        
        # Sort by token count, largest first
        priority_text_keys.sort(key=lambda k: token_counts.get(k, 0), reverse=True)
        
        for key in priority_text_keys:
            if tokens_to_trim <= 0:
                break
                
            current_tokens = token_counts[key]
            if current_tokens > tokens_to_trim:
                # Trim this key
                result[key] = truncate_to_token_limit(result[key], current_tokens - tokens_to_trim)
                tokens_to_trim = 0
    
    return result


# Token budget singleton
default_budget = TokenBudget()

# Response cache singleton
default_cache = ResponseCache()