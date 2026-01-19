"""
LangGraph Multi-Agent Example - Orchestrator-Router Pattern.

Demonstrates:
- LangGraph as ORCHESTRATION LAYER with multiple sub-agents
- AtomicUnit as EXECUTION LAYER for each agent's reasoning
- Orchestrator-Router pattern: Route → Delegate → Aggregate

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    ORCHESTRATION LAYER                      │
    │                       (LangGraph)                           │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │            Orchestrator / Router                    │    │
    │  │     (Decides WHAT to do, routes to sub-agents)      │    │
    │  └──────────┬──────────────────┬───────────────────────┘    │
    │             │                  │                  │         │
    │      ┌──────▼─────┐    ┌──────▼─────┐    ┌──────▼─────┐     │
    │      │ Sub-Agent  │    │ Sub-Agent  │    │ Sub-Agent  │     │
    │      │  (Search)  │    │ (Analyze)  │    │   (Chat)   │     │
    │      └──────┬─────┘    └──────┬─────┘    └──────┬─────┘     │
    └─────────────│─────────────────│─────────────────│───────────┘
                  │                 │                 │
    ┌─────────────▼─────────────────▼─────────────────▼───────────┐
    │                    EXECUTION LAYER                          │
    │                  (Atomic Inference)                         │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │  │ AtomicUnit  │  │ AtomicUnit  │  │ AtomicUnit  │          │
    │  │ (search.j2) │  │(analyze.j2) │  │  (chat.j2)  │          │
    │  └─────────────┘  └─────────────┘  └─────────────┘          │
    └─────────────────────────────────────────────────────────────┘

Usage:
    conda activate docintel
    pip install langgraph
    python examples/langgraph_multi_agent.py
"""

import sys
from pathlib import Path
from typing import TypedDict, Literal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END

# =============================================================================
# EXECUTION LAYER: Atomic Inference Units
# =============================================================================
from src.core import AtomicUnit
from src.schemas.agents import (
    RoutingDecision,
    SearchAgentOutput,
    AnalyzeAgentOutput,
    ChatAgentOutput,
    AgentResponse,
)


# Create AtomicUnits for each agent (EXECUTION LAYER)
# Each unit handles "HOW to think" for its specific task

routing_unit = AtomicUnit(
    template_name="agents/routing.j2",
    output_schema=RoutingDecision,
    model="openai/qwen3-coder-30b",  # Change to your model
    temperature=0.3,
)

search_unit = AtomicUnit(
    template_name="agents/search.j2",
    output_schema=SearchAgentOutput,
    model="openai/qwen3-coder-30b",
    temperature=0.5,
)

analyze_unit = AtomicUnit(
    template_name="agents/analyze.j2",
    output_schema=AnalyzeAgentOutput,
    model="openai/qwen3-coder-30b",
    temperature=0.5,
)

chat_unit = AtomicUnit(
    template_name="agents/chat.j2",
    output_schema=ChatAgentOutput,
    model="openai/qwen3-coder-30b",
    temperature=0.7,
)


# =============================================================================
# Define Multi-Agent State (LangGraph)
# =============================================================================

class MultiAgentState(TypedDict):
    """State passed between nodes in the multi-agent graph."""
    query: str
    routing_decision: RoutingDecision | None
    agent_response: AgentResponse | None


# =============================================================================
# Mock Tools for Sub-Agents
# =============================================================================

def mock_web_search(query: str) -> list[str]:
    """Simulate web search results."""
    return [
        f"Result 1 for '{query}': Relevant information found...",
        f"Result 2 for '{query}': Additional details here...",
        f"Result 3 for '{query}': Related topic discovered...",
    ]


# =============================================================================
# ORCHESTRATION LAYER: LangGraph Nodes
# =============================================================================

def router_node(state: MultiAgentState) -> dict:
    """
    ROUTER: Determines which sub-agent should handle the query.
    
    Uses AtomicUnit (Execution Layer) for intent classification.
    """
    print(f"\n🔀 [ROUTER] Analyzing query...")
    
    # Call Execution Layer for routing decision
    decision = routing_unit.run({
        "query": state["query"],
    })
    
    print(f"   Intent: {decision.intent}")
    print(f"   Selected Agent: {decision.selected_agent}")
    print(f"   Reasoning: {decision.reasoning}")
    print(f"   Confidence: {decision.confidence:.2f}")
    
    return {"routing_decision": decision}


