# EPIC: Document Extraction Pipelines with Prefect

## Document Information

| Field | Value |
|-------|-------|
| **EPIC ID** | EPIC-DAAG-003 |
| **Version** | 1.0.0 |
| **Status** | Draft |
| **Created Date** | 2026-01-19 |
| **Last Updated** | 2026-01-19 |
| **Author(s)** | NghiaCH |
| **Reviewer(s)** | - |
| **Approver** | - |

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-01-19 | NghiaCH | Initial EPIC specification |

---

## 1. Executive Summary

### 1.1 Problem Statement

Projects like **DocIntel** require processing diverse document formats (PDF, DOCX, HTML, Markdown) to:
- Extract structured metadata (title, author, date, keywords)
- Discover document structure (headings, sections, tables)
- Chunk content intelligently for vector embedding
- Build knowledge databases with rich, queryable data

Current approaches mix extraction logic with LLM calls, making pipelines:
- **Hard to test**: LLM calls interleaved with parsing logic
- **Hard to scale**: No clear separation between orchestration and inference
- **Hard to maintain**: Format-specific logic scattered across codebase

### 1.2 Solution Vision

Create example extraction pipelines demonstrating:

1. **AtomicUnit as Extraction Engine**: Each extraction step uses AtomicUnit for structured LLM output
2. **Prefect as Workflow Orchestrator**: Prefect flows manage pipeline steps, retries, and parallel processing
3. **Format-Agnostic Architecture**: Unified interface for different document types

```
┌──────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                         │
│                     (Prefect Flows)                          │
│  ┌─────────────────────────────────────────────────────┐     │
│  │                Document Pipeline                    │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────┐   │     │
│  │  │  Load   │→ │ Extract │→ │Structure│→ │ Chunk │   │     │
│  │  │Document │  │Metadata │  │Discovery│  │Content│   │     │
│  │  └─────────┘  └────┬────┘  └────┬────┘  └───┬───┘   │     │
│  └────────────────────│────────────│───────────│───────┘     │
└───────────────────────│────────────│───────────│─────────────┘
                        │            │           │
┌───────────────────────▼────────────▼───────────▼────────────┐
│                    EXECUTION LAYER                          │
│                  (Atomic Inference)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ AtomicUnit  │  │ AtomicUnit  │  │ AtomicUnit  │          │
│  │(metadata.j2)│  │(structure.j2)│ │ (chunk.j2)  │          │
│  │→Metadata    │  │→DocStructure│  │→ChunkList   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Expected Outcome

- Reusable patterns for document processing pipelines
- Clear examples of Prefect + AtomicUnit integration
- Schemas for common extraction tasks (metadata, structure, chunking)

---

## 2. Goals & Non-Goals

### 2.1 Goals

* **Metadata Extraction**: Extract title, author, date, language, keywords from any document
* **Structure Discovery**: Identify headings, sections, tables, lists hierarchy
* **Intelligent Chunking**: Split content semantically (by section, paragraph, or custom logic)
* **Prefect Integration**: Demonstrate flow-based orchestration with tasks, retries, parallel execution
* **Format Handlers**: Support PDF (text-based), DOCX, HTML, Markdown

### 2.2 Non-Goals

* **OCR/Image Processing**: No image-based PDF support (text extraction only)
* **Production RAG Pipeline**: Focus on extraction, not embedding/retrieval
* **Complex Document Types**: No support for spreadsheets, presentations initially

---

## 3. Feature Specifications

### 3.1 Document Loaders

**Directory**: `src/loaders/`

| Loader | Format | Method |
|--------|--------|--------|
| `pdf_loader.py` | PDF | PyMuPDF/pdfplumber text extraction |
| `docx_loader.py` | DOCX | python-docx |
| `html_loader.py` | HTML | BeautifulSoup |
| `markdown_loader.py` | Markdown | markdown-it |

**Common Interface**:
```python
class DocumentLoader(ABC):
    def load(self, path: Path) -> RawDocument:
        """Load document and return raw content"""
        pass
```

---

### 3.2 Extraction Schemas

**File**: `src/schemas/documents.py`

```python
class DocumentMetadata(BaseModel):
    """Extracted metadata from any document"""
    title: str
    author: str | None
    created_date: str | None
    language: str
    keywords: list[str]
    summary: str  # LLM-generated summary

class DocumentSection(BaseModel):
    """A section in document structure"""
    level: int  # Heading level (1-6)
    title: str
    content: str
    subsections: list["DocumentSection"]

class DocumentStructure(BaseModel):
    """Full document structure"""
    sections: list[DocumentSection]
    tables: list[dict]  # Extracted tables
    has_toc: bool

