# EPIC: Build "Atomic Inference" Codebase (JIL Stack)

## Document Information

| Field | Value |
|-------|-------|
| **EPIC ID** | EPIC-DAAG-001 |
| **Version** | 1.0.0 |
| **Status** | Draft |
| **Created Date** | 2026-01-16 |
| **Last Updated** | 2026-01-16 |
| **Author(s)** | NghiaCH |
| **Reviewer(s)** | - |
| **Approver** | - |

---

## Change History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-01-16 | NghiaCH | Initial EPIC specification |

---

## 1. Executive Summary
### 1.1 Problem Statement
In complex AI projects like *Personal Agentic Hub (PAH)* and *DocIntel*, the lack of a standardized "Execution Unit" leads to:

* **Spaghetti Code:** Prompt logic (f-strings) mixed inextricably with business logic.
* **Unreliable Outputs:** Difficulty in ensuring LLMs return structured data (JSON) consistently for downstream processing.
* **Vendor Lock-in:** Hard-coded dependencies on specific provider SDKs (e.g., OpenAI), making it difficult to switch models or use local LLMs.
* **Poor Observability:** Inconsistent logging and tracing across different agents and inference steps.

### 1.2 Solution Vision
Develop **"Atomic Inference,"** a lightweight, production-ready core framework based on the **JIL Stack** (Jinja2 + Instructor + LiteLLM). This framework will act as the dedicated **Execution Unit**, abstracting the "How to think" layer. It will decouple prompt management (Jinja2) from execution logic (Python), ensure type-safe outputs (Pydantic/Instructor), and provide a unified gateway for model routing (LiteLLM).

### 1.3 Expected Outcome

A reusable, robust boilerplate repository that:

* Reduces the time required to spin up new agents or extraction pipelines.
* Guarantees 100% structured output compliance via Pydantic validation.
* Allows seamless switching between models (GPT-4, Claude 3, Local Llama) via configuration.
* Serves as the foundational "Engine" for higher-level orchestrators like LangGraph.

## 2. Goals & Non-Goals

### 2.1 Goals

* **Establish Core Architecture:** Implement the `AtomicUnit` pattern combining Template Rendering, Model Call, and Validation.
* **Standardize Prompting:** Implement a Jinja2 loader with support for dynamic context, custom filters, and modular templates.
* **Unified Model Gateway:** Integrate LiteLLM to handle routing, retries, and API key management.
* **Type-Safe Validation:** Integrate Instructor to enforce Pydantic schemas on all LLM outputs.
* **Scaffold Project Structure:** Create a clean, scalable directory structure (`src/core`, `src/prompts`, `src/schemas`) suitable for enterprise use.

### 2.2 Non-Goals (For This EPIC)

* **Agent Orchestration:** Building complex loops, state management, or multi-agent workflows (this belongs to LangGraph/LangChain layers, not this Core Framework).
* **UI/Frontend:** Building a user interface for managing prompts.
* **Cloud Deployment:** Setting up CI/CD pipelines or cloud infrastructure (e.g., Dockerizing the app is a future task).

## 3. Feature Specifications 
### 3.1 Core Features

#### F1: The Atomic Unit (The "Engine")

* **Description:** Create the base class `AtomicUnit` that encapsulates a single inference step.
* **Requirements:**
* Accept a `template_name` (string) and `output_schema` (Pydantic Class).
* Method `.run(context: dict)` that executes the full pipeline: Render -> Call -> Validate.
* Support for injecting "Dynamic Memory" (RAG chunks) into the context.

#### F2: Template Engine (Jinja2 Integration)

* **Description:** A dedicated renderer module to handle prompt logic.
* **Requirements:**
* Load templates from a dedicated `src/prompts` directory.
* Support strictly typed variables in templates.
* Include custom filters (e.g., `| date`, `| json`) to format data inside prompts.
* Support template inheritance (e.g., `{% extends "base_system.j2" %}`).

#### F3: Universal LLM Gateway (LiteLLM Wrapper)

* **Description:** A centralized client for making API calls.
* **Requirements:**
* Wrap `litellm.completion` to support multiple providers (OpenAI, Anthropic, Azure, Ollama).
* Centralize API Key management (loading from `.env`).
* Configurable parameters (temperature, max_tokens) per Unit or globally.

#### F4: Structured Output Validation (Instructor Integration)

* **Description:** Enforce strict schema adherence for all outputs.
* **Requirements:**
* Patch the LiteLLM client with `instructor`.
* Automatically retry requests if validation fails (Max retries configuration).
* Return native Python objects (Pydantic models), not raw dictionaries or strings.

#### F5: Dynamic Memory & Context Interface

* **Description:** A standardized way to inject external data into the prompt.
* **Requirements:**
* Define a standard interface for passing "Vector DB Results" (RAG) and "Structured DB Schema" into the `run()` method.
* Ensure Jinja2 templates can handle optional context blocks (e.g., `{% if memories %}...{% endif %}`).

### 3.2 Technical Implementation Plan (Tasks)

1. **Repo Initialization:**
* Set up Git repository.
* Configure `pyproject.toml` (Poetry) with dependencies: `jinja2`, `litellm`, `instructor`, `pydantic`.

2. **Core Module Development (`src/core`):**
* Implement `renderer.py` (Jinja2 env setup).
* Implement `client.py` (LiteLLM + Instructor factory).
* Implement `unit.py` (The `AtomicUnit` class logic).

3. **Schema & Prompt Scaffolding:**
* Create directory structure for `src/prompts` and `src/schemas`.
* Create base templates (`base/system.j2`).

4. **Example Implementation:**
* Create a "Hello World" example (`examples/basic.py`) demonstrating a simple extraction task.
* Create a "RAG" example (`examples/with_memory.py`) demonstrating dynamic context injection.

## 4. Success Metrics

* **Reliability:** 100% of outputs in the example scripts return valid Pydantic objects (no JSON parsing errors).
* **Flexibility:** Ability to switch the model in `examples/basic.py` from `gpt-4o` to `claude-3-opus` by changing just one string, without breaking the code.
* **Cleanliness:** No SQL queries or complex string formatting logic inside Python business logic files.