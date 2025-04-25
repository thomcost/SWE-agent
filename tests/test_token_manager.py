#!/usr/bin/env python3

import os
import sys
import json
import time
import tempfile
import unittest.mock as mock
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

# Add parent directory to import path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pytest
from sweagent.utils.token_manager import (
    count_tokens,
    truncate_to_token_limit,
    TokenBudget,
    ResponseCache,
    cache_response,
    chunk_text,
    optimize_context,
    TIKTOKEN_AVAILABLE
)


class TestTokenCounting:
    """Test cases for token counting functions."""
    
    def test_count_tokens(self):
        """Test count_tokens function."""
        # Test empty string
        assert count_tokens("") == 0
        
        # Test simple string (exact count will depend on tiktoken)
        text = "This is a test string with multiple words."
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)
        
        # Test with different model
        count2 = count_tokens(text, model="gpt-3.5-turbo")
        assert count2 > 0
        assert isinstance(count2, int)
    
    def test_truncate_to_token_limit(self):
        """Test truncate_to_token_limit function."""
        # Test string below limit
        text = "Short string"
        truncated = truncate_to_token_limit(text, 10)
        assert truncated == text
        
        # Test string above limit
        long_text = "This is a longer string that will exceed the token limit and should be truncated."
        truncated = truncate_to_token_limit(long_text, 5)
        assert len(truncated) < len(long_text)
        assert count_tokens(truncated) <= 5
        
        # Test with different model
        truncated2 = truncate_to_token_limit(long_text, 5, model="gpt-3.5-turbo")
        assert len(truncated2) < len(long_text)
        assert count_tokens(truncated2, model="gpt-3.5-turbo") <= 5


class TestTokenBudget:
    """Test cases for TokenBudget class."""
    
    def test_init(self):
        """Test TokenBudget initialization."""
        # Test with defaults
        budget = TokenBudget()
        assert budget.daily_budget is None
        assert budget.hourly_budget is None
        assert budget.total_budget is None
        assert budget.usage_log == []
        assert budget.total_tokens_used == 0
        
        # Test with parameters
        budget = TokenBudget(daily_budget=1000, hourly_budget=100, total_budget=10000)
        assert budget.daily_budget == 1000
        assert budget.hourly_budget == 100
        assert budget.total_budget == 10000
    
    @mock.patch("sweagent.utils.token_manager.os.path.exists")
    @mock.patch("sweagent.utils.token_manager.open", mock.mock_open(read_data='{"usage_log": [], "total_tokens_used": 0}'))
    def test_load_usage(self, mock_exists):
        """Test _load_usage method."""
        mock_exists.return_value = True
        
        budget = TokenBudget()
        budget._load_usage()
        
        assert budget.usage_log == []
        assert budget.total_tokens_used == 0
        
        # Test with data
        mock_exists.return_value = True
        with mock.patch("sweagent.utils.token_manager.open", 
                        mock.mock_open(read_data='{"usage_log": [{"tokens": 100, "model": "gpt-4", "timestamp": "2023-01-01T12:00:00"}], "total_tokens_used": 100}')):
            budget = TokenBudget()
            budget._load_usage()
            
            assert len(budget.usage_log) == 1
            assert budget.usage_log[0]["tokens"] == 100
            assert budget.total_tokens_used == 100
    
    @mock.patch("sweagent.utils.token_manager.os.path.exists")
    @mock.patch("sweagent.utils.token_manager.os.makedirs")
    @mock.patch("sweagent.utils.token_manager.open", mock.mock_open())
    def test_save_usage(self, mock_makedirs, mock_exists):
        """Test _save_usage method."""
        mock_exists.return_value = False
        
        budget = TokenBudget()
        budget.usage_log = [{"tokens": 100, "model": "gpt-4", "timestamp": "2023-01-01T12:00:00"}]
        budget.total_tokens_used = 100
        budget._save_usage()
        
        mock_makedirs.assert_called_once()
        handle = mock.mock_open().return_value.__enter__.return_value
        handle.write.assert_called_once()
        
        # Check JSON data
        call_args = handle.write.call_args[0][0]
        data = json.loads(call_args)
        assert "usage_log" in data
        assert "total_tokens_used" in data
        assert data["total_tokens_used"] == 100
    
    def test_track_usage(self):
        """Test track_usage method."""
        # Test with no budgets
        budget = TokenBudget()
        with mock.patch.object(budget, "_save_usage") as mock_save:
            result = budget.track_usage(100, "gpt-4")
            assert result is True
            assert budget.total_tokens_used == 100
            assert len(budget.usage_log) == 1
            mock_save.assert_called_once()
        
        # Test with total budget exceeded
        budget = TokenBudget(total_budget=50)
        with mock.patch.object(budget, "_save_usage") as mock_save:
            result = budget.track_usage(100, "gpt-4")
            assert result is False
            assert budget.total_tokens_used == 100
            mock_save.assert_called_once()
        
        # Test with daily budget
        budget = TokenBudget(daily_budget=50)
        with mock.patch.object(budget, "_save_usage") as mock_save:
            # Mock today's date for usage log
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            budget.usage_log = [
                {"tokens": 40, "model": "gpt-4", "timestamp": today.isoformat()}
            ]
            
            # This should exceed daily budget
            result = budget.track_usage(20, "gpt-4")
            assert result is False
            mock_save.assert_called_once()
    
    def test_get_usage_stats(self):
        """Test get_usage_stats method."""
        budget = TokenBudget(daily_budget=1000, hourly_budget=100, total_budget=10000)
        
        # Mock usage log
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour = now.replace(minute=0, second=0, microsecond=0)
        
        budget.usage_log = [
            {"tokens": 50, "model": "gpt-4", "timestamp": today.isoformat()},
            {"tokens": 30, "model": "gpt-3.5-turbo", "timestamp": hour.isoformat()},
            {"tokens": 20, "model": "gpt-4", "timestamp": hour.isoformat()}
        ]
        budget.total_tokens_used = 100
        
        stats = budget.get_usage_stats()
        assert stats["total_tokens"] == 100
        assert stats["daily_tokens"] == 100
        assert stats["hourly_tokens"] == 50
        assert stats["daily_budget"] == 1000
        assert stats["hourly_budget"] == 100
        assert stats["total_budget"] == 10000
        assert "model_usage" in stats
        assert stats["model_usage"]["gpt-4"] == 70
        assert stats["model_usage"]["gpt-3.5-turbo"] == 30


