"""
Tests for AtomicUnit.

Run with: pytest tests/test_unit.py -v

Note: LLM integration tests require API keys in .env
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from src.core.unit import AtomicUnit
from src.core.types import MemoryChunk


# Test schemas
class SimpleOutput(BaseModel):
    """Simple test schema."""
    message: str
    count: int = 0


class EntityOutput(BaseModel):
    """Entity extraction test schema."""
    entities: list[str]
    count: int


class TestAtomicUnitInitialization:
    """Test AtomicUnit initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        assert unit.template_name == "extraction.j2"
        assert unit.output_schema == SimpleOutput
        assert unit.temperature == 0.7
        assert unit.max_tokens == 2048
        assert unit.max_retries == 3
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
            model="claude-3-haiku-20240307",
            temperature=0.5,
            max_tokens=1024,
            max_retries=5,
        )
        
        assert unit.model == "claude-3-haiku-20240307"
        assert unit.temperature == 0.5
        assert unit.max_tokens == 1024
        assert unit.max_retries == 5
    
    def test_init_with_system_template(self):
        """Test initialization with system template."""
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
            system_template="base/system.j2",
        )
        
        assert unit.system_template == "base/system.j2"


class TestAtomicUnitPreview:
    """Test AtomicUnit preview functionality."""
    
    def test_preview_prompt(self):
        """Test prompt preview without LLM call."""
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        prompt = unit.preview_prompt({
            "text": "Test text",
            "entity_types": ["person"]
        })
        
        assert "Test text" in prompt
        assert "person" in prompt
    
    def test_preview_with_memories(self):
        """Test prompt preview with memory injection."""
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        memories = [
            MemoryChunk(content="Memory 1", source="doc1"),
            MemoryChunk(content="Memory 2"),
        ]
        
        prompt = unit.preview_prompt(
            {"text": "Test"},
            memories=memories
        )
        
        assert "Memory 1" in prompt
        assert "Memory 2" in prompt


class TestAtomicUnitMocked:
    """Test AtomicUnit with mocked LLM calls."""
    
    @patch('src.core.unit.create_client')
    def test_run_returns_validated_output(self, mock_create_client):
        """Test that run() returns validated Pydantic object."""
        # Setup mock
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = SimpleOutput(
            message="Hello",
            count=42
        )
        
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        result = unit.run({"text": "Test"})
        
        assert isinstance(result, SimpleOutput)
        assert result.message == "Hello"
        assert result.count == 42
    
    @patch('src.core.unit.create_client')
    def test_run_with_memories(self, mock_create_client):
        """Test run() with memory injection."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = SimpleOutput(
            message="Response",
            count=1
        )
        
        unit = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        memories = [MemoryChunk(content="Context")]
        result = unit.run({"text": "Test"}, memories=memories)
        
        # Verify LLM was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Check that memories were passed to the call
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert any("Context" in msg["content"] for msg in messages)


class TestAtomicUnitTypes:
    """Test AtomicUnit type safety."""
    
    def test_generic_type_annotation(self):
        """Test that AtomicUnit preserves generic type."""
        unit = AtomicUnit[SimpleOutput](
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        assert unit.output_schema == SimpleOutput
    
    def test_different_schemas(self):
        """Test creating units with different schemas."""
        unit1 = AtomicUnit(
            template_name="extraction.j2",
            output_schema=SimpleOutput,
        )
        
        unit2 = AtomicUnit(
            template_name="extraction.j2",
            output_schema=EntityOutput,
        )
        
        assert unit1.output_schema == SimpleOutput
        assert unit2.output_schema == EntityOutput
