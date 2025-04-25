"""
Model adapter system for supporting various language models in SWE-agent.

This module provides adapters for different language model providers:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude, Claude Instant, etc.)
- HuggingFace (Various open models)
- Local models via llama.cpp
- Google (PaLM, Gemini)
- Cohere
- AI21 (Jurassic)
- Aleph Alpha
"""

import os
import json
import logging
import functools
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable, TypeVar, cast

from sweagent.utils.error_handler import APIError, retry
from sweagent.utils.token_manager import count_tokens, cache_response

# Configure logging
logger = logging.getLogger("sweagent.model_adapters")

# Type variables
T = TypeVar('T')

# Message type definitions
Message = Dict[str, str]
MessageList = List[Message]


class ModelAdapter(ABC):
    """Abstract base class for model adapters."""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize a model adapter.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for the model provider
            **kwargs: Additional provider-specific parameters
        """
        self.model_name = model_name
        self.api_key = api_key or self._get_api_key_from_env()
        self.config = kwargs
    
    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variables."""
        pass
    
    @abstractmethod
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """
        Generate a text completion.
        
        Args:
            prompt: Text prompt
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stop: List of stop sequences
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary with completion result
        """
        pass
    
    @abstractmethod
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """
        Generate a chat completion.
        
        Args:
            messages: List of messages in the conversation
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stop: List of stop sequences
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary with completion result
        """
        pass
    
    @abstractmethod
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Stream a chat completion.
        
        Args:
            messages: List of messages in the conversation
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stop: List of stop sequences
            callback: Callback function for each chunk
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dictionary with completion result
        """
        pass
    
    @abstractmethod
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            **kwargs: Additional provider-specific parameters
            
        Returns:
            List of embedding vectors
        """
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens for the model.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return count_tokens(text, model=self.model_name)
    
    def count_message_tokens(self, messages: MessageList) -> int:
        """
        Count tokens in a message list.
        
        Args:
            messages: List of messages
            
        Returns:
            Number of tokens
        """
        text = json.dumps(messages)
        return self.count_tokens(text)


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI models."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Generate a text completion using OpenAI API."""
        try:
            import openai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("OpenAI API key not found", 
                               recovery_hint="Set the OPENAI_API_KEY environment variable")
                               
            openai.api_key = self.api_key
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop"] = stop
            
            # Make API call
            response = openai.Completion.create(**params)
            
            # Format response
            return {
                "text": response.choices[0].text.strip(),
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except ImportError:
            raise APIError("OpenAI Python package not installed", 
                          recovery_hint="Install with 'pip install openai'",
                          provider="openai")
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}", 
                          original_exception=e,
                          provider="openai")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Generate a chat completion using OpenAI API."""
        try:
            import openai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("OpenAI API key not found", 
                               recovery_hint="Set the OPENAI_API_KEY environment variable",
                               provider="openai")
                               
            openai.api_key = self.api_key
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop"] = stop
            
            # Make API call
            response = openai.ChatCompletion.create(**params)
            
            # Format response
            return {
                "text": response.choices[0].message.content.strip(),
                "message": response.choices[0].message,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except ImportError:
            raise APIError("OpenAI Python package not installed", 
                          recovery_hint="Install with 'pip install openai'",
                          provider="openai")
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}", 
                          original_exception=e,
                          provider="openai")
    
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Stream a chat completion using OpenAI API."""
        try:
            import openai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("OpenAI API key not found", 
                               recovery_hint="Set the OPENAI_API_KEY environment variable",
                               provider="openai")
                               
            openai.api_key = self.api_key
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop"] = stop
            
            # Make API call
            full_text = ""
            for chunk in openai.ChatCompletion.create(**params):
                if hasattr(chunk.choices[0], "delta") and hasattr(chunk.choices[0].delta, "content"):
                    content = chunk.choices[0].delta.content
                    if content:
                        full_text += content
                        if callback:
                            callback(content)
            
            # Format response
            return {
                "text": full_text.strip(),
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"  # Streaming doesn't provide this accurately
            }
        except ImportError:
            raise APIError("OpenAI Python package not installed", 
                          recovery_hint="Install with 'pip install openai'",
                          provider="openai")
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}", 
                          original_exception=e,
                          provider="openai")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        try:
            import openai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("OpenAI API key not found", 
                               recovery_hint="Set the OPENAI_API_KEY environment variable",
                               provider="openai")
                               
            openai.api_key = self.api_key
            
            # Make API call
            response = openai.Embedding.create(
                model=kwargs.get("embedding_model", "text-embedding-ada-002"),
                input=texts
            )
            
            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
        except ImportError:
            raise APIError("OpenAI Python package not installed", 
                          recovery_hint="Install with 'pip install openai'",
                          provider="openai")
        except Exception as e:
            raise APIError(f"OpenAI API error: {str(e)}", 
                          original_exception=e,
                          provider="openai")


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic Claude models."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("ANTHROPIC_API_KEY")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Generate a text completion using Anthropic API."""
        try:
            from anthropic import Anthropic
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Anthropic API key not found", 
                               recovery_hint="Set the ANTHROPIC_API_KEY environment variable",
                               provider="anthropic")
            
            # Initialize client
            client = Anthropic(api_key=self.api_key)
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "prompt": f"Human: {prompt}\n\nAssistant:",
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens_to_sample"] = max_tokens
                
            if stop:
                params["stop_sequences"] = stop
            
            # Make API call
            response = client.completions.create(**params)
            
            # Format response
            return {
                "text": response.completion.strip(),
                "finish_reason": "stop" if response.stop_reason == "stop_sequence" else response.stop_reason,
                "usage": {
                    "prompt_tokens": 0,  # Anthropic doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("Anthropic Python package not installed", 
                          recovery_hint="Install with 'pip install anthropic'",
                          provider="anthropic")
        except Exception as e:
            raise APIError(f"Anthropic API error: {str(e)}", 
                          original_exception=e,
                          provider="anthropic")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Generate a chat completion using Anthropic API."""
        try:
            from anthropic import Anthropic
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Anthropic API key not found", 
                               recovery_hint="Set the ANTHROPIC_API_KEY environment variable",
                               provider="anthropic")
            
            # Initialize client
            client = Anthropic(api_key=self.api_key)
            
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "assistant"
                anthropic_messages.append({"role": role, "content": msg["content"]})
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "messages": anthropic_messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop_sequences"] = stop
            
            # Make API call
            response = client.messages.create(**params)
            
            # Format response
            return {
                "text": response.content[0].text,
                "message": {"role": "assistant", "content": response.content[0].text},
                "finish_reason": "stop",  # Anthropic doesn't provide exact finish reason in messages API
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except ImportError:
            raise APIError("Anthropic Python package not installed", 
                          recovery_hint="Install with 'pip install anthropic'",
                          provider="anthropic")
        except Exception as e:
            raise APIError(f"Anthropic API error: {str(e)}", 
                          original_exception=e,
                          provider="anthropic")
    
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Stream a chat completion using Anthropic API."""
        try:
            from anthropic import Anthropic
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Anthropic API key not found", 
                               recovery_hint="Set the ANTHROPIC_API_KEY environment variable",
                               provider="anthropic")
            
            # Initialize client
            client = Anthropic(api_key=self.api_key)
            
            # Convert messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "assistant"
                anthropic_messages.append({"role": role, "content": msg["content"]})
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "messages": anthropic_messages,
                "temperature": temperature,
                "stream": True,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop_sequences"] = stop
            
            # Make API call
            full_text = ""
            with client.messages.stream(**params) as stream:
                for chunk in stream:
                    if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                        content = chunk.delta.text
                        if content:
                            full_text += content
                            if callback:
                                callback(content)
            
            # Format response
            return {
                "text": full_text.strip(),
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"  # Streaming doesn't provide this accurately
            }
        except ImportError:
            raise APIError("Anthropic Python package not installed", 
                          recovery_hint="Install with 'pip install anthropic'",
                          provider="anthropic")
        except Exception as e:
            raise APIError(f"Anthropic API error: {str(e)}", 
                          original_exception=e,
                          provider="anthropic")
    
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """
        Generate embeddings using Anthropic API.
        
        Note: Anthropic doesn't provide embeddings API, so this falls back to OpenAI.
        """
        # Anthropic doesn't provide embeddings API
        raise APIError("Anthropic does not provide embeddings API", 
                      recovery_hint="Use OpenAIAdapter for embeddings",
                      provider="anthropic")


