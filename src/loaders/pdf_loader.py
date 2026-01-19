"""
PDF Document Loader.

Uses PyMuPDF (fitz) for text extraction from PDF files.
"""

from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from src.loaders.base import DocumentLoader, RawDocument


class PDFLoader(DocumentLoader):
    """
    Loader for PDF documents.
    
    Uses PyMuPDF for fast, accurate text extraction.
    Does NOT support OCR (image-based PDFs).
    
    Example:
        loader = PDFLoader()
        doc = loader.load(Path("report.pdf"))
    """
    
    supported_extensions = ["pdf"]
    
    def load(self, path: Path) -> RawDocument:
        """Load and extract text from PDF."""
        if fitz is None:
            raise ImportError(
                "PyMuPDF not installed. Run: pip install pymupdf"
            )
        
        path = self._validate_path(path)
        
        # Open PDF
        pdf = fitz.open(str(path))
        
        # Extract text from all pages
        pages_text = []
        for page_num, page in enumerate(pdf):
            text = page.get_text("text")
            pages_text.append(text)
        
        content = "\n\n".join(pages_text)
        
        # Extract section markers (look for heading-like patterns)
        raw_sections = self._extract_pdf_sections(pages_text)
        
        # Get file stats
        file_stats = path.stat()
        
        return RawDocument(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_type="pdf",
            file_size=file_stats.st_size,
            content=content,
            page_count=len(pdf),
            word_count=self._count_words(content),
            raw_sections=raw_sections,
        )
    
    def _extract_pdf_sections(self, pages_text: list[str]) -> list[dict]:
        """
        Extract potential section headings from PDF.
        
        Heuristics:
        - Short lines (< 100 chars) that are UPPERCASE or Title Case
        - Lines that start with numbers (1., 1.1, etc.)
        """
        import re
        
        sections = []
        position = 0
        
        for page_num, page_text in enumerate(pages_text):
            for line in page_text.split('\n'):
                line = line.strip()
                
                # Skip empty or very short lines
                if len(line) < 3:
                    position += len(line) + 1
                    continue
                
                # Check for heading patterns
                is_heading = False
                level = 1
                
                # Numbered sections: 1., 1.1., Chapter 1, etc.
                if re.match(r'^(\d+\.)+\s+\w+', line) or \
                   re.match(r'^(Chapter|Section|Part)\s+\d+', line, re.IGNORECASE):
                    is_heading = True
                    # Count dots for level
                    dots = line.count('.') 
                    level = min(dots, 3) if dots > 0 else 1
                
                # ALL CAPS heading (but not too long)
                elif line.isupper() and len(line) < 80:
                    is_heading = True
                    level = 1
                
                # Title Case and short (likely heading)
                elif line.istitle() and len(line) < 60 and not line.endswith('.'):
                    is_heading = True
                    level = 2
                
                if is_heading:
                    sections.append({
                        "title": line,
                        "position": position,
                        "level": level,
                        "page": page_num + 1,
                    })
                
                position += len(line) + 1
        
        return sections
