"""
Document Extraction Pipeline with Prefect.

Demonstrates:
- Prefect as ORCHESTRATION LAYER (flow control, retries, parallel)
- AtomicUnit as EXECUTION LAYER (structured LLM calls)

Architecture:
    ┌────────────────────────────────────────────────────────────┐
    │                  ORCHESTRATION LAYER                       │
    │                     (Prefect Flow)                         │
    │  ┌──────────────────────────────────────────────────────┐  │
    │  │              Document Extraction Flow                 │  │
    │  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │  │
    │  │  │  Load   │→ │ Extract  │→ │ Discover │→ │ Chunk │  │  │
    │  │  │Document │  │ Metadata │  │Structure │  │Content│  │  │
    │  │  └─────────┘  └────┬─────┘  └────┬─────┘  └───┬───┘  │  │
    │  └────────────────────│────────────│────────────│───────┘  │
    └───────────────────────│────────────│────────────│──────────┘
                            │            │            │
    ┌───────────────────────▼────────────▼────────────▼──────────┐
    │                    EXECUTION LAYER                          │
    │                  (Atomic Inference)                         │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │  │ AtomicUnit  │  │ AtomicUnit  │  │ AtomicUnit  │          │
    │  │(metadata.j2)│  │(structure.j2)│ │ (chunk.j2)  │          │
    │  └─────────────┘  └─────────────┘  └─────────────┘          │
    └─────────────────────────────────────────────────────────────┘

Usage:
    conda activate atomic
    pip install prefect pymupdf python-docx beautifulsoup4 markdown-it-py
    python examples/prefect_pipelines/document_pipeline.py
"""

import sys
import time
import hashlib
from pathlib import Path
from typing import Literal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from prefect import flow, task
from prefect.logging import get_run_logger

# =============================================================================
# EXECUTION LAYER: Atomic Inference
# =============================================================================
from src.core import AtomicUnit
from src.loaders import PDFLoader, DOCXLoader, HTMLLoader, MarkdownLoader, RawDocument
from src.schemas.documents import (
    DocumentMetadata,
    DocumentStructure,
    ChunkingStrategy,
    ContentChunk,
    ExtractedDocument,
)


# Create AtomicUnits for each extraction step
metadata_unit = AtomicUnit(
    template_name="extraction/metadata.j2",
    output_schema=DocumentMetadata,
    model="openai/qwen3-coder-30b",  # Change to your model
    temperature=0.3,
    max_tokens=12800
)

structure_unit = AtomicUnit(
    template_name="extraction/structure.j2",
    output_schema=DocumentStructure,
    model="openai/qwen3-coder-30b",
    temperature=0.3,
    max_tokens=12800
)

chunking_unit = AtomicUnit(
    template_name="extraction/chunk_strategy.j2",
    output_schema=ChunkingStrategy,
    model="openai/qwen3-coder-30b",
    temperature=0.3,
    max_tokens=12800
)


# =============================================================================
# Document Loader Registry
# =============================================================================

LOADERS = {
    "pdf": PDFLoader(),
    "docx": DOCXLoader(),
    "html": HTMLLoader(),
    "htm": HTMLLoader(),
    "md": MarkdownLoader(),
    "markdown": MarkdownLoader(),
}


def get_loader(file_type: str):
    """Get appropriate loader for file type."""
    loader = LOADERS.get(file_type.lower())
    if loader is None:
        raise ValueError(f"No loader for file type: {file_type}")
    return loader


# =============================================================================
# ORCHESTRATION LAYER: Prefect Tasks
# Each task is a step, but LLM calls go through AtomicUnit
# =============================================================================

@task(name="load-document", retries=2)
def load_document(file_path: str) -> RawDocument:
    """
    Task 1: Load document from file.
    
    Pure Python task - no LLM calls.
    """
    logger = get_run_logger()
    
    path = Path(file_path)
    file_type = path.suffix.lower().lstrip('.')
    
    logger.info(f"Loading {path.name} (type: {file_type})")
    
    loader = get_loader(file_type)
    doc = loader.load(path)
    
    logger.info(f"Loaded: {doc.word_count} words, {len(doc.raw_sections)} sections detected")
    
    return doc


@task(name="extract-metadata")
def extract_metadata(doc: RawDocument) -> DocumentMetadata:
    """
    Task 2: Extract document metadata.
    
    Uses AtomicUnit (Execution Layer) for LLM call.
    """
    logger = get_run_logger()
    logger.info("Extracting metadata via AtomicUnit...")
    
    # Call Execution Layer
    metadata = metadata_unit.run({
        "content": doc.content,
        "raw_sections": doc.raw_sections,
    })
    
    logger.info(f"Extracted: title='{metadata.title}', lang={metadata.language}")
    
    return metadata


@task(name="discover-structure")
def discover_structure(doc: RawDocument) -> DocumentStructure:
    """
    Task 3: Discover document structure.
    
    Uses AtomicUnit (Execution Layer) for LLM call.
    """
    logger = get_run_logger()
    logger.info("Discovering structure via AtomicUnit...")
    
    # Call Execution Layer
    structure = structure_unit.run({
        "content": doc.content,
        "raw_sections": doc.raw_sections,
    })
    
    logger.info(f"Found: {structure.total_sections} sections, {len(structure.tables)} tables")
    
    return structure


