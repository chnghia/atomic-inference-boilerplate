"""
Document Extraction Schemas.

Pydantic models for structured document data:
- DocumentMetadata: Title, author, keywords, summary
- DocumentStructure: Sections, tables hierarchy
- ContentChunk: Chunks for vector embedding
"""

from typing import Literal, Any
from pydantic import BaseModel, Field


# =============================================================================
# Metadata Extraction
# =============================================================================

class DocumentMetadata(BaseModel):
    """
    Extracted metadata from any document.
    
    LLM-extracted fields like title, summary, keywords.
    """
    title: str = Field(description="Document title")
    author: str | None = Field(default=None, description="Author name if found")
    created_date: str | None = Field(default=None, description="Creation/publication date")
    language: str = Field(default="en", description="Primary language (ISO code)")
    keywords: list[str] = Field(
        default_factory=list,
        description="Key topics/keywords"
    )
    summary: str = Field(description="Brief summary of document content")
    document_type: str = Field(
        default="unknown",
        description="Type: article, report, manual, email, etc."
    )


# =============================================================================
# Structure Discovery
# =============================================================================

class DocumentSection(BaseModel):
    """A section in the document hierarchy."""
    level: int = Field(ge=1, le=6, description="Heading level (1-6)")
    title: str = Field(description="Section title")
    content: str = Field(default="", description="Section content (may be empty for parent sections)")
    start_position: int = Field(default=0, description="Character position in original doc")
    subsections: list["DocumentSection"] = Field(
        default_factory=list,
        description="Nested subsections"
    )


class TableData(BaseModel):
    """Extracted table information."""
    title: str | None = Field(default=None, description="Table caption if present")
    headers: list[str] = Field(default_factory=list, description="Column headers")
    rows: list[list[str]] = Field(default_factory=list, description="Row data")
    position: int = Field(default=0, description="Position in document")


class DocumentStructure(BaseModel):
    """
    Full document structure analysis.
    
    Hierarchical representation of document organization.
    """
    sections: list[DocumentSection] = Field(
        default_factory=list,
        description="Top-level sections"
    )
    tables: list[TableData] = Field(
        default_factory=list,
        description="Tables found in document"
    )
    has_toc: bool = Field(
        default=False,
        description="Whether document has table of contents"
    )
    total_sections: int = Field(default=0, description="Total section count")


# =============================================================================
# Chunking
# =============================================================================

class ChunkingStrategy(BaseModel):
    """
    Decision on how to chunk this document.
    
    LLM analyzes document and recommends chunking approach.
    """
    strategy: Literal["by_section", "by_paragraph", "by_tokens", "hybrid"] = Field(
        description="Recommended chunking strategy"
    )
    target_chunk_size: int = Field(
        default=500,
        description="Target tokens per chunk"
    )
    overlap: int = Field(
        default=50,
        description="Token overlap between chunks"
    )
    reasoning: str = Field(
        description="Why this strategy was chosen"
    )


class ContentChunk(BaseModel):
    """
    A content chunk ready for embedding.
    
    Contains text and metadata for vector storage.
    """
    chunk_id: str = Field(description="Unique chunk identifier")
    content: str = Field(description="Chunk text content")
    chunk_type: Literal["section", "paragraph", "table", "mixed"] = Field(
        description="Type of content in this chunk"
    )
    
    # Positioning
    chunk_index: int = Field(description="Order in document")
    start_position: int = Field(default=0, description="Start char position")
    end_position: int = Field(default=0, description="End char position")
    
    # Metadata for retrieval
    section_title: str | None = Field(default=None, description="Parent section title")
    page_number: int | None = Field(default=None, description="Page number if applicable")
    
    # Stats
    token_count: int = Field(default=0, description="Approximate token count")
    word_count: int = Field(default=0, description="Word count")
    
    # Custom metadata
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


# =============================================================================
# Pipeline Output
# =============================================================================

class ExtractedDocument(BaseModel):
    """
    Complete extraction output for a document.
    
    Combines all extraction stages.
    """
    # Source info
    file_path: str
    file_name: str
    file_type: str
    
    # Extraction results
    metadata: DocumentMetadata
    structure: DocumentStructure
    chunks: list[ContentChunk]
    
    # Processing info
    chunk_count: int = Field(default=0)
    total_tokens: int = Field(default=0)
    processing_time_ms: int = Field(default=0)