class TestResponseCache:
    """Test cases for ResponseCache class."""
    
    def test_init(self):
        """Test ResponseCache initialization."""
        # Test with defaults
        with mock.patch("sweagent.utils.token_manager.os.makedirs") as mock_makedirs:
            cache = ResponseCache()
            assert cache.ttl == 3600 * 24  # 1 day
            assert cache.max_size == 1000
            assert cache.memory_cache == {}
            mock_makedirs.assert_called_once()
        
        # Test with parameters
        with mock.patch("sweagent.utils.token_manager.os.makedirs") as mock_makedirs:
            cache = ResponseCache(cache_dir="/tmp/cache", ttl=60, max_size=10)
            assert cache.cache_dir == "/tmp/cache"
            assert cache.ttl == 60
            assert cache.max_size == 10
            mock_makedirs.assert_called_once()
    
    def test_get_cache_key(self):
        """Test _get_cache_key method."""
        cache = ResponseCache()
        
        # Test basic key generation
        key1 = cache._get_cache_key("test prompt", "gpt-4", 0.0)
        assert isinstance(key1, str)
        assert len(key1) > 0
        
        # Test same parameters produce same key
        key2 = cache._get_cache_key("test prompt", "gpt-4", 0.0)
        assert key1 == key2
        
        # Test different parameters produce different keys
        key3 = cache._get_cache_key("test prompt", "gpt-4", 0.5)
        assert key1 != key3
        
        key4 = cache._get_cache_key("test prompt", "gpt-3.5-turbo", 0.0)
        assert key1 != key4
        
        key5 = cache._get_cache_key("different prompt", "gpt-4", 0.0)
        assert key1 != key5
        
        # Test with max_tokens
        key6 = cache._get_cache_key("test prompt", "gpt-4", 0.0, 100)
        assert key1 != key6
    
    def test_get_cache_path(self):
        """Test _get_cache_path method."""
        cache = ResponseCache(cache_dir="/tmp/cache")
        path = cache._get_cache_path("abc123")
        assert path == "/tmp/cache/abc123.json"
    
    def test_get(self):
        """Test get method."""
        cache = ResponseCache()
        
        # Test cache miss (memory and file)
        with mock.patch("sweagent.utils.token_manager.os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = cache.get("test prompt", "gpt-4")
            assert result is None
        
        # Test memory cache hit
        key = cache._get_cache_key("test prompt", "gpt-4", 0.0)
        cache.memory_cache[key] = {
            "timestamp": time.time(),
            "response": {"text": "cached response"}
        }
        result = cache.get("test prompt", "gpt-4")
        assert result == {"text": "cached response"}
        
        # Test memory cache expired
        cache.memory_cache[key] = {
            "timestamp": time.time() - cache.ttl - 1,  # Expired
            "response": {"text": "expired response"}
        }
        with mock.patch("sweagent.utils.token_manager.os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = cache.get("test prompt", "gpt-4")
            assert result is None
            assert key not in cache.memory_cache
        
        # Test file cache hit
        with mock.patch("sweagent.utils.token_manager.os.path.exists") as mock_exists, \
             mock.patch("sweagent.utils.token_manager.open", 
                       mock.mock_open(read_data='{"timestamp": ' + str(time.time()) + ', "response": {"text": "file response"}}')):
            mock_exists.return_value = True
            result = cache.get("test prompt", "gpt-4")
            assert result == {"text": "file response"}
            assert key in cache.memory_cache
        
        # Test file cache expired
        with mock.patch("sweagent.utils.token_manager.os.path.exists") as mock_exists, \
             mock.patch("sweagent.utils.token_manager.open", 
                       mock.mock_open(read_data='{"timestamp": ' + str(time.time() - cache.ttl - 1) + ', "response": {"text": "expired"}}')), \
             mock.patch("sweagent.utils.token_manager.os.remove") as mock_remove:
            mock_exists.return_value = True
            result = cache.get("test prompt", "gpt-4")
            assert result is None
            mock_remove.assert_called_once()
    
    def test_set(self):
        """Test set method."""
        cache = ResponseCache()
        
        # Test setting cache entry
        with mock.patch("sweagent.utils.token_manager.open", mock.mock_open()) as mock_file:
            response = {"text": "test response"}
            cache.set("test prompt", "gpt-4", response)
            
            # Check memory cache
            key = cache._get_cache_key("test prompt", "gpt-4", 0.0)
            assert key in cache.memory_cache
            assert cache.memory_cache[key]["response"] == response
            
            # Check file cache
            mock_file.assert_called_once()
            handle = mock_file.return_value.__enter__.return_value
            handle.write.assert_called_once()
            
            # Parse JSON data
            call_args = handle.write.call_args[0][0]
            data = json.loads(call_args)
            assert "timestamp" in data
            assert "response" in data
            assert data["response"] == response
        
        # Test max_size limit
        cache = ResponseCache(max_size=2)
        
        # Add 3 entries
        cache.set("prompt1", "gpt-4", {"text": "response1"})
        time.sleep(0.01)  # Ensure different timestamps
        cache.set("prompt2", "gpt-4", {"text": "response2"})
        time.sleep(0.01)
        cache.set("prompt3", "gpt-4", {"text": "response3"})
        
        # Check only newest 2 are kept
        assert len(cache.memory_cache) == 2
        
        # Get keys
        key1 = cache._get_cache_key("prompt1", "gpt-4", 0.0)
        key2 = cache._get_cache_key("prompt2", "gpt-4", 0.0)
        key3 = cache._get_cache_key("prompt3", "gpt-4", 0.0)
        
        # Oldest should be removed
        assert key1 not in cache.memory_cache
        assert key2 in cache.memory_cache
        assert key3 in cache.memory_cache
    
    def test_clear(self):
        """Test clear method."""
        cache = ResponseCache()
        
        # Add some entries
        cache.memory_cache = {
            "key1": {"timestamp": time.time() - 3600, "response": {"text": "old"}},
            "key2": {"timestamp": time.time(), "response": {"text": "new"}}
        }
        
        # Test clear by age
        with mock.patch("sweagent.utils.token_manager.os.listdir") as mock_listdir, \
             mock.patch("sweagent.utils.token_manager.open", 
                       mock.mock_open(read_data='{"timestamp": ' + str(time.time() - 3600) + ', "response": {}}')), \
             mock.patch("sweagent.utils.token_manager.os.remove") as mock_remove:
            mock_listdir.return_value = ["key1.json", "key2.json"]
            
            count = cache.clear(age=1800)  # 30 minutes
            
            # Should clear one memory entry
            assert len(cache.memory_cache) == 1
            assert "key1" not in cache.memory_cache
            assert "key2" in cache.memory_cache
            
            # Should attempt to clear one file
            assert mock_remove.call_count == 1
            
            # Should return count of cleared entries
            assert count == 2  # 1 memory + 1 file
        
        # Test clear all
        with mock.patch("sweagent.utils.token_manager.os.listdir") as mock_listdir, \
             mock.patch("sweagent.utils.token_manager.os.remove") as mock_remove:
            mock_listdir.return_value = ["key1.json", "key2.json"]
            
            count = cache.clear()
            
            # Should clear all memory entries
            assert len(cache.memory_cache) == 0
            
            # Should clear all files
            assert mock_remove.call_count == 2
            
            # Should return count of cleared entries
            assert count == 3  # 1 memory + 2 files


class TestCacheDecorator:
    """Test cases for cache_response decorator."""
    
    def test_cache_response(self):
        """Test cache_response decorator."""
        # Create mock cache
        mock_cache = mock.MagicMock(spec=ResponseCache)
        mock_cache.get.return_value = None
        
        # Create test function
        @cache_response(cache_instance=mock_cache)
        def test_func(prompt, model="gpt-4", temperature=0.0):
            return {"text": f"Response for {prompt} using {model}"}
        
        # Test caching
        result = test_func("test prompt", model="gpt-4")
        assert result["text"] == "Response for test prompt using gpt-4"
        
        # Check cache operations
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
        
        # Test cache hit
        mock_cache.get.return_value = {"text": "Cached response"}
        result = test_func("test prompt", model="gpt-4")
        assert result["text"] == "Cached response"
        
        # Test with different parameters
        mock_cache.get.return_value = None
        result = test_func("test prompt", model="gpt-3.5-turbo", temperature=0.5)
        assert result["text"] == "Response for test prompt using gpt-3.5-turbo"
        
        # Test with messages format
        @cache_response(cache_instance=mock_cache)
        def chat_func(messages, model="gpt-4"):
            return {"text": f"Response for chat using {model}"}
        
        mock_cache.get.return_value = None
        messages = [{"role": "user", "content": "Hello"}]
        result = chat_func(messages, model="gpt-4")
        assert result["text"] == "Response for chat using gpt-4"
        mock_cache.set.assert_called()


class TestTokenOptimization:
    """Test cases for token optimization functions."""
    
    def test_chunk_text(self):
        """Test chunk_text function."""
        # Test chunking
        text = "This is a test string that should be split into chunks."
        chunks = chunk_text(text, chunk_size=5, overlap=1)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be reasonably sized
        for chunk in chunks:
            assert len(chunk) > 0
            assert count_tokens(chunk) <= 10  # Allow some flexibility
        
        # Joined chunks should approximately cover the original text
        # (not perfect due to tokenization effects at chunk boundaries)
        joined = " ".join(chunks)
        assert len(joined) >= len(text) * 0.8
    
    def test_optimize_context(self):
        """Test optimize_context function."""
        # Create test context
        context = {
            "important": "This is important content that should be preserved",
            "less_important": "This is less important content that can be trimmed if needed",
            "not_text": 123,  # Non-text field should be preserved
            "large_text": "A" * 1000  # Large text field
        }
        
        # Test with context under limit
        result = optimize_context(context, max_tokens=10000)
        assert result == context
        
        # Test with context over limit
        result = optimize_context(context, max_tokens=10, priority_keys=["important"])
        
        # Priority key should be preserved or at least partially preserved
        assert "important" in result
        assert len(result["important"]) > 0
        
        # Less important key should be trimmed or removed
        assert len(result["less_important"]) < len(context["less_important"]) or \
               result["less_important"] == "[Content trimmed to reduce token usage]"
        
        # Non-text field should be preserved
        assert result["not_text"] == 123
        
        # Total tokens should be reduced
        total_tokens = sum(count_tokens(v) for k, v in result.items() if isinstance(v, str))
        assert total_tokens <= 15  # Allow some flexibility for approximate counting