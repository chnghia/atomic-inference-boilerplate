"""
HTML Document Loader.

Uses BeautifulSoup for parsing and extracting text from HTML files.
"""

from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from src.loaders.base import DocumentLoader, RawDocument


class HTMLLoader(DocumentLoader):
    """
    Loader for HTML documents.
    
    Extracts text content and preserves heading structure.
    Handles both local files and can be extended for URLs.
    
    Example:
        loader = HTMLLoader()
        doc = loader.load(Path("page.html"))
    """
    
    supported_extensions = ["html", "htm"]
    
    def load(self, path: Path) -> RawDocument:
        """Load and extract text from HTML."""
        if BeautifulSoup is None:
            raise ImportError(
                "BeautifulSoup not installed. Run: pip install beautifulsoup4"
            )
        
        path = self._validate_path(path)
        
        # Read HTML content
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Extract text
        content = soup.get_text(separator='\n', strip=True)
        
        # Extract headings for structure
        raw_sections = self._extract_headings(soup)
        
        # Get file stats
        file_stats = path.stat()
        
        return RawDocument(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_type="html",
            file_size=file_stats.st_size,
            content=content,
            page_count=None,
            word_count=self._count_words(content),
            raw_sections=raw_sections,
        )
    
    def _extract_headings(self, soup) -> list[dict]:
        """Extract heading elements (h1-h6) as section markers."""
        sections = []
        position = 0
        
        # Find all heading tags
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text(strip=True)
            if text:
                level = int(tag.name[1])  # h1 -> 1, h2 -> 2, etc.
                sections.append({
                    "title": text,
                    "position": position,
                    "level": level,
                })
                position += 1  # Just for ordering
        
        return sections
