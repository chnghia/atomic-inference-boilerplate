# Atomic Inference Boilerplate (The JIL Stack)

A production-ready boilerplate for building **AI Atomic Inference** using the **JIL Stack** (**J**inja2, **I**nstructor, **L**iteLLM).

## Philosophy

> Complex reasoning should be broken down into "Atomic Units"—single, focused inference steps consisting of a specific Prompt and a specific Output Schema.

This framework acts as the **"Engine"** (deciding *how to think*), not the **"Orchestrator"** (deciding *what to do next*). It's designed to be the robust Execution Layer inside LangGraph nodes or LangChain workflows.

## Key Features

- ✅ **Atomic Design**: Single, focused inference steps with validated outputs
- ✅ **Structured First**: Type-safe Pydantic outputs, never raw strings
- ✅ **Separation of Concerns**: Jinja2 for prompts, Python for logic
- ✅ **Multi-Provider Support**: OpenAI, Anthropic, Ollama, LM Studio via LiteLLM

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd atomic-inference-boilerplate

# 2. Install dependencies
conda activate docintel  # or your environment
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run example
python examples/basic.py
```

## Project Structure

```
src/
├── core/           # Core framework
│   ├── types.py    # Shared type definitions
│   ├── renderer.py # Jinja2 template engine
│   ├── client.py   # LiteLLM + Instructor
│   └── unit.py     # AtomicUnit class
├── modules/        # Shared utilities
│   ├── utils.py
│   └── vector_store.py
├── prompts/        # Jinja2 templates
└── schemas/        # Pydantic schemas
```

## Usage

```python
from src.core import AtomicUnit
from pydantic import BaseModel

class ExtractedEntity(BaseModel):
    name: str
    entity_type: str

# Create atomic unit
extractor = AtomicUnit(
    template_name="extraction.j2",
    output_schema=ExtractedEntity,
    model="gpt-4o-mini"
)

# Run inference
result = extractor.run({"text": "Apple Inc. is a technology company."})
print(result)  # ExtractedEntity(name='Apple Inc.', entity_type='company')
```

## Documentation

See [docs/specs/](docs/specs/) for detailed specifications.
