"""
Common utilities for Atomic Inference.

This module contains shared helper functions used across the framework.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def ensure_dir(path: Path | str) -> Path:
    """Ensure a directory exists, create if not."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def hash_text(text: str) -> str:
    """Generate a short hash for text (useful for caching)."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def now_iso() -> str:
    """Get current datetime in ISO format."""
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + suffix


def load_env_or_default(key: str, default: str | None = None) -> str | None:
    """Load environment variable with optional default."""
    return os.getenv(key, default)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Useful for preparing text for vector embeddings.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at word boundary
        if end < len(text):
            last_space = chunk.rfind(" ")
            if last_space > chunk_size // 2:
                chunk = chunk[:last_space]
                end = start + last_space
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def format_memories_for_prompt(memories: list[dict]) -> str:
    """
    Format memory chunks for injection into prompts.
    
    Args:
        memories: List of memory dicts with 'content' and optional 'source'
        
    Returns:
        Formatted string for prompt injection
    """
    lines = []
    for i, mem in enumerate(memories, 1):
        content = mem.get("content", "")
        source = mem.get("source")
        if source:
            lines.append(f"[{i}] {content} (Source: {source})")
        else:
            lines.append(f"[{i}] {content}")
    
    return "\n".join(lines)
