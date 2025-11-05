"""LLM client abstraction and simple providers."""

from __future__ import annotations

import os
import re
from typing import Protocol
import httpx
import logging

logger = logging.getLogger(__name__)

# Import os at module level for get_llm_client
import os


class LLMClient(Protocol):
    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate a text completion for a prompt."""


class HTTPLLMClient:
    """HTTP-based LLM client for Mistral chat API.

    Purpose:
        Call local Mistral chat API via HTTP.
        Automatically detects Docker vs host access and adjusts URL accordingly.

    Args:
        url: Base URL of the LLM service (e.g., http://mistral-chat:8000)
        timeout: Request timeout in seconds
    """

    def __init__(self, url: str | None = None, timeout: float = 30.0) -> None:
        self.url = url or os.getenv("LLM_URL", "http://localhost:8001")
        if not self.url.startswith("http"):
            self.url = f"http://{self.url}"
        # Remove trailing slash
        self.url = self.url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._host_url: str | None = None  # Cached host URL for fallback
        
    def _get_host_url(self, docker_url: str) -> str:
        """Convert Docker URL to host URL if running from host.
        
        Args:
            docker_url: Docker network URL (e.g., http://llm-server:8000)
            
        Returns:
            Host URL (e.g., http://localhost:8080)
        """
        # Map common Docker service names to host ports
        docker_to_host = {
            "llm-server:8000": "localhost:8001",  # Port mapping: 8000->8001
            "mistral-chat:8000": "localhost:8001",
            "mistral-vllm:8000": "localhost:8001",
        }
        
        # Extract host:port from URL
        url_parts = docker_url.replace("http://", "").replace("https://", "")
        if url_parts in docker_to_host:
            return f"http://{docker_to_host[url_parts]}"
        
        # Default: try common ports
        if ":8000" in url_parts:
            return "http://localhost:8001"  # Common mapping
        if ":8001" in url_parts:
            return "http://localhost:8001"
            
        return docker_url  # Fallback to original

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate text via OpenAI-compatible chat completions API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant message content from choices[0].message.content

        Raises:
            httpx.RequestError: On network errors
            httpx.HTTPStatusError: On HTTP errors
            ValueError: On empty or invalid response structure
        """
        client = await self._get_client()
        
        # Try /chat endpoint first (used by local Mistral API)
        chat_url = f"{self.url}/chat"
        chat_payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = await client.post(chat_url, json=chat_payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            content = (data.get("response") or "").strip()
            if content:
                return content
            # If response field is empty but status is OK, raise error to trigger fallback
            error_msg = f"Empty response from /chat endpoint: {data}"
            logger.warning(error_msg)
            raise ValueError(error_msg)
        except httpx.HTTPStatusError as e:
            # If /chat returns 404, try OpenAI-compatible /v1/chat/completions
            if e.response is not None and e.response.status_code == 404:
                logger.debug(f"/chat endpoint not found, trying /v1/chat/completions")
                pass  # Fall through to try /v1/chat/completions
            else:
                logger.warning(f"HTTP error from /chat endpoint: {e.response.status_code if e.response else 'unknown'} - {e}")
                # Try host URL fallback for HTTP errors too
                if self._host_url is None and ("llm-server" in self.url or "mistral" in self.url.lower()):
                    self._host_url = self._get_host_url(self.url)
                    logger.info(f"Trying host URL fallback after HTTP error: {self._host_url}")
                    try:
                        host_url = f"{self._host_url}/chat"
                        host_payload = {
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        }
                        response = await client.post(host_url, json=host_payload, timeout=self.timeout)
                        response.raise_for_status()
                        data = response.json()
                        content = (data.get("response") or "").strip()
                        if content:
                            logger.info(f"Successfully connected to LLM via host URL after HTTP error")
                            return content
                    except Exception as host_error:
                        logger.debug(f"Host URL fallback after HTTP error also failed: {host_error}")
                raise
        except httpx.ConnectError as e:
            logger.warning(f"Connection error to /chat endpoint: {e}")
            # Try host URL fallback before re-raising
            if self._host_url is None and ("llm-server" in self.url or "mistral" in self.url.lower()):
                self._host_url = self._get_host_url(self.url)
                logger.info(f"Trying host URL fallback after connection error: {self._host_url}")
                try:
                    host_url = f"{self._host_url}/chat"
                    host_payload = {
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                    response = await client.post(host_url, json=host_payload, timeout=self.timeout)
                    response.raise_for_status()
                    data = response.json()
                    content = (data.get("response") or "").strip()
                    if content:
                        logger.info(f"Successfully connected to LLM via host URL after connection error")
                        return content
                except Exception as host_error:
                    logger.debug(f"Host URL fallback after connection error also failed: {host_error}")
            raise  # Re-raise if all attempts failed
        except Exception as e:
            logger.warning(
                f"Unexpected error from /chat endpoint: {type(e).__name__}: {e}",
                exc_info=True
            )
            raise
        
        # Fallback: try OpenAI-compatible /v1/chat/completions endpoint
        openai_url = f"{self.url}/v1/chat/completions"
        openai_payload = {
            "model": os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.95,
            "stop": ["</s>", "[/INST]"]
        }
        
        try:
            response = await client.post(openai_url, json=openai_payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            # Validate and extract content
            if "choices" not in data or not data["choices"]:
                raise ValueError("Response missing 'choices'")
            message = data["choices"][0].get("message", {})
            content = (message.get("content") or "").strip()
            if not content:
                raise ValueError("LLM returned empty content")
            return content
        except httpx.HTTPStatusError:
            # Both endpoints failed, re-raise to trigger host URL fallback
            raise
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            # If Docker URL failed, try host URL
            if self._host_url is None and ("llm-server" in self.url or "mistral" in self.url.lower()):
                self._host_url = self._get_host_url(self.url)
                logger.debug(f"Docker URL failed, trying host URL: {self._host_url}")
                try:
                    # Try /chat endpoint first (legacy)
                    host_url = f"{self._host_url}/chat"
                    host_payload = {
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    }
                    response = await client.post(host_url, json=host_payload, timeout=self.timeout)
                    response.raise_for_status()
                    data = response.json()
                    content = (data.get("response") or "").strip()
                    if content:
                        logger.info(f"Successfully connected to LLM via host URL: {self._host_url}")
                        return content
                    
                    # If /chat doesn't work, try /v1/chat/completions
                    host_url = f"{self._host_url}/v1/chat/completions"
                    host_openai_payload = {
                        "model": os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": 0.95,
                        "stop": ["</s>", "[/INST]"]
                    }
                    response = await client.post(host_url, json=host_openai_payload, timeout=self.timeout)
                    response.raise_for_status()
                    data = response.json()
                    if "choices" not in data or not data["choices"]:
                        raise ValueError("Response missing 'choices'")
                    message = data["choices"][0].get("message", {})
                    content = (message.get("content") or "").strip()
                    if content:
                        logger.info(f"Successfully connected to LLM via host URL: {self._host_url}")
                        return content
                except Exception as host_error:
                    logger.debug(f"Host URL also failed: {host_error}")
            logger.warning("LLM connection error, service may be unavailable: %s", e, extra={"url": self.url})
            raise
        except Exception:
            # Re-raise to let ResilientLLMClient fallback if needed
            raise

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class FallbackLLMClient:
    """Trivial LLM that returns context-aware fallback responses.
    
    Analyzes the prompt to determine if it's for summarization or intent parsing,
    and returns appropriate fallback format.
    """

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate context-aware fallback response.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (ignored)
            max_tokens: Maximum tokens (ignored)
            
        Returns:
            Fallback response in appropriate format
        """
        prompt_lower = prompt.lower()
        
        # Detect summarization prompts - check for Russian/English keywords
        # More comprehensive detection for summarization prompts
        summarization_keywords = [
            "суммариз", "summarize", "суммар", "итогов", "факт",
            "канала", "channel", "пост", "post", "новост", "news",
            "перед тобой", "перед тобой фрагмент", "перед тобой несколько",
            "ключевых фактов", "key facts", "фрагмент", "fragment",
            "напиши", "write", "предложен", "sentences", "предложения",
            "дайджест", "digest", "резюме", "summary", "саммар"
        ]
        
        intent_keywords = [
            "извлеки", "extract", "intent", "задача", "task",
            "deadline", "приоритет", "priority", "title", "название",
            "json", "needs_clarification"
        ]
        
        is_summarization = any(keyword in prompt_lower for keyword in summarization_keywords)
        is_intent = any(keyword in prompt_lower for keyword in intent_keywords)
        
        # Stronger detection: if prompt contains "пост" or "post" and summarization keywords, it's summarization
        if ("пост" in prompt_lower or "post" in prompt_lower) and is_summarization:
            is_intent = False
            is_summarization = True
        
        # If prompt explicitly asks for summary or digest, prioritize summarization
        if ("суммар" in prompt_lower or "summary" in prompt_lower or 
            "дайджест" in prompt_lower or "digest" in prompt_lower):
            is_intent = False
            is_summarization = True
        
        if is_summarization and not is_intent:
            # Generate simple text summary from prompt content
            # Extract post texts - look for numbered lines like "1. текст поста"
            # Also look for posts after markers like "ФРАГМЕНТ:" or "POSTS:" or "ПОСТЫ:"
            lines = prompt.split('\n')
            post_texts = []
            in_content_section = False
            skip_keywords = ['важно', 'пример', 'суммар', 'верни', 'json', 'задача', 'task', 
                           'фрагмент', 'fragment', 'критич', 'critical', 'пример правильного', 
                           'пример неправильного', 'example correct', 'example wrong']
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                    
                line_lower = line_stripped.lower()
                
                # Detect content sections
                if any(marker in line_lower for marker in ['фрагмент:', 'fragment:', 'посты:', 'posts:', 'post:', 'post ']):
                    in_content_section = True
                    continue
                
                # Stop at instruction sections
                if any(marker in line_lower for marker in ['ключевые факты:', 'key facts:', 'итоговая суммаризация:', 'final summary:', 'критически важно:', 'critical:']):
                    in_content_section = False
                    break
                
                # Skip instructions and empty lines
                if (not in_content_section and 
                    any(skip in line_lower for skip in skip_keywords) or
                    line_stripped.startswith(('Пример', 'ВАЖНО', 'Example', 'CRITICAL', 'EXAMPLE'))):
                    continue
                    
                # Look for numbered lines: "1. текст" or "1) текст"
                numbered_match = re.match(r'^\d+[\.\)]\s*(.+)$', line_stripped)
                if numbered_match:
                    text = numbered_match.group(1).strip()
                    # Filter out very short or instruction-like text
                    if len(text) > 15 and not any(skip in text.lower() for skip in skip_keywords):
                        post_texts.append(text)
                # Also capture non-numbered content lines in content section
                elif in_content_section and len(line_stripped) > 20:
                    # Skip lines that are clearly instructions
                    if not any(skip in line_lower for skip in skip_keywords):
                        # Check if line looks like actual content (not instruction)
                        if not line_stripped.lower().startswith(('задача:', 'task:', 'пример:', 'example:', 'критич', 'critical')):
                            # Extract meaningful content (avoid repeating same text)
                            # Check if similar content already in recent posts
                            is_duplicate = False
                            if post_texts:
                                for recent_post in post_texts[-3:]:
                                    if line_stripped[:50].lower() in recent_post.lower()[:50] or recent_post.lower()[:50] in line_stripped[:50].lower():
                                        is_duplicate = True
                                        break
                            if not is_duplicate:
                                post_texts.append(line_stripped[:300])  # Limit length
            
            if post_texts:
                # Use more posts and create better summary
                # Take up to 5 posts, but ensure variety
                unique_posts = []
                seen_content = set()
                for post in post_texts:
                    # Simple deduplication - check if similar content already seen
                    post_lower = post.lower()[:50]  # First 50 chars for comparison
                    if post_lower not in seen_content:
                        seen_content.add(post_lower)
                        unique_posts.append(post)
                        if len(unique_posts) >= 5:
                            break
                
                # Create summary from unique posts
                # Filter out instruction-like text that might have been captured
                filtered_posts = []
                for post in unique_posts:
                    post_lower = post.lower()
                    # Skip posts that look like instructions
                    if not any(instr in post_lower for instr in [
                        'не используй', 'не нумеруй', 'только предложения', 'верни только',
                        'do not use', 'do not number', 'only sentences', 'return only',
                        'важно:', 'important:', 'пример:', 'example:'
                    ]):
                        filtered_posts.append(post)
                
                if not filtered_posts:
                    # If all filtered, use original but clean
                    filtered_posts = unique_posts[:3]
                
                summary = '. '.join(filtered_posts)
                if len(summary) > 500:
                    summary = summary[:500] + '...'
                if not summary.endswith(('.', '!', '?', '...')):
                    summary += '.'
                return summary
            else:
                # Generic fallback - extract meaningful content from prompt
                content_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    if (len(line_stripped) > 20 and 
                        not any(skip in line_stripped.lower() for skip in skip_keywords) and
                        not line_stripped.lower().startswith(('задача:', 'task:', 'пример:', 'example:', 'критич', 'critical', 'важно'))):
                        content_lines.append(line_stripped[:200])  # Limit length
                        if len(content_lines) >= 3:
                            break
                if content_lines:
                    summary = '. '.join(content_lines)
                    if len(summary) > 500:
                        summary = summary[:500] + '...'
                    if not summary.endswith(('.', '!', '?', '...')):
                        summary += '.'
                    return summary
                # Last resort: generic message with prompt hash for debugging
                import hashlib
                prompt_hash = hashlib.md5(prompt.encode()[:100]).hexdigest()[:8]
                return f"Обсуждаются основные темы канала. [fallback:{prompt_hash}]"
        else:
            # Default to intent parsing JSON format
            return (
                '{"title":"Task","description":"","deadline":null,'
                '"priority":"medium","tags":[],"needs_clarification":false,"questions":[]}'
            )


def get_llm_client(url: str | None = None, timeout: float = 120.0) -> LLMClient:
    """Get appropriate LLM client based on configuration.

    Purpose:
        Returns HTTPLLMClient if URL is configured, otherwise FallbackLLMClient.

    Args:
        url: LLM service URL (from env var LLM_URL if not provided)
        timeout: Request timeout in seconds (default: 120.0 for summarization)

    Returns:
        LLMClient instance
    """
    if url:
        logger.info(f"Using provided LLM URL: {url}")
        return HTTPLLMClient(url=url, timeout=timeout)
    llm_url = os.getenv("LLM_URL", "")
    if llm_url and llm_url.strip():
        logger.info(f"Using LLM URL from env: {llm_url}")
        return HTTPLLMClient(url=llm_url, timeout=timeout)
    logger.warning(
        f"LLM_URL not configured (value='{llm_url}'), using FallbackLLMClient. "
        f"This will result in poor summarization quality."
    )
    return FallbackLLMClient()


class ResilientLLMClient:
    """LLM client that falls back to FallbackLLMClient on errors.

    Purpose:
        Wraps HTTPLLMClient and automatically falls back on connection failures.
    """

    def __init__(self, url: str | None = None) -> None:
        """Initialize resilient client.

        Args:
            url: LLM service URL
        """
        self._primary = get_llm_client(url) if url else get_llm_client()
        self._fallback = FallbackLLMClient()
        self._use_fallback = isinstance(self._primary, FallbackLLMClient)

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 256) -> str:
        """Generate with automatic fallback.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Generated text or fallback response
        """
        if self._use_fallback:
            return await self._fallback.generate(prompt, temperature, max_tokens)

        try:
            return await self._primary.generate(prompt, temperature, max_tokens)
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(f"LLM service unavailable, using fallback: {e}")
            return await self._fallback.generate(prompt, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"LLM error, using fallback: {e}")
            return await self._fallback.generate(prompt, temperature, max_tokens)


