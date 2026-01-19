"""
Tests for TemplateRenderer.

Run with: pytest tests/test_renderer.py -v
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.renderer import TemplateRenderer
from src.core.types import MemoryChunk


class TestTemplateRenderer:
    """Test cases for TemplateRenderer."""
    
    @pytest.fixture
    def renderer(self):
        """Create a renderer instance."""
        return TemplateRenderer()
    
    def test_render_string_basic(self, renderer):
        """Test basic string template rendering."""
        template = "Hello, {{ name }}!"
        result = renderer.render_string(template, {"name": "World"})
        assert result == "Hello, World!"
    
    def test_render_string_with_loop(self, renderer):
        """Test template with loop."""
        template = """
{% for item in items %}
- {{ item }}
{% endfor %}
"""
        result = renderer.render_string(template, {"items": ["a", "b", "c"]})
        assert "- a" in result
        assert "- b" in result
        assert "- c" in result
    
    def test_datetime_filter(self, renderer):
        """Test datetime filter."""
        template = "Date: {{ dt | datetime('%Y-%m-%d') }}"
        dt = datetime(2024, 1, 15, 10, 30)
        result = renderer.render_string(template, {"dt": dt})
        assert result == "Date: 2024-01-15"
    
    def test_datetime_filter_with_time(self, renderer):
        """Test datetime filter with time."""
        template = "Time: {{ dt | datetime('%H:%M') }}"
        dt = datetime(2024, 1, 15, 10, 30)
        result = renderer.render_string(template, {"dt": dt})
        assert result == "Time: 10:30"
    
    def test_json_filter(self, renderer):
        """Test JSON filter."""
        template = "Data: {{ data | json }}"
        result = renderer.render_string(template, {"data": {"key": "value"}})
        # Note: Jinja2 autoescapes " to &#34; in output
        assert "key" in result
        assert "value" in result
    
    def test_truncate_filter(self, renderer):
        """Test truncate filter."""
        template = "{{ text | truncate(10) }}"
        result = renderer.render_string(template, {"text": "This is a very long text"})
        assert len(result) <= 13  # 10 + "..."
        assert result.endswith("...")
    
    def test_truncate_filter_short_text(self, renderer):
        """Test truncate filter with short text."""
        template = "{{ text | truncate(50) }}"
        result = renderer.render_string(template, {"text": "Short"})
        assert result == "Short"
        assert "..." not in result
    
    def test_bullet_filter(self, renderer):
        """Test bullet filter."""
        template = "{{ items | bullet }}"
        result = renderer.render_string(template, {"items": ["one", "two", "three"]})
        assert result == "- one\n- two\n- three"
    
    def test_conditional_rendering(self, renderer):
        """Test conditional blocks."""
        template = """
{% if show_header %}
# Header
{% endif %}
Content here
"""
        result_with = renderer.render_string(template, {"show_header": True})
        assert "# Header" in result_with
        
        result_without = renderer.render_string(template, {"show_header": False})
        assert "# Header" not in result_without
    
    def test_memory_chunk_rendering(self, renderer):
        """Test rendering with MemoryChunk objects."""
        template = """
{% for memory in memories %}
- {{ memory.content }}{% if memory.source %} ({{ memory.source }}){% endif %}
{% endfor %}
"""
        memories = [
            MemoryChunk(content="First memory", source="doc1.pdf"),
            MemoryChunk(content="Second memory"),
        ]
        result = renderer.render_string(template, {"memories": memories})
        assert "First memory" in result
        assert "(doc1.pdf)" in result
        assert "Second memory" in result
    
    def test_empty_context(self, renderer):
        """Test rendering with no context."""
        template = "Static content"
        result = renderer.render_string(template)
        assert result == "Static content"
    
    def test_render_extraction_template(self, renderer):
        """Test rendering the extraction.j2 template."""
        result = renderer.render("extraction.j2", {
            "text": "Sample text here",
            "entity_types": ["person", "organization"]
        })
        assert "Sample text here" in result
        assert "person" in result
        assert "organization" in result


class TestTemplateRendererEdgeCases:
    """Edge case tests for TemplateRenderer."""
    
    @pytest.fixture
    def renderer(self):
        return TemplateRenderer()
    
    def test_datetime_filter_with_string(self, renderer):
        """Test datetime filter with ISO string input."""
        template = "{{ dt | datetime('%Y-%m-%d') }}"
        result = renderer.render_string(template, {"dt": "2024-01-15T10:30:00"})
        assert result == "2024-01-15"
    
    def test_datetime_filter_with_invalid_string(self, renderer):
        """Test datetime filter with invalid string (should return as-is)."""
        template = "{{ dt | datetime }}"
        result = renderer.render_string(template, {"dt": "not-a-date"})
        assert result == "not-a-date"
    
    def test_json_filter_with_nested(self, renderer):
        """Test JSON filter with nested structures."""
        template = "{{ data | json }}"
        result = renderer.render_string(template, {
            "data": {"nested": {"key": [1, 2, 3]}}
        })
        assert "[1, 2, 3]" in result
