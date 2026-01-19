"""
Dynamic Context Example - Runtime Context Building.

Demonstrates:
- Runtime context injection
- Conditional template blocks
- User profile + session state injection
- Complex context composition

Usage:
    conda activate docintel
    python examples/dynamic_context.py
"""

from datetime import datetime
from pydantic import BaseModel, Field

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import AtomicUnit


# Define output schema
class PersonalizedResponse(BaseModel):
    """Schema for personalized assistant response."""
    greeting: str = Field(description="Personalized greeting")
    response: str = Field(description="Main response to the query")
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up actions"
    )
    tone: str = Field(description="Detected tone: formal, casual, or friendly")


def build_user_context(user_id: str) -> dict:
    """
    Build dynamic user context.
    
    In production, this would fetch from database/session store.
    """
    # Simulated user data
    users = {
        "user_001": {
            "name": "Nghia",
            "role": "Developer",
            "preferences": {
                "language": "vi",
                "tone": "casual",
                "timezone": "Asia/Ho_Chi_Minh"
            },
            "recent_topics": ["Python", "AI agents", "LangGraph"],
        },
        "user_002": {
            "name": "John",
            "role": "Manager",
            "preferences": {
                "language": "en",
                "tone": "formal",
                "timezone": "America/New_York"
            },
            "recent_topics": ["project planning", "team metrics"],
        }
    }
    
    return users.get(user_id, {"name": "User", "preferences": {"tone": "friendly"}})


def build_session_context() -> dict:
    """Build session-specific context."""
    return {
        "current_time": datetime.now(),
        "session_id": "sess_12345",
        "conversation_turn": 3,
    }


def main():
    """Run dynamic context example."""
    
    # Create dynamic context template (inline for demonstration)
    context_template = """
{% if user.name %}
You are speaking with {{ user.name }}{% if user.role %}, who is a {{ user.role }}{% endif %}.
{% endif %}

{% if user.preferences %}
## User Preferences
- Preferred tone: {{ user.preferences.tone | default('friendly') }}
- Language: {{ user.preferences.language | default('en') }}
{% endif %}

{% if user.recent_topics %}
## Recent Discussion Topics
{{ user.recent_topics | bullet }}
{% endif %}

## Session Info
- Current time: {{ session.current_time | datetime("%H:%M %d/%m/%Y") }}
- Conversation turn: {{ session.conversation_turn }}

## User Query
{{ query }}

## Instructions
1. Greet the user appropriately based on their preferences
2. Answer their query in their preferred tone
3. Suggest relevant follow-up actions based on their recent topics
"""
    
    # Build contexts
    user_context = build_user_context("user_001")  # Try "user_002" for different style
    session_context = build_session_context()
    
    print("=" * 60)
    print("DYNAMIC CONTEXT DEMONSTRATION")
    print("=" * 60)
    print(f"\nUser: {user_context.get('name')}")
    print(f"Role: {user_context.get('role', 'N/A')}")
    print(f"Tone: {user_context.get('preferences', {}).get('tone', 'friendly')}")
    
    # Combine all context
    full_context = {
        "user": user_context,
        "session": session_context,
        "query": "Hôm nay tôi nên làm gì với dự án AI agent?"
    }
    
    # Render template
    from src.core.renderer import TemplateRenderer
    renderer = TemplateRenderer()
    prompt = renderer.render_string(context_template, full_context)
    
    print("\n" + "=" * 60)
    print("GENERATED PROMPT:")
    print("=" * 60)
    print(prompt)
    
    # Create AtomicUnit and run
    print("\n" + "=" * 60)
    print("RUNNING WITH DYNAMIC CONTEXT...")
    print("=" * 60)
    
    from src.core.client import create_client
    client = create_client()
    
    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_model=PersonalizedResponse,
    )
    
    print(f"\nGreeting: {result.greeting}")
    print(f"Tone: {result.tone}")
    print(f"\nResponse:\n{result.response}")
    print(f"\nSuggestions:")
    for i, suggestion in enumerate(result.suggestions, 1):
        print(f"  {i}. {suggestion}")


if __name__ == "__main__":
    main()