@task(name="decide-chunking-strategy")
def decide_chunking_strategy(
    doc: RawDocument,
    structure: DocumentStructure
) -> ChunkingStrategy:
    """
    Task 4: Decide chunking strategy.
    
    Uses AtomicUnit (Execution Layer) for LLM call.
    """
    logger = get_run_logger()
    logger.info("Deciding chunking strategy via AtomicUnit...")
    
    # Call Execution Layer
    strategy = chunking_unit.run({
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "word_count": doc.word_count,
        "char_count": doc.char_count,
        "structure": structure,
        "content": doc.content,
    })
    
    logger.info(f"Strategy: {strategy.strategy}, chunk_size={strategy.target_chunk_size}")
    
    return strategy


@task(name="create-chunks")
def create_chunks(
    doc: RawDocument,
    structure: DocumentStructure,
    strategy: ChunkingStrategy
) -> list[ContentChunk]:
    """
    Task 5: Create content chunks.
    
    Uses simple Python logic for chunking (no LLM needed for basic chunking).
    For production, could use AtomicUnit for semantic chunking.
    """
    logger = get_run_logger()
    logger.info(f"Creating chunks with strategy: {strategy.strategy}")
    
    chunks = []
    content = doc.content
    chunk_size = strategy.target_chunk_size * 4  # ~4 chars per token
    overlap = strategy.overlap * 4
    
    if strategy.strategy == "by_section" and structure.sections:
        # Chunk by sections
        for i, section in enumerate(structure.sections):
            chunk_id = f"{doc.file_name}_{i}"
            chunks.append(ContentChunk(
                chunk_id=chunk_id,
                content=section.content[:chunk_size] if section.content else section.title,
                chunk_type="section",
                chunk_index=i,
                section_title=section.title,
                word_count=len((section.content or section.title).split()),
                token_count=len((section.content or section.title).split()) // 4,
            ))
    else:
        # Simple fixed-size chunking
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            
            # Try to break at sentence boundary
            if end < len(content):
                last_period = chunk_text.rfind('.')
                if last_period > chunk_size // 2:
                    chunk_text = chunk_text[:last_period + 1]
                    end = start + last_period + 1
            
            chunk_id = hashlib.md5(f"{doc.file_name}_{chunk_index}".encode()).hexdigest()[:8]
            
            chunks.append(ContentChunk(
                chunk_id=chunk_id,
                content=chunk_text.strip(),
                chunk_type="paragraph",
                chunk_index=chunk_index,
                start_position=start,
                end_position=end,
                word_count=len(chunk_text.split()),
                token_count=len(chunk_text.split()) // 4,
            ))
            
            chunk_index += 1
            start = end - overlap
    
    logger.info(f"Created {len(chunks)} chunks")
    
    return chunks


# =============================================================================
# Main Flow
# =============================================================================

@flow(name="document-extraction-pipeline")
def extract_document(file_path: str) -> ExtractedDocument:
    """
    Complete document extraction pipeline.
    
    Orchestrates: Load → ExtractMetadata → DiscoverStructure → Chunk
    """
    logger = get_run_logger()
    start_time = time.time()
    
    logger.info(f"Starting extraction: {file_path}")
    
    # Task 1: Load document (pure Python)
    doc = load_document(file_path)
    
    # Task 2: Extract metadata (AtomicUnit)
    metadata = extract_metadata(doc)
    
    # Task 3: Discover structure (AtomicUnit)
    structure = discover_structure(doc)
    
    # Task 4: Decide chunking (AtomicUnit)
    strategy = decide_chunking_strategy(doc, structure)
    
    # Task 5: Create chunks (Python logic)
    chunks = create_chunks(doc, structure, strategy)
    
    # Calculate stats
    processing_time_ms = int((time.time() - start_time) * 1000)
    total_tokens = sum(c.token_count for c in chunks)
    
    result = ExtractedDocument(
        file_path=doc.file_path,
        file_name=doc.file_name,
        file_type=doc.file_type,
        metadata=metadata,
        structure=structure,
        chunks=chunks,
        chunk_count=len(chunks),
        total_tokens=total_tokens,
        processing_time_ms=processing_time_ms,
    )
    
    logger.info(f"Extraction complete: {len(chunks)} chunks, {processing_time_ms}ms")
    
    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run the pipeline on a sample file."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract document to structured data")
    parser.add_argument("file", help="Path to document file")
    parser.add_argument("--output", "-o", help="Output JSON file")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📄 Document Extraction Pipeline (Prefect + AtomicUnit)")
    print("   Orchestration Layer: Prefect")
    print("   Execution Layer: Atomic Inference")
    print("=" * 60)
    
    # Run the flow
    result = extract_document(args.file)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 EXTRACTION RESULT:")
    print("=" * 60)
    print(f"Title: {result.metadata.title}")
    print(f"Language: {result.metadata.language}")
    print(f"Keywords: {', '.join(result.metadata.keywords)}")
    print(f"Summary: {result.metadata.summary[:200]}...")
    print(f"\nStructure: {result.structure.total_sections} sections")
    print(f"Chunks: {result.chunk_count}")
    print(f"Total Tokens: ~{result.total_tokens}")
    print(f"Processing Time: {result.processing_time_ms}ms")
    
    # Save if output specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
