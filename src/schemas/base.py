"""
Base schemas for Atomic Inference.

This module provides common base classes for output schemas.
Extend these when creating task-specific schemas.
"""

from typing import Any
from pydantic import BaseModel, Field


class BaseExtraction(BaseModel):
    """
    Base class for extraction tasks.
    
    Provides common fields like confidence and reasoning.
    Extend this for specific extraction schemas.
    
    Example:
        class PersonExtraction(BaseExtraction):
            name: str
            age: int | None = None
    """
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the extraction (0.0-1.0)"
    )
    reasoning: str | None = Field(
        default=None,
        description="Optional reasoning/explanation for the extraction"
    )


class BaseResponse(BaseModel):
    """
    Base class for general LLM responses.
    
    Use when you need a structured response with optional metadata.
    
    Example:
        class AnalysisResponse(BaseResponse):
            summary: str
            key_points: list[str]
    """
    success: bool = Field(default=True, description="Whether the task was successful")
    error_message: str | None = Field(default=None, description="Error message if failed")


class Entity(BaseModel):
    """
    Represents an extracted entity.
    
    Common use case for NER (Named Entity Recognition) tasks.
    """
    name: str = Field(description="The entity text")
    entity_type: str = Field(description="Type of entity (person, org, location, etc.)")
    start_index: int | None = Field(default=None, description="Start position in source text")
    end_index: int | None = Field(default=None, description="End position in source text")


class Classification(BaseModel):
    """
    Represents a classification result.
    
    Use for text classification, sentiment analysis, etc.
    """
    label: str = Field(description="Classification label")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    reasoning: str | None = Field(default=None, description="Explanation for classification")


class Summary(BaseModel):
    """
    Represents a text summary.
    
    Use for summarization tasks.
    """
    summary: str = Field(description="The summarized text")
    key_points: list[str] = Field(default_factory=list, description="Key points extracted")
    word_count: int | None = Field(default=None, description="Word count of summary")
