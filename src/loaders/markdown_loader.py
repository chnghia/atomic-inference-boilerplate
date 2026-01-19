"""
Markdown Document Loader.

Uses markdown-it-py for parsing Markdown files.
"""

from pathlib import Path
import re

try:
    from markdown_it import MarkdownIt
except ImportError:
    MarkdownIt = None

from src.loaders.base import DocumentLoader, RawDocument


class MarkdownLoader(DocumentLoader):
    """
    Loader for Markdown documents.
    
    Preserves heading structure which is naturally defined in Markdown.
    
    Example:
        loader = MarkdownLoader()
        doc = loader.load(Path("README.md"))
    """
    
    supported_extensions = ["md", "markdown"]
    
    def load(self, path: Path) -> RawDocument:
        """Load and extract text from Markdown."""
        path = self._validate_path(path)
        
        # Read Markdown content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract headings using regex (more reliable than parsing)
        raw_sections = self._extract_markdown_headings(content)
        
        # Get file stats
        file_stats = path.stat()
        
        return RawDocument(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_type="md",
            file_size=file_stats.st_size,
            content=content,
            page_count=None,
            word_count=self._count_words(content),
            raw_sections=raw_sections,
        )
    
    def _extract_markdown_headings(self, content: str) -> list[dict]:
        """Extract Markdown headings (# Heading)."""
        sections = []
        
        # Match ATX-style headings: # Heading, ## Heading, etc.
        pattern = r'^(#{1,6})\s+(.+)$'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            hashes = match.group(1)
            title = match.group(2).strip()
            
            sections.append({
                "title": title,
                "position": match.start(),
                "level": len(hashes),
            })
        
        return sections
    
    def to_plain_text(self, content: str) -> str:
        """
        Convert Markdown to plain text (optional).
        
        Removes Markdown syntax for cleaner text extraction.
        """
        if MarkdownIt is None:
            # Fallback: simple regex cleanup
            text = content
            # Remove images
            text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
            # Remove links but keep text
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            # Remove emphasis markers
            text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)
            # Remove code blocks
            text = re.sub(r'```[\s\S]*?```', '', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            return text
        
        # Use markdown-it for proper parsing
        md = MarkdownIt()
        tokens = md.parse(content)
        
        # Extract text from inline tokens
        text_parts = []
        for token in tokens:
            if token.type == 'inline' and token.content:
                text_parts.append(token.content)
            elif token.type == 'fence':
                # Skip code blocks
                pass
        
        return '\n'.join(text_parts)
