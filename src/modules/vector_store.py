"""
Vector Store Interface for Atomic Inference.

This module provides the abstract base class for vector stores,
enabling integration with various RAG backends.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.core.types import MemoryChunk


class VectorStoreBase(ABC):
    """
    Abstract base class for vector store implementations.
    
    Provides a standard interface for:
    - Adding documents to the store
    - Searching for relevant documents
    - Managing document lifecycle
    
    Example implementation:
        class ChromaVectorStore(VectorStoreBase):
            def __init__(self, collection_name: str):
                self.collection = chromadb.get_or_create_collection(collection_name)
                
            def add(self, content: str, metadata: dict | None = None) -> str:
                doc_id = str(uuid4())
                self.collection.add(documents=[content], ids=[doc_id], metadatas=[metadata])
                return doc_id
                
            def search(self, query: str, top_k: int = 5) -> list[MemoryChunk]:
                results = self.collection.query(query_texts=[query], n_results=top_k)
                return [MemoryChunk(content=doc) for doc in results["documents"][0]]
    """
    
    @abstractmethod
    def add(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """
        Add a document to the vector store.
        
        Args:
            content: Text content to embed and store
            metadata: Optional metadata dict
            
        Returns:
            Document ID for future reference
        """
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[MemoryChunk]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            
        Returns:
            List of MemoryChunk objects sorted by relevance
        """
        pass
    
    def add_many(self, documents: list[tuple[str, dict | None]]) -> list[str]:
        """
        Add multiple documents to the store.
        
        Args:
            documents: List of (content, metadata) tuples
            
        Returns:
            List of document IDs
        """
        return [self.add(content, metadata) for content, metadata in documents]
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document from the store.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        raise NotImplementedError("Delete not implemented for this store")
    
    def clear(self) -> None:
        """Clear all documents from the store."""
        raise NotImplementedError("Clear not implemented for this store")


class InMemoryVectorStore(VectorStoreBase):
    """
    Simple in-memory vector store for testing and development.
    
    Uses basic string matching (not actual embeddings).
    For production, use a proper vector DB like Chroma, Pinecone, etc.
    """
    
    def __init__(self):
        self._documents: dict[str, tuple[str, dict | None]] = {}
        self._counter = 0
    
    def add(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Add document with auto-generated ID."""
        self._counter += 1
        doc_id = f"doc_{self._counter}"
        self._documents[doc_id] = (content, metadata)
        return doc_id
    
    def search(self, query: str, top_k: int = 5) -> list[MemoryChunk]:
        """Search using simple substring matching (for testing only)."""
        query_lower = query.lower()
        results = []
        
        for doc_id, (content, metadata) in self._documents.items():
            # Simple relevance: count query words in content
            score = sum(1 for word in query_lower.split() if word in content.lower())
            if score > 0:
                results.append((score, content, metadata))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [
            MemoryChunk(
                content=content,
                score=score / len(query.split()),
                metadata=metadata,
            )
            for score, content, metadata in results[:top_k]
        ]
    
    def delete(self, doc_id: str) -> bool:
        """Delete document by ID."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._counter = 0
