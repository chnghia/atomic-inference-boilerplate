"""
Basic Example - Hello World Entity Extraction.

Demonstrates:
- Basic AtomicUnit usage
- Pydantic schema definition
- Model switching (change 1 string)

Usage:
    conda activate atomic
    python examples/basic.py
"""

from pydantic import BaseModel, Field

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import AtomicUnit


# Define output schema
class ExtractedEntities(BaseModel):
    """Schema for entity extraction output."""
    entities: list[dict] = Field(
        description="List of extracted entities with 'name' and 'type' keys"
    )
    count: int = Field(description="Total number of entities found")


def main():
    """Run basic entity extraction example."""
    
    # Create an AtomicUnit for entity extraction
    extractor = AtomicUnit(
        template_name="extraction.j2",
        output_schema=ExtractedEntities,
        # MODEL SWITCHING: Change this string to switch providers
        # Examples:
        #   - "gpt-4o-mini" (OpenAI)
        #   - "claude-3-haiku-20240307" (Anthropic)
        #   - "ollama/llama3" (Local Ollama)
        #   - "openai/your-model-name" (LM Studio via OpenAI-compatible API)
        #       ↳ Requires OPENAI_API_BASE in .env pointing to LM Studio
        model="openai/qwen3-coder-30b",  # LM Studio: use "openai/" prefix
        temperature=0.3,
    )
    
    # Sample text for extraction
    sample_text = """
    Apple Inc., headquartered in Cupertino, California, announced that 
    Tim Cook will present the new iPhone 15 at the Steve Jobs Theater 
    in September 2024. The company's stock traded at $185 on NASDAQ.
    """
    
    # Preview the prompt (useful for debugging)
    print("=" * 60)
    print("PROMPT PREVIEW:")
    print("=" * 60)
    prompt = extractor.preview_prompt({
        "text": sample_text,
        "entity_types": ["organization", "person", "location", "product", "date"]
    })
    print(prompt)
    print()
    
    # Run the extraction
    print("=" * 60)
    print("RUNNING EXTRACTION...")
    print("=" * 60)
    
    result = extractor.run({
        "text": sample_text,
        "entity_types": ["organization", "person", "location", "product", "date"]
    })
    
    # Result is a validated Pydantic object, NOT raw string/dict
    print(f"\nResult Type: {type(result).__name__}")
    print(f"Entity Count: {result.count}")
    print("\nExtracted Entities:")
    for entity in result.entities:
        print(f"  - {entity.get('name', 'N/A')} ({entity.get('type', 'unknown')})")
    
    # Demonstrate that result is a proper Pydantic model
    print("\n" + "=" * 60)
    print("PYDANTIC MODEL FEATURES:")
    print("=" * 60)
    print(f"JSON: {result.model_dump_json(indent=2)}")


if __name__ == "__main__":
    main()