class ContentChunk(BaseModel):
    """A chunk for embedding"""
    content: str
    chunk_type: Literal["section", "paragraph", "table"]
    metadata: dict  # Section title, page number, etc.
    token_count: int
```

---

### 3.3 Extraction Prompts

**Directory**: `src/prompts/extraction/`

| Prompt | Purpose | Output Schema |
|--------|---------|---------------|
| `metadata.j2` | Extract document metadata | `DocumentMetadata` |
| `structure.j2` | Discover document structure | `DocumentStructure` |
| `chunk_strategy.j2` | Decide chunking strategy | `ChunkingDecision` |
| `chunk_content.j2` | Create semantic chunks | `list[ContentChunk]` |

---

### 3.4 Prefect Flows

**Directory**: `examples/prefect_pipelines/`

#### Flow 1: Single Document Pipeline
**File**: `document_pipeline.py`

```python
@flow(name="document-extraction")
def extract_document(file_path: str) -> ExtractedDocument:
    """Complete extraction pipeline for a single document"""
    
    # Task 1: Load document
    raw_doc = load_document(file_path)
    
    # Task 2: Extract metadata (uses AtomicUnit)
    metadata = extract_metadata(raw_doc)
    
    # Task 3: Discover structure (uses AtomicUnit)
    structure = discover_structure(raw_doc)
    
    # Task 4: Create chunks (uses AtomicUnit)
    chunks = create_chunks(raw_doc, structure)
    
    return ExtractedDocument(
        metadata=metadata,
        structure=structure,
        chunks=chunks
    )
```

#### Flow 2: Batch Processing Pipeline
**File**: `batch_pipeline.py`

```python
@flow(name="batch-extraction")
def extract_batch(directory: str) -> list[ExtractedDocument]:
    """Process multiple documents in parallel"""
    
    files = list_documents(directory)
    
    # Parallel extraction with Prefect
    results = extract_document.map(files)
    
    return results
```

#### Flow 3: Incremental Pipeline
**File**: `incremental_pipeline.py`

```python
@flow(name="incremental-extraction")
def extract_incremental(directory: str, state_file: str):
    """Only process new/modified documents"""
    
    # Load processing state
    state = load_state(state_file)
    
    # Find new/modified files
    new_files = find_new_files(directory, state)
    
    # Process only new files
    for file in new_files:
        result = extract_document(file)
        save_result(result)
        update_state(state, file)
```

---

### 3.5 Directory Structure

```
src/
├── loaders/
│   ├── __init__.py
│   ├── base.py           # ABC for loaders
│   ├── pdf_loader.py
│   ├── docx_loader.py
│   ├── html_loader.py
│   └── markdown_loader.py
├── schemas/
│   └── documents.py      # Extraction schemas
└── prompts/
    └── extraction/
        ├── metadata.j2
        ├── structure.j2
        ├── chunk_strategy.j2
        └── chunk_content.j2

examples/
└── prefect_pipelines/
    ├── __init__.py
    ├── document_pipeline.py    # Single doc
    ├── batch_pipeline.py       # Batch processing
    └── incremental_pipeline.py # Incremental
```

---

## 4. Technical Implementation Plan

### Task 1: Dependencies & Setup
- Add `prefect`, `pymupdf`, `python-docx`, `beautifulsoup4` to dependencies
- Create directory structure

### Task 2: Document Loaders
- Implement base loader interface
- Create PDF, DOCX, HTML, Markdown loaders

### Task 3: Extraction Schemas & Prompts
- Create `documents.py` with all schemas
- Create extraction prompts

### Task 4: Prefect Pipelines
- Implement single document pipeline
- Implement batch processing pipeline
- (Optional) Implement incremental pipeline

### Task 5: Documentation
- Update README
- Create usage examples

---

## 5. Success Metrics

| Metric | Criteria |
|--------|----------|
| **Extraction Quality** | Metadata fields correctly populated for sample docs |
| **Layer Separation** | No LLM calls outside AtomicUnit in pipelines |
| **Scalability** | Batch pipeline processes 10+ docs in parallel |
| **Reusability** | Adding new format requires only new loader |

---

## 6. Dependencies

```toml
# Add to pyproject.toml & requirements.txt
prefect = "^3.0"
pymupdf = "^1.24"       # PDF extraction
python-docx = "^1.1"    # DOCX extraction
beautifulsoup4 = "^4.12" # HTML parsing
markdown-it-py = "^3.0"  # Markdown parsing
```

---

## 7. References

- [Prefect Documentation](https://docs.prefect.io/)
- [DocIntel Project](internal reference)
- [Unstructured.io](https://unstructured.io/) - Inspiration for document processing
