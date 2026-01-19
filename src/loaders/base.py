"""
Base Document Loader Interface.

Provides abstract base class for all document loaders and
common data structures for document representation.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    """
    Raw document representation after loading.
    
    Contains the raw text content and basic metadata
    before LLM-based extraction.
    """
    # Source information
    file_path: str = Field(description="Original file path")
    file_name: str = Field(description="File name without path")
    file_type: str = Field(description="File extension (pdf, docx, html, md)")
    file_size: int = Field(description="File size in bytes")
    
    # Content
    content: str = Field(description="Extracted text content")
    
    # Basic metadata (from file, not LLM)
    page_count: int | None = Field(default=None, description="Number of pages (if applicable)")
    word_count: int = Field(description="Approximate word count")
    
    # Raw structure hints (format-specific)
    raw_sections: list[dict] = Field(
        default_factory=list,
        description="Raw section markers found in document"
    )
    
    # Timestamps
    loaded_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def char_count(self) -> int:
        return len(self.content)


class DocumentLoader(ABC):
    """
    Abstract base class for document loaders.
    
    Each loader handles a specific document format and
    extracts raw text content for further processing.
    
    Example:
        loader = PDFLoader()
        doc = loader.load(Path("document.pdf"))
        print(doc.content)
    """
    
    # Supported file extensions for this loader
    supported_extensions: list[str] = []
    
    @abstractmethod
    def load(self, path: Path) -> RawDocument:
        """
        Load a document from the given path.
        
        Args:
            path: Path to the document file
            
        Returns:
            RawDocument with extracted content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type not supported
        """
        pass
    
    def can_load(self, path: Path) -> bool:
        """Check if this loader can handle the given file."""
        return path.suffix.lower().lstrip('.') in self.supported_extensions
    
    def _validate_path(self, path: Path) -> Path:
        """Validate and normalize the file path."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {path}")
        
        if not self.can_load(path):
            raise ValueError(
                f"Unsupported file type: {path.suffix}. "
                f"Supported: {self.supported_extensions}"
            )
        
        return path
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def _extract_sections_from_headings(
        self,
        content: str,
        heading_pattern: str = r'^#+\s+(.+)$'
    ) -> list[dict]:
        """
        Extract section markers from heading patterns.
        
        Default pattern matches Markdown headings.
        """
        import re
        
        sections = []
        for match in re.finditer(heading_pattern, content, re.MULTILINE):
            sections.append({
                "title": match.group(1).strip(),
                "position": match.start(),
                "level": len(match.group(0)) - len(match.group(1)) - 1,
            })
        
        return sections
