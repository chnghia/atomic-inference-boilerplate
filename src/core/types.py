"""
Shared type definitions for Atomic Inference.

This module contains all common types used across the framework:
- MemoryChunk: Represents a piece of context from RAG/vector store
- LLMConfig: Configuration for LLM calls
"""

from typing import TypeVar, Generic, Any
from pydantic import BaseModel, Field


# Generic type for output schemas
T = TypeVar('T', bound=BaseModel)


class MemoryChunk(BaseModel):
    """
    Represents a chunk of memory/context from RAG or vector store.
    
    Attributes:
        content: The actual text content of the memory
        source: Optional source identifier (file path, URL, etc.)
        score: Optional relevance score from vector search
        metadata: Optional additional metadata
    """
    content: str
    source: str | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None


class LLMConfig(BaseModel):
    """
    Configuration for LLM calls.
    
    Attributes:
        model: Model identifier (e.g., "gpt-4o-mini", "claude-3-haiku-20240307")
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum tokens in response
        max_retries: Number of retries on validation failure
    """
    model: str = Field(default="gpt-4o-mini", description="LLM model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)
    max_retries: int = Field(default=3, ge=1)


class InferenceResult(BaseModel, Generic[T]):
    """
    Wrapper for inference results with metadata.
    
    Attributes:
        data: The validated output data
        model: Model used for inference
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion
    """
    data: Any  # Will be T at runtime
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
