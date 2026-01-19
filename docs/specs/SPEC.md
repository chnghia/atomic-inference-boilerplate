# ATOMIC INFERENCE BOILERPLATE (THE JIL STACK) – Software Requirements Specification

## Document Information

| Field | Value |
|-------|-------|
| **Version** | 1.0.0-mvp |
| **Status** | Approved |
| **Created Date** | 2026-01-19 |
| **Last Updated** | 2026-01-19 |
| **Author(s)** | NghiaCH |
| **Reviewer(s)** | NghiaCH |
| **Approver** | NghiaCH |

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 0.1 | 2026-01-19 | NghiaCH | Initial draft |

--- 

## 1. Project Overview

### 1.1 Project Name
**Atomic Inference Boilerplate (The JIL Stack)**

### 1.2 Project Description
This project is a production-ready boilerplate for building **AI Atomic Inference** using the **JIL Stack** (**J**inja2, **I**nstructor, **L**iteLLM). It serves as a lightweight and efficient "Core Framework" designed specifically to act as the **Execution Unit** of your AI architecture.

While agentic frameworks like **LangGraph** or **LangChain** act as the **"Orchestrator"** (deciding *what to do next*), Atomic Inference acts as the **"Engine"** (deciding *how to think*). It abstracts and standardizes the critical layer of LLM interaction: formatting prompts, managing API calls, handling retries, and strictly validating outputs.

### 1.3 Philosophy

We believe that building reliable AI agents requires separating **Workflow Logic** from **Inference Logic**.

1. **Atomic Design:**
Complex reasoning should be broken down into "Atomic Units"—single, focused inference steps consisting of a specific Prompt and a specific Output Schema. If the atom is stable, the molecule (Agent) is stable.
2. **Structured First (Software 2.0):**
Text is for humans; Objects are for code. We never interact with raw strings. Every inference step must return a strictly validated **Pydantic** object. We trust the Schema, not the probabilistic token stream.
3. **Separation of Concerns (Jinja2 vs. Python):**
Prompt Engineering is not the same as Software Engineering.
* **Python** handles logic, data flow, and type safety.
* **Jinja2** handles context presentation, loops, and conditional text generation.
* *Spaghetti code involving f-strings inside Python logic is strictly prohibited.*


4. **The Engine, Not the Architect:**
This framework does not try to be an agent orchestrator. It is designed to be the robust **Execution Layer** *inside* the nodes of a LangGraph or the steps of a LangChain workflow. It ensures that when the Architect asks for a brick, the Engine delivers a perfect brick, not a pile of mud.