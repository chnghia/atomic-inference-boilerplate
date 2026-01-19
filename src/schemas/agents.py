"""
Agent-specific Pydantic schemas for LangGraph integration.

This module contains schemas for:
- Single Agent: ReAct reasoning and response
- Multi-Agent: Routing, specialized agent outputs
"""

from typing import Literal
from pydantic import BaseModel, Field


# =============================================================================
# Single Agent Schemas (ReAct Pattern)
# =============================================================================

class ReasoningStep(BaseModel):
    """
    Output schema for a single reasoning step in ReAct pattern.
    
    The agent thinks, decides on an action, and provides action input.
    """
    thought: str = Field(
        description="The agent's reasoning about what to do next"
    )
    action: Literal["search", "calculate", "respond"] = Field(
        description="The action to take: search, calculate, or respond with final answer"
    )
    action_input: str = Field(
        description="Input for the action (query for search, expression for calculate, or final answer)"
    )


class FinalResponse(BaseModel):
    """
    Output schema for the agent's final response.
    """
    answer: str = Field(description="The final answer to the user's question")
    sources: list[str] = Field(
        default_factory=list,
        description="List of sources or tools used to derive the answer"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        default=0.8,
        description="Confidence in the answer"
    )


# =============================================================================
# Multi-Agent Schemas (Orchestrator-Router Pattern)
# =============================================================================

class RoutingDecision(BaseModel):
    """
    Output schema for the orchestrator's routing decision.
    
    Determines which sub-agent should handle the user's query.
    """
    intent: str = Field(
        description="Detected user intent (e.g., 'search_info', 'analyze_data', 'general_chat')"
    )
    selected_agent: Literal["search", "analyze", "chat"] = Field(
        description="The sub-agent to route to"
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was selected"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in the routing decision"
    )


class SearchAgentOutput(BaseModel):
    """
    Output schema for the Search Agent.
    """
    query_understanding: str = Field(
        description="How the agent understood the search query"
    )
    results: list[str] = Field(
        description="List of search results or findings"
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Sources of information"
    )
    summary: str = Field(
        description="Summary of findings"
    )


class AnalyzeAgentOutput(BaseModel):
    """
    Output schema for the Analyze Agent.
    """
    analysis_type: str = Field(
        description="Type of analysis performed (e.g., 'comparison', 'breakdown', 'evaluation')"
    )
    key_findings: list[str] = Field(
        description="Key findings from the analysis"
    )
    conclusion: str = Field(
        description="Overall conclusion"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations based on analysis"
    )


class ChatAgentOutput(BaseModel):
    """
    Output schema for the Chat Agent (general conversation).
    """
    response: str = Field(
        description="The conversational response"
    )
    tone: Literal["friendly", "professional", "casual"] = Field(
        default="friendly",
        description="Tone of the response"
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )


# =============================================================================
# Unified Agent Response (for multi-agent aggregation)
# =============================================================================

class AgentResponse(BaseModel):
    """
    Unified response wrapper for any sub-agent output.
    """
    agent_name: str = Field(description="Name of the agent that produced this response")
    success: bool = Field(default=True, description="Whether the agent succeeded")
    response_text: str = Field(description="Human-readable response")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
