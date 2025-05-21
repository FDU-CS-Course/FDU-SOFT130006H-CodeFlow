# Codebase Status Report (src/ directory)

This document provides an overview of the `src/` directory structure and design, based on an initial code walkthrough.

## Core Workflow and Graph (`src/workflow.py`, `src/graph/`)

*   **`src/workflow.py`**: Defines and runs the main asynchronous agent workflow.
    *   Uses `src.graph.build_graph()` to get the compiled agent graph.
    *   `run_agent_workflow_async()` is the primary entry point for executing the workflow with user input and configurations.
    *   Handles streaming of results from the graph.
*   **`src/graph/`**: Contains the LangGraph-based graph definition.
    *   **`builder.py`**: Builds the `StateGraph`.
        *   `_build_base_graph()`: Defines nodes (coordinator, planner, researcher, etc.) and their basic connections (START, END).
        *   `build_graph()`: Compiles the graph (currently without persistent memory).
        *   `build_graph_with_memory()`: Provides an option to build with `MemorySaver`.
    *   **`nodes.py`**: Implements the logic for each node in the graph.
        *   Nodes include: `coordinator_node`, `planner_node`, `research_team_node`, `researcher_node`, `coder_node`, `reporter_node`, `human_feedback_node`, `background_investigation_node`.
        *   Nodes interact with LLMs, tools, and manage the `State`.
        *   Uses helper functions like `_execute_agent_step` for agent execution.
    *   **`types.py`**: Defines the `State` class (inheriting from `MessagesState`) which is the shared state object passed between graph nodes. It includes fields for messages, plan, observations, locale, etc.

## Agents (`src/agents/`)

*   **`src/agents/agents.py`**: Contains a factory function `create_agent()`.
    *   Uses `langgraph.prebuilt.create_react_agent` to create ReAct-style agents.
    *   Configures agents with an LLM (via `src.llms.get_llm_by_type`), a list of tools, and a dynamically rendered prompt (via `src.prompts.apply_prompt_template`).
*   The core agent logic (what each agent *does*) is primarily implemented within the corresponding functions in `src/graph/nodes.py`.

## Tools (`src/tools/`)

*   Provides various tools that agents can use.
*   **`__init__.py`** exports:
    *   `crawl_tool` (from `crawl.py`): For web crawling.
    *   `python_repl_tool` (from `python_repl.py`): For executing Python code.
    *   `get_web_search_tool` (from `search.py`): A generic web search tool.
    *   `VolcengineTTS` (from `tts.py`): For text-to-speech.
*   **`tavily_search/`**: Contains specific integration for Tavily search (e.g., `LoggedTavilySearch` used in `nodes.py`).
*   **`decorators.py`**: Likely provides decorators for tool functions (e.g., for logging).
*   **`file_reader.py`**: Implements `ReadFileLinesTool` for reading specific line ranges from files.
*   **`codebase_search.py`**: Implements `CodebaseSearchTool` for exact codebase searching using `ripgrep`.

## Prompts (`src/prompts/`)

*   Manages prompt templates for LLMs.
*   **`template.py`**: Uses Jinja2 to load and render prompt templates.
    *   `apply_prompt_template()`: Takes a prompt name and the current agent `State`, renders the template, and prepends it as a system message to the existing conversation messages.
*   **`.md` files** (e.g., `planner.md`, `researcher.md`): Contain the actual Jinja2 prompt templates for different agents/nodes.
*   **`planner_model.py`**: Defines a Pydantic model `Plan` for structured output from the planner LLM.
*   The subdirectories for specialized tasks like `podcast/`, `ppt/`, and `prose/` have been removed as they are not relevant to the current defect analysis goals.

## LLMs (`src/llms/`)

*   **`llm.py`**: Manages LLM instances (currently `ChatOpenAI`).
    *   `get_llm_by_type()`: Retrieves an LLM instance, using a cache. It loads LLM configurations (model names, parameters) from the root `conf.yaml` based on an `LLMType` (e.g., "basic", "reasoning").
    *   `LLMType` and the mapping of agents to LLM types (`AGENT_LLM_MAP`) are defined in `src/config/agents.py`.

## Configuration (`src/config/`)

*   Handles loading and access to configuration parameters.
*   **`loader.py`**: Defines `load_yaml_config()` which loads YAML files, supports environment variable substitution (e.g., `$VAR_NAME`), and caches results.
*   **`configuration.py`**: Defines a dataclass `Configuration` holding runtime parameters (e.g., `max_plan_iterations`, `max_search_results`).
    *   `Configuration.from_runnable_config()` allows creating an instance from LangGraph's `RunnableConfig`, with overrides from environment variables.
*   **`agents.py`**: Defines `LLMType` (Literal: "basic", "reasoning", "vision") and `AGENT_LLM_MAP` (e.g., `{"planner": "basic"}`).
*   **`tools.py`**: May contain tool-specific configurations (not deeply inspected).
*   **`questions.py`**: Purpose not fully clear, possibly example inputs or related config.
*   The main configuration file for LLMs and other settings appears to be `conf.yaml` in the project root.

## Server (`src/server/`)

*   Contains code for an API server.
*   **`app.py`**: Likely the main application file for a FastAPI/Flask server.
*   Includes modules for handling chat requests (`chat_request.py`) and MCP (Multi-Server Client Protocol) requests (`mcp_request.py`, `mcp_utils.py`). This suggests the server can expose the agent workflow via an API and potentially interact with other tool servers.

## Utilities (`src/utils/`)

*   **`json_utils.py`**: Provides utilities for JSON manipulation, such as `repair_json_output` (used in `nodes.py` to fix potentially malformed JSON from LLMs).

## Specialized Modules

*   The specialized modules from the original `deer-flow` (`src/prose/`, `src/podcast/`, `src/ppt/`) designed for specific content generation tasks (prose, podcasts, PowerPoint presentations) have been removed as they are not aligned with the new defect analysis objectives.

## Overall Design

*   The system is built around **LangGraph**, orchestrating a flow of state through different nodes (agents/logic blocks).
*   **Agents** are created using a ReAct pattern, equipped with LLMs and tools.
*   **Prompts** are managed using Jinja2 templates.
*   **Configuration** is loaded from YAML files (primarily `conf.yaml`) and environment variables, with specific classes and mappings in `src/config/`.
*   **Tools** are modular and can be assigned to agents.
*   The project includes a **server component** to expose functionality via an API.
*   The codebase is generally well-structured with clear separation of concerns (graph logic, agent creation, tools, prompts, LLM management, configuration).
