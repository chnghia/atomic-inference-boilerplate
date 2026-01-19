"""
Jinja2 Template Renderer for Atomic Inference.

This module provides the TemplateRenderer class that handles:
- Loading templates from the prompts directory
- Rendering templates with context
- Custom filters (datetime, json, truncate)
- Template inheritance support
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateRenderer:
    """
    Jinja2-based template renderer for prompt management.
    
    Separates prompt engineering (Jinja2) from business logic (Python).
    
    Example:
        renderer = TemplateRenderer()
        prompt = renderer.render("extraction.j2", {"text": "Hello world"})
    """
    
    def __init__(self, templates_dir: str | Path | None = None):
        """
        Initialize the template renderer.
        
        Args:
            templates_dir: Path to templates directory. Defaults to src/prompts/
        """
        if templates_dir is None:
            # Default to src/prompts relative to this file's location
            templates_dir = Path(__file__).parent.parent / "prompts"
        
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._register_filters()
    
    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        # Datetime formatting filter
        self.env.filters["datetime"] = self._datetime_filter
        
        # JSON serialization filter
        self.env.filters["json"] = self._json_filter
        
        # Text truncation filter
        self.env.filters["truncate"] = self._truncate_filter
        
        # List join with custom separator
        self.env.filters["bullet"] = self._bullet_filter
    
    @staticmethod
    def _datetime_filter(dt: datetime | str, fmt: str = "%Y-%m-%d %H:%M") -> str:
        """
        Format datetime object or string.
        
        Usage in template: {{ created_at | datetime("%d/%m/%Y") }}
        """
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                return dt
        return dt.strftime(fmt)
    
    @staticmethod
    def _json_filter(obj: Any, indent: int | None = None) -> str:
        """
        Serialize object to JSON string.
        
        Usage in template: {{ data | json }}
        """
        return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)
    
    @staticmethod
    def _truncate_filter(text: str, length: int = 100, suffix: str = "...") -> str:
        """
        Truncate text to specified length.
        
        Usage in template: {{ long_text | truncate(50) }}
        """
        if len(text) <= length:
            return text
        return text[:length].rsplit(" ", 1)[0] + suffix
    
    @staticmethod
    def _bullet_filter(items: list[str], bullet: str = "- ") -> str:
        """
        Format list as bullet points.
        
        Usage in template: {{ items | bullet }}
        """
        return "\n".join(f"{bullet}{item}" for item in items)
    
    def render(self, template_name: str, context: dict[str, Any] | None = None) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name of the template file (e.g., "extraction.j2")
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered template string
            
        Raises:
            jinja2.TemplateNotFound: If template doesn't exist
        """
        if context is None:
            context = {}
        
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def render_string(self, template_string: str, context: dict[str, Any] | None = None) -> str:
        """
        Render a template from a string (for dynamic templates).
        
        Args:
            template_string: Jinja2 template as string
            context: Dictionary of variables to pass to the template
            
        Returns:
            Rendered template string
        """
        if context is None:
            context = {}
        
        template = self.env.from_string(template_string)
        return template.render(**context)
