"""
LLM Client Factory for Atomic Inference.

This module provides the create_client function that:
- Wraps LiteLLM with Instructor for structured output
- Centralizes API key management via environment variables
- Provides consistent configuration across providers
"""

import os
from typing import Type, TypeVar

import instructor
import litellm
from dotenv import load_dotenv
from pydantic import BaseModel

from src.core.types import LLMConfig


# Load environment variables
load_dotenv()

# Type variable for output schema
T = TypeVar("T", bound=BaseModel)


def create_client(
    config: LLMConfig | None = None,
    mode: instructor.Mode | None = None,
) -> instructor.Instructor:
    """
    Create an Instructor-patched LiteLLM client.
    
    This factory creates a client that:
    - Routes to multiple providers via LiteLLM
    - Enforces structured output via Instructor
    - Auto-retries on validation failure
    
    Args:
        config: LLM configuration (uses defaults if not provided)
        mode: Instructor mode. Defaults to MD_JSON for better compatibility
              with local models (LM Studio, Ollama, etc.)
              Options:
              - instructor.Mode.JSON: Strict JSON mode (OpenAI, Anthropic)
              - instructor.Mode.MD_JSON: Markdown JSON (local models, universal)
              - instructor.Mode.TOOLS: Tool calling mode (if supported)
        
    Returns:
        Instructor client ready for structured inference
        
    Example:
        client = create_client()
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            response_model=MySchema,
        )
    """
    if config is None:
        config = LLMConfig()
    
    # Use MD_JSON by default for better compatibility with local models
    # This extracts JSON from markdown code blocks instead of using response_format
    if mode is None:
        mode = instructor.Mode.MD_JSON
    
    # Create instructor client from litellm
    client = instructor.from_litellm(
        litellm.completion,
        mode=mode,
    )
    
    return client


def single_call_llm(
    messages: list[dict],
    response_model: Type[T],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    max_retries: int = 3,
) -> T:
    """
    Make a single LLM call with structured output (for testing/simple cases).
    
    This is a convenience function for simple use cases and testing.
    For production, use AtomicUnit with templates instead.
    
    Args:
        messages: List of message dicts (role, content)
        response_model: Pydantic model for output validation
        model: Model identifier (defaults to env DEFAULT_MODEL or gpt-4o-mini)
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        max_retries: Retries on validation failure
        
    Returns:
        Validated Pydantic model instance
        
    Example:
        class Greeting(BaseModel):
            message: str
            
        result = single_call_llm(
            messages=[{"role": "user", "content": "Say hello"}],
            response_model=Greeting
        )
        print(result.message)  # "Hello!"
    """
    if model is None:
        model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    
    client = create_client()
    
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_model=response_model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
    )
    
    return response

