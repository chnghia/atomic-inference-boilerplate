"""
AtomicUnit - The Core Engine for Atomic Inference.

This module provides the AtomicUnit class that encapsulates:
- Template rendering (Jinja2)
- LLM calling (LiteLLM)
- Output validation (Instructor + Pydantic)

The AtomicUnit is the fundamental building block for all inference tasks.
"""

import os
from typing import Type, TypeVar, Generic

from pydantic import BaseModel

from src.core.types import MemoryChunk, LLMConfig
from src.core.renderer import TemplateRenderer
from src.core.client import create_client


T = TypeVar("T", bound=BaseModel)


class AtomicUnit(Generic[T]):
    """
    The Atomic Unit - a single, focused inference step.
    
    Encapsulates the entire inference pipeline:
    1. Render prompt template with context
    2. Call LLM via LiteLLM
    3. Validate output with Pydantic schema
    
    Example:
        class ExtractedEntity(BaseModel):
            name: str
            entity_type: str
            
        extractor = AtomicUnit(
            template_name="extraction.j2",
            output_schema=ExtractedEntity,
            model="gpt-4o-mini"
        )
        
        result = extractor.run({"text": "Apple Inc. is a technology company."})
        print(result.name)  # "Apple Inc."
    """
    
    def __init__(
        self,
        template_name: str,
        output_schema: Type[T],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_retries: int = 3,
        system_template: str | None = None,
    ):
        """
        Initialize an Atomic Unit.
        
        Args:
            template_name: Name of the user prompt template (e.g., "extraction.j2")
            output_schema: Pydantic model class for output validation
            model: LLM model identifier (defaults to env DEFAULT_MODEL)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            max_retries: Retries on validation failure
            system_template: Optional system prompt template name
        """
        self.template_name = template_name
        self.output_schema = output_schema
        self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.system_template = system_template
        
        # Initialize components
        self.renderer = TemplateRenderer()
        self.client = create_client()
    
    def run(
        self,
        context: dict | None = None,
        memories: list[MemoryChunk] | None = None,
        system_context: dict | None = None,
    ) -> T:
        """
        Execute the atomic inference pipeline.
        
        Pipeline:
        1. Inject memories into context (if provided)
        2. Render prompt template with context
        3. Call LLM with structured output
        4. Return validated Pydantic object
        
        Args:
            context: Dictionary of variables for the user prompt template
            memories: Optional list of MemoryChunk for RAG injection
            system_context: Optional dict for system prompt template
            
        Returns:
            Validated instance of output_schema
            
        Raises:
            ValidationError: If LLM output doesn't match schema after retries
        """
        if context is None:
            context = {}
        
        # Inject memories into context
        if memories:
            context["memories"] = memories
        
        # Render user prompt
        user_prompt = self.renderer.render(self.template_name, context)
        
        # Build messages
        messages = []
        
        # Add system message if template provided
        if self.system_template:
            sys_ctx = system_context or {}
            if memories:
                sys_ctx["memories"] = memories
            system_prompt = self.renderer.render(self.system_template, sys_ctx)
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": user_prompt})
        
        # Call LLM with structured output
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=self.output_schema,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=self.max_retries,
        )
        
        return response
    
    def preview_prompt(
        self,
        context: dict | None = None,
        memories: list[MemoryChunk] | None = None,
    ) -> str:
        """
        Preview the rendered prompt without calling the LLM.
        
        Useful for debugging and testing prompt templates.
        
        Args:
            context: Dictionary of variables for the template
            memories: Optional list of MemoryChunk
            
        Returns:
            Rendered prompt string
        """
        if context is None:
            context = {}
        
        if memories:
            context["memories"] = memories
        
        return self.renderer.render(self.template_name, context)
