"""
LLM Manager with Automatic Model Fallback

Manages LLM interactions with automatic switching when token limits are reached.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import httpx

from .config import Config, get_config


@dataclass
class TokenUsage:
    """Tracks token usage for a request."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str
    token_usage: TokenUsage
    duration_ms: int
    success: bool
    error: Optional[str] = None


class LLMManager:
    """
    Manages LLM interactions with automatic model fallback.
    
    Features:
    - Automatic switching to fallback models on token limit
    - Token tracking and estimation
    - Retry logic with exponential backoff
    - Model health checking
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.llm_config = self.config.llm
        
        # Model state
        self.current_model_index = 0
        self.available_models = [self.llm_config.primary_model] + self.llm_config.fallback_models
        self.model_health: Dict[str, bool] = {m: True for m in self.available_models}
        
        # Usage tracking
        self.total_tokens_used = 0
        self.session_token_count = 0
        self.model_switch_count = 0
        self.total_calls = 0
        
        # HTTP client
        self.client = httpx.Client(
            base_url=self.llm_config.ollama_base_url,
            timeout=self.llm_config.timeout,
        )
        
        logger.info(f"LLM Manager initialized with models: {self.available_models}")
    
    @property
    def current_model(self) -> str:
        """Get the current active model."""
        return self.available_models[self.current_model_index]
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimation: ~4 characters per token on average
        return len(text) // 4
    
    def check_token_limits(self, prompt_tokens: int) -> Tuple[bool, str]:
        """
        Check if we're approaching token limits.
        
        Returns:
            Tuple of (should_switch, reason)
        """
        limits = self.llm_config.token_limits
        
        if prompt_tokens >= limits.input_max:
            return True, f"Input tokens ({prompt_tokens}) exceed max ({limits.input_max})"
        
        if prompt_tokens >= limits.input_warning:
            logger.warning(f"Approaching token limit: {prompt_tokens}/{limits.input_max}")
        
        return False, ""
    
    def switch_model(self, reason: str = "") -> bool:
        """
        Switch to the next available model.
        
        Returns:
            True if successfully switched, False if no more models available
        """
        next_index = self.current_model_index + 1
        
        # Find next healthy model
        while next_index < len(self.available_models):
            model = self.available_models[next_index]
            if self.model_health.get(model, False):
                old_model = self.current_model
                self.current_model_index = next_index
                self.model_switch_count += 1
                logger.info(f"Switched model: {old_model} -> {self.current_model}. Reason: {reason}")
                return True
            next_index += 1
        
        logger.error("No more fallback models available")
        return False
    
    def reset_to_primary(self) -> None:
        """Reset to primary model (for new sessions)."""
        self.current_model_index = 0
        self.session_token_count = 0
        logger.info(f"Reset to primary model: {self.current_model}")
    
    async def check_model_health(self, model: str) -> bool:
        """Check if a model is available and responding."""
        try:
            async with httpx.AsyncClient(
                base_url=self.llm_config.ollama_base_url,
                timeout=10,
            ) as client:
                response = await client.post(
                    "/api/generate",
                    json={"model": model, "prompt": "hi", "stream": False},
                )
                healthy = response.status_code == 200
                self.model_health[model] = healthy
                return healthy
        except Exception as e:
            logger.warning(f"Model health check failed for {model}: {e}")
            self.model_health[model] = False
            return False
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM with automatic fallback.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            LLMResponse with the generated content or error
        """
        start_time = time.time()
        self.total_calls += 1
        
        # Estimate prompt tokens
        full_prompt = (system_prompt or "") + prompt
        estimated_tokens = self.estimate_tokens(full_prompt)
        
        # Check if we need to switch models
        should_switch, reason = self.check_token_limits(estimated_tokens)
        if should_switch:
            if not self.switch_model(reason):
                return LLMResponse(
                    content="",
                    model=self.current_model,
                    token_usage=TokenUsage(),
                    duration_ms=0,
                    success=False,
                    error="All models exhausted due to token limits",
                )
        
        # Prepare request
        request_body = {
            "model": self.current_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.llm_config.temperature,
                "num_predict": max_tokens or self.llm_config.max_tokens,
            },
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Try current model with retries
        max_retries = self.config.error_handling.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.post("/api/generate", json=request_body)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract token usage
                    token_usage = TokenUsage(
                        prompt_tokens=data.get("prompt_eval_count", estimated_tokens),
                        completion_tokens=data.get("eval_count", 0),
                        total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    )
                    
                    # Update tracking
                    self.total_tokens_used += token_usage.total_tokens
                    self.session_token_count += token_usage.total_tokens
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    return LLMResponse(
                        content=data.get("response", ""),
                        model=self.current_model,
                        token_usage=token_usage,
                        duration_ms=duration_ms,
                        success=True,
                    )
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    
            except httpx.TimeoutException:
                last_error = "Request timeout"
                logger.warning(f"Timeout on attempt {attempt + 1} for {self.current_model}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error on attempt {attempt + 1}: {e}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                backoff = min(
                    self.config.error_handling.exponential_backoff_base ** attempt,
                    self.config.error_handling.max_backoff_seconds,
                )
                time.sleep(backoff)
        
        # Current model failed, try switching
        if self.switch_model(f"Model {self.current_model} failed: {last_error}"):
            # Retry with new model
            return self.generate(prompt, system_prompt, temperature, max_tokens)
        
        duration_ms = int((time.time() - start_time) * 1000)
        return LLMResponse(
            content="",
            model=self.current_model,
            token_usage=TokenUsage(),
            duration_ms=duration_ms,
            success=False,
            error=f"All models failed. Last error: {last_error}",
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            LLMResponse with the generated content
        """
        start_time = time.time()
        self.total_calls += 1
        
        # Estimate total tokens from messages
        total_text = " ".join(m.get("content", "") for m in messages)
        estimated_tokens = self.estimate_tokens(total_text)
        
        # Check token limits
        should_switch, reason = self.check_token_limits(estimated_tokens)
        if should_switch:
            if not self.switch_model(reason):
                return LLMResponse(
                    content="",
                    model=self.current_model,
                    token_usage=TokenUsage(),
                    duration_ms=0,
                    success=False,
                    error="All models exhausted due to token limits",
                )
        
        request_body = {
            "model": self.current_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.llm_config.temperature,
                "num_predict": max_tokens or self.llm_config.max_tokens,
            },
        }
        
        max_retries = self.config.error_handling.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.post("/api/chat", json=request_body)
                
                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", {})
                    
                    token_usage = TokenUsage(
                        prompt_tokens=data.get("prompt_eval_count", estimated_tokens),
                        completion_tokens=data.get("eval_count", 0),
                        total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                    )
                    
                    self.total_tokens_used += token_usage.total_tokens
                    self.session_token_count += token_usage.total_tokens
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    return LLMResponse(
                        content=message.get("content", ""),
                        model=self.current_model,
                        token_usage=token_usage,
                        duration_ms=duration_ms,
                        success=True,
                    )
                else:
                    last_error = f"HTTP {response.status_code}"
                    
            except httpx.TimeoutException:
                last_error = "Request timeout"
            except Exception as e:
                last_error = str(e)
            
            if attempt < max_retries - 1:
                backoff = min(
                    self.config.error_handling.exponential_backoff_base ** attempt,
                    self.config.error_handling.max_backoff_seconds,
                )
                time.sleep(backoff)
        
        # Try switching models
        if self.switch_model(f"Model failed: {last_error}"):
            return self.chat(messages, temperature, max_tokens)
        
        duration_ms = int((time.time() - start_time) * 1000)
        return LLMResponse(
            content="",
            model=self.current_model,
            token_usage=TokenUsage(),
            duration_ms=duration_ms,
            success=False,
            error=f"All models failed. Last error: {last_error}",
        )
    
    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """Get embeddings for text using the embedding model."""
        try:
            response = self.client.post(
                "/api/embeddings",
                json={
                    "model": self.config.embeddings.model,
                    "prompt": text,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", [])
            else:
                logger.error(f"Embedding request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current LLM manager statistics."""
        return {
            "current_model": self.current_model,
            "model_index": self.current_model_index,
            "available_models": self.available_models,
            "model_health": self.model_health,
            "total_tokens_used": self.total_tokens_used,
            "session_tokens": self.session_token_count,
            "model_switches": self.model_switch_count,
            "total_calls": self.total_calls,
        }
    
    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Global LLM manager instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
