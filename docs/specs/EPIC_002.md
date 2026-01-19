# EPIC: LangGraph Integration Examples

## Document Information

| Field | Value |
|-------|-------|
| **EPIC ID** | EPIC-DAAG-002 |
| **Version** | 1.0.0 |
| **Status** | Draft |
| **Created Date** | 2026-01-19 |
| **Last Updated** | 2026-01-19 |
| **Author(s)** | NghiaCH |
| **Reviewer(s)** | - |
| **Approver** | - |

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-01-19 | NghiaCH | Initial EPIC specification |

---

## 1. Executive Summary

### 1.1 Problem Statement

The Atomic Inference framework acts as the **"Execution Layer"** (how to think), but real-world AI applications need an **"Orchestration Layer"** (what to do next). Without clear examples demonstrating this separation, developers may:

* Mix orchestration logic with inference logic
* Struggle to integrate AtomicUnit into agent workflows
* Not fully understand the "Engine vs Architect" philosophy

### 1.2 Solution Vision

Create a set of example implementations showing how **LangGraph** (Orchestrator) integrates with **Atomic Inference** (Execution Layer):

1. **Single Agent Example**: Simple ReAct-style agent using AtomicUnit for each reasoning step
2. **Multi-Agent Example**: Orchestrator-Router pattern with specialized sub-agents, each powered by AtomicUnit

```
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
│      │  (Search)  │    │ (Analyze)  │    │ (Respond)  │     │
│      └──────┬─────┘    └──────┬─────┘    └──────┬─────┘     │
└─────────────│─────────────────│─────────────────│───────────┘
              │                 │                 │
┌─────────────▼─────────────────▼─────────────────▼───────────┐
│                    EXECUTION LAYER                          │
│                  (Atomic Inference)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ AtomicUnit  │  │ AtomicUnit  │  │ AtomicUnit  │          │
│  │  (Render →  │  │  (Render →  │  │  (Render →  │          │
│  │  Call →     │  │  Call →     │  │  Call →     │          │
│  │  Validate)  │  │  Validate)  │  │  Validate)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Expected Outcome

* Clear demonstration of layer separation: LangGraph → Atomic Inference
* Reusable patterns for building production agents
* Understanding of when to use Single vs Multi-Agent architectures

---

## 2. Goals & Non-Goals

### 2.1 Goals

* **Single Agent Example**: Implement a ReAct agent with tool calling, using AtomicUnit for structured reasoning
* **Multi-Agent Example**: Implement Orchestrator-Router pattern with 2-3 specialized sub-agents
* **Demonstrate Integration**: Show how Pydantic schemas flow between orchestration and execution layers
* **Document Patterns**: Clear comments explaining the separation of concerns

### 2.2 Non-Goals (For This EPIC)

* **Production Agent Features**: Advanced error handling, checkpointing, human-in-the-loop
* **Complex Tools**: Real API integrations (use mocks/simple tools)
* **Agent Memory**: Long-term memory or RAG integration (covered in separate examples)

---

## 3. Feature Specifications

### 3.1 Example 1: Single Agent with Tools

**File**: `examples/langgraph_single_agent.py`

**Description**: A simple ReAct-style agent that can use tools (search, calculate) to answer questions.

**Architecture**:
```
User Query → LangGraph Agent Loop
                   │
                   ├── [Think] AtomicUnit(reasoning.j2) → ReasoningOutput
                   │
                   ├── [Act] Tool Execution (if needed)
                   │
                   └── [Respond] AtomicUnit(response.j2) → FinalResponse
```

**Key Components**:
- `ReasoningOutput(BaseModel)`: Thought, action, action_input
- `FinalResponse(BaseModel)`: Answer with sources
- AtomicUnit for structured reasoning at each step

**Tools**:
- `search_web(query)`: Simulated web search
- `calculate(expression)`: Simple math evaluation

---

### 3.2 Example 2: Multi-Agent Orchestrator-Router

**File**: `examples/langgraph_multi_agent.py`

**Description**: An orchestrator that routes user queries to specialized sub-agents, each using AtomicUnit for their specific task.

**Architecture**:
```
User Query → Orchestrator Agent
                   │
                   ▼
         ┌─────────────────┐
         │  Router Logic   │  ← AtomicUnit(routing.j2) → RoutingDecision
         │  (Intent Class) │
         └────────┬────────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   ┌───────┐  ┌───────┐  ┌───────┐
   │Search │  │Analyze│  │ Chat  │
   │ Agent │  │ Agent │  │ Agent │
   └───┬───┘  └───┬───┘  └───┬───┘
       │          │          │
       ▼          ▼          ▼
   AtomicUnit AtomicUnit AtomicUnit
   (search.j2)(analyze.j2)(chat.j2)
       │          │          │
       └──────────┼──────────┘
                  ▼
            Final Response
```

**Sub-Agents**:
1. **SearchAgent**: For queries needing external information
2. **AnalyzeAgent**: For data analysis or reasoning tasks  
3. **ChatAgent**: For general conversation

**Key Schemas**:
- `RoutingDecision(BaseModel)`: intent, confidence, selected_agent
- `SearchResult(BaseModel)`: results, sources
- `AnalysisResult(BaseModel)`: analysis, key_points
- `ChatResponse(BaseModel)`: message, follow_up_questions

---

### 3.3 Supporting Files

#### Prompt Templates

| File | Purpose |
|------|---------|
| `src/prompts/agents/routing.j2` | Intent classification for router |
| `src/prompts/agents/reasoning.j2` | ReAct reasoning step |
| `src/prompts/agents/search.j2` | Search agent prompt |
| `src/prompts/agents/analyze.j2` | Analysis agent prompt |
| `src/prompts/agents/chat.j2` | Chat agent prompt |

#### Schemas

| File | Purpose |
|------|---------|
| `src/schemas/agents.py` | Agent-specific Pydantic models |

---

## 4. Technical Implementation Plan

### Task 1: Dependencies & Setup
- Add `langgraph` to dependencies
- Create `src/prompts/agents/` directory

### Task 2: Single Agent Example
- Create reasoning and response schemas
- Implement ReAct loop with LangGraph
- Integrate AtomicUnit for each step

### Task 3: Multi-Agent Example  
- Create routing schema and prompt
- Implement Orchestrator with routing logic
- Create 3 specialized sub-agents
- Wire up LangGraph StateGraph

### Task 4: Documentation
- Add comprehensive comments
- Update README with LangGraph section
- Create integration guide

---

## 5. Success Metrics

| Metric | Criteria |
|--------|----------|
| **Separation** | No LLM calls outside AtomicUnit in examples |
| **Clarity** | Clear comments showing which layer handles what |
| **Runnable** | Both examples run successfully with local/cloud models |
| **Reusable** | Patterns can be copied for new agent types |

---

## 6. Dependencies

```toml
# Add to pyproject.toml & requirements.txt
langgraph = "^0.2"
```

---

## 7. References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ReAct Pattern Paper](https://arxiv.org/abs/2210.03629)
- [Multi-Agent Orchestration Patterns](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