class HuggingFaceAdapter(ModelAdapter):
    """Adapter for HuggingFace models."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("HUGGINGFACE_API_KEY")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Generate a text completion using HuggingFace API."""
        try:
            from huggingface_hub import InferenceClient
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("HuggingFace API key not found", 
                               recovery_hint="Set the HUGGINGFACE_API_KEY environment variable",
                               provider="huggingface")
            
            # Initialize client
            client = InferenceClient(token=self.api_key)
            
            # Set up parameters
            params = {
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_new_tokens"] = max_tokens
                
            # Make API call
            response = client.text_generation(
                prompt,
                model=self.model_name,
                **params
            )
            
            # Format response
            return {
                "text": response.strip(),
                "finish_reason": "stop",  # HF doesn't provide finish reason
                "usage": {
                    "prompt_tokens": 0,  # HF doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("HuggingFace hub package not installed", 
                          recovery_hint="Install with 'pip install huggingface_hub'",
                          provider="huggingface")
        except Exception as e:
            raise APIError(f"HuggingFace API error: {str(e)}", 
                          original_exception=e,
                          provider="huggingface")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Generate a chat completion using HuggingFace API."""
        try:
            from huggingface_hub import InferenceClient
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("HuggingFace API key not found", 
                               recovery_hint="Set the HUGGINGFACE_API_KEY environment variable",
                               provider="huggingface")
            
            # Initialize client
            client = InferenceClient(token=self.api_key)
            
            # Convert messages to HF format
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"<|system|>\n{msg['content']}\n"
                elif msg["role"] == "user":
                    prompt += f"<|user|>\n{msg['content']}\n"
                elif msg["role"] == "assistant":
                    prompt += f"<|assistant|>\n{msg['content']}\n"
            
            prompt += "<|assistant|>\n"
            
            # Set up parameters
            params = {
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_new_tokens"] = max_tokens
                
            # Make API call
            response = client.text_generation(
                prompt,
                model=self.model_name,
                **params
            )
            
            # Format response
            return {
                "text": response.strip(),
                "message": {"role": "assistant", "content": response.strip()},
                "finish_reason": "stop",  # HF doesn't provide finish reason
                "usage": {
                    "prompt_tokens": 0,  # HF doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("HuggingFace hub package not installed", 
                          recovery_hint="Install with 'pip install huggingface_hub'",
                          provider="huggingface")
        except Exception as e:
            raise APIError(f"HuggingFace API error: {str(e)}", 
                          original_exception=e,
                          provider="huggingface")
    
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Stream a chat completion using HuggingFace API."""
        try:
            from huggingface_hub import InferenceClient
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("HuggingFace API key not found", 
                               recovery_hint="Set the HUGGINGFACE_API_KEY environment variable",
                               provider="huggingface")
            
            # Initialize client
            client = InferenceClient(token=self.api_key)
            
            # Convert messages to HF format
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"<|system|>\n{msg['content']}\n"
                elif msg["role"] == "user":
                    prompt += f"<|user|>\n{msg['content']}\n"
                elif msg["role"] == "assistant":
                    prompt += f"<|assistant|>\n{msg['content']}\n"
            
            prompt += "<|assistant|>\n"
            
            # Set up parameters
            params = {
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_new_tokens"] = max_tokens
                
            # Make API call
            full_text = ""
            for token in client.text_generation(
                prompt,
                model=self.model_name,
                stream=True,
                **params
            ):
                if token:
                    full_text += token
                    if callback:
                        callback(token)
            
            # Format response
            return {
                "text": full_text.strip(),
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"  # Streaming doesn't provide this accurately
            }
        except ImportError:
            raise APIError("HuggingFace hub package not installed", 
                          recovery_hint="Install with 'pip install huggingface_hub'",
                          provider="huggingface")
        except Exception as e:
            raise APIError(f"HuggingFace API error: {str(e)}", 
                          original_exception=e,
                          provider="huggingface")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """Generate embeddings using HuggingFace API."""
        try:
            from huggingface_hub import InferenceClient
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("HuggingFace API key not found", 
                               recovery_hint="Set the HUGGINGFACE_API_KEY environment variable",
                               provider="huggingface")
            
            # Initialize client
            client = InferenceClient(token=self.api_key)
            
            # Set embedding model
            embedding_model = kwargs.get("embedding_model", self.model_name)
            
            # Get embeddings
            embeddings = []
            for text in texts:
                embedding = client.feature_extraction(
                    text,
                    model=embedding_model
                )
                embeddings.append(embedding)
            
            return embeddings
        except ImportError:
            raise APIError("HuggingFace hub package not installed", 
                          recovery_hint="Install with 'pip install huggingface_hub'",
                          provider="huggingface")
        except Exception as e:
            raise APIError(f"HuggingFace API error: {str(e)}", 
                          original_exception=e,
                          provider="huggingface")


class GeminiAdapter(ModelAdapter):
    """Adapter for Google Gemini models."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("GOOGLE_API_KEY")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Generate a text completion using Google Gemini API."""
        try:
            import google.generativeai as genai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Google API key not found", 
                               recovery_hint="Set the GOOGLE_API_KEY environment variable",
                               provider="google")
            
            # Configure genai
            genai.configure(api_key=self.api_key)
            
            # Set up parameters
            params = {
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_output_tokens"] = max_tokens
                
            # Make API call
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt, **params)
            
            # Format response
            return {
                "text": response.text,
                "finish_reason": "stop",  # Gemini doesn't provide finish reason
                "usage": {
                    "prompt_tokens": 0,  # Gemini doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("Google generative AI package not installed", 
                          recovery_hint="Install with 'pip install google-generativeai'",
                          provider="google")
        except Exception as e:
            raise APIError(f"Google Gemini API error: {str(e)}", 
                          original_exception=e,
                          provider="google")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Generate a chat completion using Google Gemini API."""
        try:
            import google.generativeai as genai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Google API key not found", 
                               recovery_hint="Set the GOOGLE_API_KEY environment variable",
                               provider="google")
            
            # Configure genai
            genai.configure(api_key=self.api_key)
            
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append({"role": role, "parts": [msg["content"]]})
            
            # Set up parameters
            params = {
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_output_tokens"] = max_tokens
                
            # Make API call
            model = genai.GenerativeModel(self.model_name)
            chat = model.start_chat(history=gemini_messages)
            response = chat.send_message(gemini_messages[-1]["parts"][0], **params)
            
            # Format response
            return {
                "text": response.text,
                "message": {"role": "assistant", "content": response.text},
                "finish_reason": "stop",  # Gemini doesn't provide finish reason
                "usage": {
                    "prompt_tokens": 0,  # Gemini doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("Google generative AI package not installed", 
                          recovery_hint="Install with 'pip install google-generativeai'",
                          provider="google")
        except Exception as e:
            raise APIError(f"Google Gemini API error: {str(e)}", 
                          original_exception=e,
                          provider="google")
    
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Stream a chat completion using Google Gemini API."""
        try:
            import google.generativeai as genai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Google API key not found", 
                               recovery_hint="Set the GOOGLE_API_KEY environment variable",
                               provider="google")
            
            # Configure genai
            genai.configure(api_key=self.api_key)
            
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append({"role": role, "parts": [msg["content"]]})
            
            # Set up parameters
            params = {
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_output_tokens"] = max_tokens
                
            # Make API call
            model = genai.GenerativeModel(self.model_name)
            chat = model.start_chat(history=gemini_messages)
            
            full_text = ""
            for chunk in chat.send_message(
                gemini_messages[-1]["parts"][0],
                stream=True,
                **params
            ):
                if chunk.text:
                    full_text += chunk.text
                    if callback:
                        callback(chunk.text)
            
            # Format response
            return {
                "text": full_text.strip(),
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"  # Streaming doesn't provide this accurately
            }
        except ImportError:
            raise APIError("Google generative AI package not installed", 
                          recovery_hint="Install with 'pip install google-generativeai'",
                          provider="google")
        except Exception as e:
            raise APIError(f"Google Gemini API error: {str(e)}", 
                          original_exception=e,
                          provider="google")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """Generate embeddings using Google Gemini API."""
        try:
            import google.generativeai as genai
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Google API key not found", 
                               recovery_hint="Set the GOOGLE_API_KEY environment variable",
                               provider="google")
            
            # Configure genai
            genai.configure(api_key=self.api_key)
            
            # Set embedding model
            embedding_model = kwargs.get("embedding_model", "embedding-001")
            
            # Get embeddings
            embedding_model = genai.get_model(embedding_model)
            
            embeddings = []
            for text in texts:
                result = embedding_model.embed_content(text)
                embeddings.append(result["embedding"])
            
            return embeddings
        except ImportError:
            raise APIError("Google generative AI package not installed", 
                          recovery_hint="Install with 'pip install google-generativeai'",
                          provider="google")
        except Exception as e:
            raise APIError(f"Google Gemini API error: {str(e)}", 
                          original_exception=e,
                          provider="google")


class CohereAdapter(ModelAdapter):
    """Adapter for Cohere models."""
    
    def _get_api_key_from_env(self) -> Optional[str]:
        return os.environ.get("COHERE_API_KEY")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Generate a text completion using Cohere API."""
        try:
            import cohere
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Cohere API key not found", 
                               recovery_hint="Set the COHERE_API_KEY environment variable",
                               provider="cohere")
            
            # Initialize client
            client = cohere.Client(api_key=self.api_key)
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop_sequences"] = stop
            
            # Make API call
            response = client.generate(**params)
            
            # Format response
            return {
                "text": response.generations[0].text,
                "finish_reason": "stop" if response.generations[0].finish_reason == "COMPLETE" else response.generations[0].finish_reason,
                "usage": {
                    "prompt_tokens": 0,  # Cohere doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("Cohere Python package not installed", 
                          recovery_hint="Install with 'pip install cohere'",
                          provider="cohere")
        except Exception as e:
            raise APIError(f"Cohere API error: {str(e)}", 
                          original_exception=e,
                          provider="cohere")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    @cache_response(ttl=3600)  # Cache for 1 hour
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Generate a chat completion using Cohere API."""
        try:
            import cohere
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Cohere API key not found", 
                               recovery_hint="Set the COHERE_API_KEY environment variable",
                               provider="cohere")
            
            # Initialize client
            client = cohere.Client(api_key=self.api_key)
            
            # Convert messages to Cohere format
            chat_history = []
            message = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    # Prepend system message to user message
                    if not message:
                        message = msg["content"]
                elif msg["role"] == "user":
                    if message:
                        message += "\n\n" + msg["content"]
                    else:
                        message = msg["content"]
                elif msg["role"] == "assistant" and len(chat_history) > 0:
                    # Add to chat history
                    chat_history.append({"role": "USER", "message": chat_history[-1]["message"]})
                    chat_history.append({"role": "CHATBOT", "message": msg["content"]})
                elif msg["role"] == "assistant":
                    # First message, no user message yet
                    chat_history.append({"role": "CHATBOT", "message": msg["content"]})
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "message": message,
                "temperature": temperature,
                **kwargs
            }
            
            if len(chat_history) > 0:
                params["chat_history"] = chat_history
                
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop_sequences"] = stop
            
            # Make API call
            response = client.chat(**params)
            
            # Format response
            return {
                "text": response.text,
                "message": {"role": "assistant", "content": response.text},
                "finish_reason": "stop",  # Cohere doesn't provide finish reason in chat API
                "usage": {
                    "prompt_tokens": 0,  # Cohere doesn't provide token usage
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except ImportError:
            raise APIError("Cohere Python package not installed", 
                          recovery_hint="Install with 'pip install cohere'",
                          provider="cohere")
        except Exception as e:
            raise APIError(f"Cohere API error: {str(e)}", 
                          original_exception=e,
                          provider="cohere")
    
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Stream a chat completion using Cohere API."""
        try:
            import cohere
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Cohere API key not found", 
                               recovery_hint="Set the COHERE_API_KEY environment variable",
                               provider="cohere")
            
            # Initialize client
            client = cohere.Client(api_key=self.api_key)
            
            # Convert messages to Cohere format
            chat_history = []
            message = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    # Prepend system message to user message
                    if not message:
                        message = msg["content"]
                elif msg["role"] == "user":
                    if message:
                        message += "\n\n" + msg["content"]
                    else:
                        message = msg["content"]
                elif msg["role"] == "assistant" and len(chat_history) > 0:
                    # Add to chat history
                    chat_history.append({"role": "USER", "message": chat_history[-1]["message"]})
                    chat_history.append({"role": "CHATBOT", "message": msg["content"]})
                elif msg["role"] == "assistant":
                    # First message, no user message yet
                    chat_history.append({"role": "CHATBOT", "message": msg["content"]})
            
            # Set up parameters
            params = {
                "model": self.model_name,
                "message": message,
                "temperature": temperature,
                **kwargs
            }
            
            if len(chat_history) > 0:
                params["chat_history"] = chat_history
                
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop_sequences"] = stop
            
            # Make API call
            full_text = ""
            for event in client.chat_stream(**params):
                if event.event_type == "text-generation":
                    full_text += event.text
                    if callback:
                        callback(event.text)
            
            # Format response
            return {
                "text": full_text.strip(),
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"  # Streaming doesn't provide this accurately
            }
        except ImportError:
            raise APIError("Cohere Python package not installed", 
                          recovery_hint="Install with 'pip install cohere'",
                          provider="cohere")
        except Exception as e:
            raise APIError(f"Cohere API error: {str(e)}", 
                          original_exception=e,
                          provider="cohere")
    
    @retry(max_attempts=3, backoff_factor=1.0)
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """Generate embeddings using Cohere API."""
        try:
            import cohere
            
            # Ensure API key is set
            if not self.api_key:
                raise APIError("Cohere API key not found", 
                               recovery_hint="Set the COHERE_API_KEY environment variable",
                               provider="cohere")
            
            # Initialize client
            client = cohere.Client(api_key=self.api_key)
            
            # Set up parameters
            params = {
                "model": kwargs.get("embedding_model", "embed-english-v3.0"),
                "texts": texts,
                **kwargs
            }
            
            # Make API call
            response = client.embed(**params)
            
            # Extract embeddings
            return response.embeddings
        except ImportError:
            raise APIError("Cohere Python package not installed", 
                          recovery_hint="Install with 'pip install cohere'",
                          provider="cohere")
        except Exception as e:
            raise APIError(f"Cohere API error: {str(e)}", 
                          original_exception=e,
                          provider="cohere")


class LlamaCppAdapter(ModelAdapter):
    """Adapter for local models via llama.cpp."""
    
    def __init__(self, model_name: str, model_path: str, **kwargs):
        """
        Initialize a llama.cpp adapter.
        
        Args:
            model_name: Name of the model
            model_path: Path to the model file
            **kwargs: Additional parameters
        """
        super().__init__(model_name, **kwargs)
        self.model_path = model_path
        self._llama = None
    
    def _get_api_key_from_env(self) -> Optional[str]:
        # No API key needed for local models
        return None
    
    def _load_model(self):
        """Load the model if not already loaded."""
        try:
            from llama_cpp import Llama
            
            if self._llama is None:
                self._llama = Llama(
                    model_path=self.model_path,
                    **self.config
                )
            
            return self._llama
        except ImportError:
            raise APIError("llama-cpp-python package not installed", 
                          recovery_hint="Install with 'pip install llama-cpp-python'",
                          provider="llama.cpp")
        except Exception as e:
            raise APIError(f"Failed to load model: {str(e)}", 
                          original_exception=e,
                          provider="llama.cpp")
    
    @cache_response(ttl=3600)  # Cache for 1 hour
    def complete(self, 
                prompt: str, 
                temperature: float = 0.0, 
                max_tokens: Optional[int] = None, 
                stop: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Generate a text completion using llama.cpp."""
        try:
            llama = self._load_model()
            
            # Set up parameters
            params = {
                "prompt": prompt,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop"] = stop
            
            # Make API call
            response = llama(**params)
            
            # Format response
            return {
                "text": response["choices"][0]["text"],
                "finish_reason": response["choices"][0]["finish_reason"],
                "usage": {
                    "prompt_tokens": response["usage"]["prompt_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "total_tokens": response["usage"]["total_tokens"]
                }
            }
        except Exception as e:
            raise APIError(f"llama.cpp error: {str(e)}", 
                          original_exception=e,
                          provider="llama.cpp")
    
    @cache_response(ttl=3600)  # Cache for 1 hour
    def chat_complete(self, 
                     messages: MessageList, 
                     temperature: float = 0.0, 
                     max_tokens: Optional[int] = None,
                     stop: Optional[List[str]] = None,
                     **kwargs) -> Dict[str, Any]:
        """Generate a chat completion using llama.cpp."""
        try:
            llama = self._load_model()
            
            # Format messages as a single prompt
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"<|system|>\n{msg['content']}\n"
                elif msg["role"] == "user":
                    prompt += f"<|user|>\n{msg['content']}\n"
                elif msg["role"] == "assistant":
                    prompt += f"<|assistant|>\n{msg['content']}\n"
            
            prompt += "<|assistant|>\n"
            
            # Set up parameters
            params = {
                "prompt": prompt,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop"] = stop
            
            # Make API call
            response = llama(**params)
            
            # Format response
            return {
                "text": response["choices"][0]["text"],
                "message": {"role": "assistant", "content": response["choices"][0]["text"]},
                "finish_reason": response["choices"][0]["finish_reason"],
                "usage": {
                    "prompt_tokens": response["usage"]["prompt_tokens"],
                    "completion_tokens": response["usage"]["completion_tokens"],
                    "total_tokens": response["usage"]["total_tokens"]
                }
            }
        except Exception as e:
            raise APIError(f"llama.cpp error: {str(e)}", 
                          original_exception=e,
                          provider="llama.cpp")
    
    def stream_chat_complete(self, 
                           messages: MessageList, 
                           temperature: float = 0.0, 
                           max_tokens: Optional[int] = None,
                           stop: Optional[List[str]] = None,
                           callback: Optional[Callable[[str], None]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Stream a chat completion using llama.cpp."""
        try:
            llama = self._load_model()
            
            # Format messages as a single prompt
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"<|system|>\n{msg['content']}\n"
                elif msg["role"] == "user":
                    prompt += f"<|user|>\n{msg['content']}\n"
                elif msg["role"] == "assistant":
                    prompt += f"<|assistant|>\n{msg['content']}\n"
            
            prompt += "<|assistant|>\n"
            
            # Set up parameters
            params = {
                "prompt": prompt,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if stop:
                params["stop"] = stop
            
            # Make API call
            full_text = ""
            for chunk in llama.create_completion(
                **params,
                stream=True
            ):
                text = chunk["choices"][0]["text"]
                full_text += text
                if callback:
                    callback(text)
            
            # Format response
            return {
                "text": full_text.strip(),
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"  # Streaming doesn't provide this accurately
            }
        except Exception as e:
            raise APIError(f"llama.cpp error: {str(e)}", 
                          original_exception=e,
                          provider="llama.cpp")
    
    def embeddings(self, 
                  texts: List[str], 
                  **kwargs) -> List[List[float]]:
        """Generate embeddings using llama.cpp."""
        try:
            llama = self._load_model()
            
            # Get embeddings
            embeddings = []
            for text in texts:
                embedding = llama.embed(text)
                embeddings.append(embedding)
            
            return embeddings
        except Exception as e:
            raise APIError(f"llama.cpp error: {str(e)}", 
                          original_exception=e,
                          provider="llama.cpp")


# Factory function to get appropriate adapter
def get_model_adapter(provider: str,
                     model_name: str,
                     api_key: Optional[str] = None,
                     **kwargs) -> ModelAdapter:
    """
    Get a model adapter for the specified provider and model.
    
    Args:
        provider: Provider name (openai, anthropic, huggingface, etc.)
        model_name: Name of the model
        api_key: API key for the provider
        **kwargs: Additional provider-specific parameters
        
    Returns:
        ModelAdapter instance
        
    Raises:
        APIError: If the provider is not supported
    """
    provider = provider.lower()
    
    if provider == "openai":
        return OpenAIAdapter(model_name, api_key, **kwargs)
    elif provider == "anthropic":
        return AnthropicAdapter(model_name, api_key, **kwargs)
    elif provider in ["huggingface", "hf"]:
        return HuggingFaceAdapter(model_name, api_key, **kwargs)
    elif provider in ["google", "gemini"]:
        return GeminiAdapter(model_name, api_key, **kwargs)
    elif provider == "cohere":
        return CohereAdapter(model_name, api_key, **kwargs)
    elif provider in ["llama.cpp", "llamacpp", "llama"]:
        model_path = kwargs.pop("model_path")
        return LlamaCppAdapter(model_name, model_path, **kwargs)
    else:
        raise APIError(f"Unsupported provider: {provider}", 
                      recovery_hint="Choose from: openai, anthropic, huggingface, google, cohere, llama.cpp",
                      provider=provider)