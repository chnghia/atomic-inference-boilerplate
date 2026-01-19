"""
Batch Document Extraction Pipeline with Prefect.

Demonstrates:
- Parallel processing multiple documents
- Prefect's .map() for concurrent task execution
- Progress tracking across batch

Usage:
    python examples/prefect_pipelines/batch_pipeline.py /path/to/docs/
"""

import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from prefect import flow, task
from prefect.logging import get_run_logger

from examples.prefect_pipelines.document_pipeline import (
    extract_document,
    LOADERS,
)
from src.schemas.documents import ExtractedDocument


# =============================================================================
# Batch Processing Tasks
# =============================================================================

@task(name="list-documents")
def list_documents(directory: str, extensions: List[str] | None = None) -> List[str]:
    """
    List all processable documents in a directory.
    """
    logger = get_run_logger()
    
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    # Default to all supported extensions
    if extensions is None:
        extensions = list(LOADERS.keys())
    
    files = []
    for ext in extensions:
        files.extend(dir_path.glob(f"**/*.{ext}"))
    
    file_paths = [str(f) for f in files]
    
    logger.info(f"Found {len(file_paths)} documents in {directory}")
    
    return file_paths


@task(name="save-results")
def save_results(results: List[ExtractedDocument], output_dir: str) -> None:
    """
    Save extraction results to JSON files.
    """
    logger = get_run_logger()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        if result:  # Skip failed extractions
            output_file = output_path / f"{Path(result.file_name).stem}.json"
            with open(output_file, 'w') as f:
                f.write(result.model_dump_json(indent=2))
    
    logger.info(f"Saved {len(results)} results to {output_dir}")


@task(name="summarize-batch")
def summarize_batch(results: List[ExtractedDocument]) -> dict:
    """
    Generate summary statistics for batch processing.
    """
    successful = [r for r in results if r is not None]
    
    return {
        "total_files": len(results),
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "total_chunks": sum(r.chunk_count for r in successful),
        "total_tokens": sum(r.total_tokens for r in successful),
        "avg_processing_time_ms": (
            sum(r.processing_time_ms for r in successful) / len(successful)
            if successful else 0
        ),
        "file_types": list(set(r.file_type for r in successful)),
    }


# =============================================================================
# Batch Flow
# =============================================================================

@flow(name="batch-document-extraction")
def extract_batch(
    directory: str,
    output_dir: str | None = None,
    extensions: List[str] | None = None,
) -> dict:
    """
    Process multiple documents in parallel.
    
    Args:
        directory: Path to directory containing documents
        output_dir: Optional path to save JSON results
        extensions: Optional list of file extensions to process
        
    Returns:
        Summary statistics
    """
    logger = get_run_logger()
    
    logger.info(f"Starting batch extraction: {directory}")
    
    # Step 1: List documents
    files = list_documents(directory, extensions)
    
    if not files:
        logger.warning("No documents found!")
        return {"total_files": 0}
    
    # Step 2: Extract each document (parallel via .map())
    # Prefect automatically runs these concurrently
    results = extract_document.map(files)
    
    # Collect results (wait for all to complete)
    extracted_docs = [r.result() for r in results]
    
    # Step 3: Save results if output_dir specified
    if output_dir:
        save_results(extracted_docs, output_dir)
    
    # Step 4: Generate summary
    summary = summarize_batch(extracted_docs)
    
    logger.info(f"Batch complete: {summary['successful']}/{summary['total_files']} successful")
    
    return summary


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run batch pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch extract documents")
    parser.add_argument("directory", help="Directory containing documents")
    parser.add_argument("--output", "-o", help="Output directory for JSON results")
    parser.add_argument(
        "--extensions", "-e",
        nargs="+",
        help="File extensions to process (default: all supported)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📚 Batch Document Extraction Pipeline")
    print("   Orchestration: Prefect (parallel processing)")
    print("   Execution: Atomic Inference")
    print("=" * 60)
    
    # Run the flow
    summary = extract_batch(
        directory=args.directory,
        output_dir=args.output,
        extensions=args.extensions,
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 BATCH SUMMARY:")
    print("=" * 60)
    print(f"Total Files: {summary['total_files']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Total Chunks: {summary.get('total_chunks', 0)}")
    print(f"Total Tokens: ~{summary.get('total_tokens', 0)}")
    print(f"Avg Processing Time: {summary.get('avg_processing_time_ms', 0):.0f}ms")
    print(f"File Types: {', '.join(summary.get('file_types', []))}")


if __name__ == "__main__":
    main()