def search_agent_node(state: MultiAgentState) -> dict:
    """
    SEARCH AGENT: Handles information retrieval queries.
    
    Uses AtomicUnit (Execution Layer) for search reasoning.
    """
    print(f"\n🔍 [SEARCH AGENT] Processing query...")
    
    # Get mock search results (in production, call real search API)
    search_results = mock_web_search(state["query"])
    
    # Call Execution Layer for search synthesis
    output = search_unit.run({
        "query": state["query"],
        "search_results": search_results,
    })
    
    print(f"   Query Understanding: {output.query_understanding}")
    print(f"   Found {len(output.results)} results")
    print(f"   Summary: {output.summary[:100]}...")
    
    return {
        "agent_response": AgentResponse(
            agent_name="search",
            success=True,
            response_text=output.summary,
            metadata={"results": output.results, "sources": output.sources}
        )
    }


def analyze_agent_node(state: MultiAgentState) -> dict:
    """
    ANALYZE AGENT: Handles analysis and reasoning queries.
    
    Uses AtomicUnit (Execution Layer) for analytical thinking.
    """
    print(f"\n📊 [ANALYZE AGENT] Processing query...")
    
    # Call Execution Layer for analysis
    output = analyze_unit.run({
        "query": state["query"],
        "context": "User is asking for analysis or comparison.",
    })
    
    print(f"   Analysis Type: {output.analysis_type}")
    print(f"   Key Findings: {len(output.key_findings)} items")
    print(f"   Conclusion: {output.conclusion[:100]}...")
    
    return {
        "agent_response": AgentResponse(
            agent_name="analyze",
            success=True,
            response_text=output.conclusion,
            metadata={
                "analysis_type": output.analysis_type,
                "key_findings": output.key_findings,
                "recommendations": output.recommendations,
            }
        )
    }


def chat_agent_node(state: MultiAgentState) -> dict:
    """
    CHAT AGENT: Handles general conversation.
    
    Uses AtomicUnit (Execution Layer) for conversational response.
    """
    print(f"\n💬 [CHAT AGENT] Processing query...")
    
    # Call Execution Layer for chat response
    output = chat_unit.run({
        "message": state["query"],
    })
    
    print(f"   Tone: {output.tone}")
    print(f"   Response: {output.response[:100]}...")
    print(f"   Follow-ups: {len(output.follow_up_questions)} suggestions")
    
    return {
        "agent_response": AgentResponse(
            agent_name="chat",
            success=True,
            response_text=output.response,
            metadata={
                "tone": output.tone,
                "follow_up_questions": output.follow_up_questions,
            }
        )
    }


def route_to_agent(state: MultiAgentState) -> Literal["search", "analyze", "chat"]:
    """
    Conditional routing based on router decision.
    
    Pure Orchestration Layer logic - no LLM calls.
    """
    decision = state["routing_decision"]
    return decision.selected_agent


# =============================================================================
# Build the Multi-Agent Graph
# =============================================================================

def create_multi_agent():
    """Create the LangGraph multi-agent orchestrator."""
    
    # Create graph
    workflow = StateGraph(MultiAgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("search", search_agent_node)
    workflow.add_node("analyze", analyze_agent_node)
    workflow.add_node("chat", chat_agent_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges from router to sub-agents
    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "search": "search",
            "analyze": "analyze",
            "chat": "chat",
        }
    )
    
    # All sub-agents go to END
    workflow.add_edge("search", END)
    workflow.add_edge("analyze", END)
    workflow.add_edge("chat", END)
    
    return workflow.compile()


# =============================================================================
# Main
# =============================================================================

def main():
    """Run the multi-agent example."""
    
    print("=" * 70)
    print("🤖 LangGraph Multi-Agent (Orchestrator-Router Pattern)")
    print("   Orchestration Layer: LangGraph")
    print("   Execution Layer: Atomic Inference (AtomicUnit per agent)")
    print("=" * 70)
    
    # Create multi-agent system
    agent = create_multi_agent()
    
    # Example queries for different agents
    queries = [
        "What is the capital of France?",           # → Search Agent
        "Compare Python and JavaScript",            # → Analyze Agent
        "Hello! How are you today?",                # → Chat Agent
        "Find information about machine learning",  # → Search Agent
    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"📝 Query: {query}")
        print("=" * 70)
        
        # Initialize state
        initial_state: MultiAgentState = {
            "query": query,
            "routing_decision": None,
            "agent_response": None,
        }
        
        # Run multi-agent system
        result = agent.invoke(initial_state)
        
        # Print result
        print(f"\n{'='*70}")
        print("📋 FINAL RESULT:")
        print("=" * 70)
        if result.get("agent_response"):
            response = result["agent_response"]
            print(f"Handled by: {response.agent_name.upper()} Agent")
            print(f"Success: {response.success}")
            print(f"Response: {response.response_text}")
            if response.metadata:
                print(f"Metadata: {list(response.metadata.keys())}")
        
        print()


if __name__ == "__main__":
    main()
