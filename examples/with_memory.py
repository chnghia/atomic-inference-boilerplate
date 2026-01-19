"""
Memory Example - RAG Context Injection.

Demonstrates:
- Dynamic memory injection (MemoryChunk)
- Optional context blocks in templates
- InMemoryVectorStore for testing

Usage:
    conda activate atomic
    python examples/with_memory.py
"""

from pydantic import BaseModel, Field

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import AtomicUnit, MemoryChunk
from src.modules.vector_store import InMemoryVectorStore


# Define output schema
class AnswerWithSources(BaseModel):
    """Schema for RAG-style Q&A output."""
    answer: str = Field(description="The answer to the question")
    sources_used: list[int] = Field(
        description="Indices of memory chunks used (1-indexed)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the answer"
    )


def main():
    """Run example with memory/RAG injection."""
    
    # Create a simple in-memory vector store
    store = InMemoryVectorStore()
    
    # Add some "documents" to the store
    store.add("Python was created by Guido van Rossum in 1991.", {"source": "wiki"})
    store.add("Python is an interpreted, high-level programming language.", {"source": "docs"})
    store.add("The Python Software Foundation manages the development of Python.", {"source": "wiki"})
    store.add("Ruby was created by Yukihiro Matsumoto in 1995.", {"source": "wiki"})
    store.add("JavaScript was created by Brendan Eich in 1995.", {"source": "wiki"})
    
    # Search for relevant documents
    query = "Who created Python and when?"
    search_results = store.search(query, top_k=3)
    
    print("=" * 60)
    print(f"QUERY: {query}")
    print("=" * 60)
    print("\nRetrieved memories:")
    for i, mem in enumerate(search_results, 1):
        print(f"  [{i}] {mem.content} (score: {mem.score:.2f})")
    
    # Create AtomicUnit with QA template
    qa_unit = AtomicUnit(
        template_name="qa_with_context.j2",  # We'll use inline template for this example
        output_schema=AnswerWithSources,
        model="gpt-4o-mini",
    )
    
    # For this example, use inline template since we haven't created qa_with_context.j2
    # In real usage, you would use a proper template file
    qa_template = """
Answer the following question based on the provided context.

## Question
{{ question }}

{% if memories %}
## Context (use these to answer)
{% for memory in memories %}
[{{ loop.index }}] {{ memory.content }}
{% endfor %}
{% endif %}

## Instructions
1. Answer the question based on the context
2. List which context items you used (by number)
3. Rate your confidence (0.0-1.0)
"""
    
    # Render and run
    print("\n" + "=" * 60)
    print("RUNNING QA WITH CONTEXT...")
    print("=" * 60)
    
    # Use render_string for inline template
    from src.core.renderer import TemplateRenderer
    renderer = TemplateRenderer()
    prompt = renderer.render_string(qa_template, {
        "question": query,
        "memories": search_results
    })
    
    print("\nGenerated Prompt:")
    print(prompt)
    
    # For actual LLM call, we'd use the AtomicUnit
    # Here we're demonstrating the memory injection pattern
    result = qa_unit.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_model=AnswerWithSources,
    )
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Answer: {result.answer}")
    print(f"Sources Used: {result.sources_used}")
    print(f"Confidence: {result.confidence:.2f}")


if __name__ == "__main__":
    main()
