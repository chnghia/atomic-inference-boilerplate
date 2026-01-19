"""
LangGraph Single Agent Example - ReAct Pattern.

Demonstrates:
- LangGraph as ORCHESTRATION LAYER (what to do next)
- AtomicUnit as EXECUTION LAYER (how to think)
- ReAct pattern: Think → Act → Observe loop

Architecture:
    User Query → LangGraph Agent Loop
                       │
                       ├── [Think] AtomicUnit(reasoning.j2) → ReasoningStep
                       │
                       ├── [Act] Tool Execution (search/calculate)
                       │
                       └── [Respond] Final Answer

Usage:
    conda activate atomic
    pip install langgraph
    python examples/langgraph_single_agent.py
"""

import sys
from pathlib import Path
from typing import TypedDict, Annotated
import operator

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END

# =============================================================================
# EXECUTION LAYER: Atomic Inference
# =============================================================================
from src.core import AtomicUnit
from src.schemas.agents import ReasoningStep, FinalResponse


# =============================================================================
# Define Agent State (LangGraph)
# =============================================================================

class AgentState(TypedDict):
    """State passed between nodes in the agent graph."""
    question: str
    observations: Annotated[list[dict], operator.add]  # Accumulated observations
    current_step: ReasoningStep | None
    final_answer: FinalResponse | None
    step_count: int


# =============================================================================
# Tools (Simple implementations for demo)
# =============================================================================

def search_tool(query: str) -> str:
    """Simulated web search tool."""
    # In production, this would call a real search API
    mock_results = {
        "python": "Python is a high-level programming language created by Guido van Rossum in 1991.",
        "weather": "The weather today is sunny with a high of 25°C.",
        "langgraph": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
    }
    
    query_lower = query.lower()
    for key, result in mock_results.items():
        if key in query_lower:
            return result
    
    return f"Search results for '{query}': General information found."


def calculate_tool(expression: str) -> str:
    """Simple calculator tool."""
    try:
        # Safe eval for simple math (in production, use a proper parser)
        allowed_chars = set("0123456789+-*/().% ")
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"Result: {result}"
        else:
            return "Error: Invalid characters in expression"
    except Exception as e:
        return f"Calculation error: {str(e)}"


# =============================================================================
# ORCHESTRATION LAYER: LangGraph Nodes
# Each node uses AtomicUnit (Execution Layer) for LLM calls
# =============================================================================

# Create AtomicUnit for reasoning steps
reasoning_unit = AtomicUnit(
    template_name="agents/reasoning.j2",
    output_schema=ReasoningStep,
    model="openai/qwen3-coder-30b",  # Change to your model
    temperature=0.3,
)


def think_node(state: AgentState) -> dict:
    """
    THINK: Use AtomicUnit to decide next action.
    
    This is where Orchestration Layer calls Execution Layer.
    """
    print(f"\n🧠 [THINK] Step {state['step_count'] + 1}")
    
    # Call Execution Layer (AtomicUnit)
    reasoning = reasoning_unit.run({
        "question": state["question"],
        "observations": state["observations"],
    })
    
    print(f"   Thought: {reasoning.thought}")
    print(f"   Action: {reasoning.action}")
    print(f"   Input: {reasoning.action_input}")
    
    return {
        "current_step": reasoning,
        "step_count": state["step_count"] + 1,
    }


def act_node(state: AgentState) -> dict:
    """
    ACT: Execute the tool selected by the reasoning step.
    
    This is pure Orchestration Layer logic - no LLM calls.
    """
    step = state["current_step"]
    
    if step.action == "respond":
        # No tool execution needed, just pass to respond
        return {"observations": []}
    
    print(f"\n⚡ [ACT] Executing {step.action}...")
    
    # Execute tool
    if step.action == "search":
        result = search_tool(step.action_input)
    elif step.action == "calculate":
        result = calculate_tool(step.action_input)
    else:
        result = f"Unknown action: {step.action}"
    
    print(f"   Result: {result}")
    
    # Add observation
    observation = {
        "action": step.action,
        "action_input": step.action_input,
        "result": result,
    }
    
    return {"observations": [observation]}


def respond_node(state: AgentState) -> dict:
    """
    RESPOND: Generate final answer using AtomicUnit.
    
    Another call to Execution Layer with different prompt.
    """
    print(f"\n✅ [RESPOND] Generating final answer...")
    
    step = state["current_step"]
    
    # For simple cases, use the action_input as the answer
    final = FinalResponse(
        answer=step.action_input,
        sources=[obs["action"] for obs in state["observations"]],
        confidence=0.85,
    )
    
    return {"final_answer": final}


def should_continue(state: AgentState) -> str:
    """
    ROUTER: Decide whether to continue loop or respond.
    
    This is Orchestration Layer decision logic.
    """
    step = state["current_step"]
    
    # If action is respond, go to respond node
    if step.action == "respond":
        return "respond"
    
    # Safety check: max iterations
    if state["step_count"] >= 5:
        return "respond"
    
    # Continue the loop
    return "continue"


# =============================================================================
# Build the Agent Graph
# =============================================================================

def create_agent():
    """Create the LangGraph agent."""
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("think", think_node)
    workflow.add_node("act", act_node)
    workflow.add_node("respond", respond_node)
    
    # Set entry point
    workflow.set_entry_point("think")
    
    # Add conditional edge from think
    workflow.add_conditional_edges(
        "think",
        should_continue,
        {
            "continue": "act",
            "respond": "respond",
        }
    )
    
    # After act, go back to think
    workflow.add_edge("act", "think")
    
    # Respond is the end
    workflow.add_edge("respond", END)
    
    return workflow.compile()


# =============================================================================
# Main
# =============================================================================

def main():
    """Run the single agent example."""
    
    print("=" * 60)
    print("🤖 LangGraph Single Agent (ReAct Pattern)")
    print("   Orchestration Layer: LangGraph")
    print("   Execution Layer: Atomic Inference")
    print("=" * 60)
    
    # Create agent
    agent = create_agent()
    
    # Example questions
    questions = [
        "What is Python and calculate 2 + 2 * 10",
        "Tell me about LangGraph",
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"📝 Question: {question}")
        print("=" * 60)
        
        # Initialize state
        initial_state: AgentState = {
            "question": question,
            "observations": [],
            "current_step": None,
            "final_answer": None,
            "step_count": 0,
        }
        
        # Run agent
        result = agent.invoke(initial_state)
        
        # Print result
        print(f"\n{'='*60}")
        print("📋 FINAL RESULT:")
        print("=" * 60)
        if result.get("final_answer"):
            final = result["final_answer"]
            print(f"Answer: {final.answer}")
            print(f"Sources: {final.sources}")
            print(f"Confidence: {final.confidence}")
        
        print()


if __name__ == "__main__":
    main()
