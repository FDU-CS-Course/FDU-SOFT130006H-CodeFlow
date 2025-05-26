# Development Plan for AI-based Defect Analysis Tool

This document outlines the development plan to adapt the `deer-flow` codebase into an AI-based defect analysis and false positive detection tool, based on the requirements specified in `docs/demands.md`.

## 1. Workflow Modification

*   **Objective:** Modify the main workflow to align with the new processing requirements.
*   **Tasks:**
    *   **Identify Workflow Definition:** ✅ Located the primary workflow definition in `src/graph/builder.py` and `src/workflow.py`.
    *   **Bypass Coordinator:** ✅ Modified the workflow graph to skip the "Coordinator" agent. The workflow now starts directly with the "Planner" agent.
        * Changes made in `src/graph/builder.py` to change the initial edge from START to "planner" instead of "coordinator".
        * Updated `src/workflow.py` and `src/server/app.py` to include the "locale" field in the initial state, which was previously set by the coordinator.
    *   **Input Schema Update:** ✅ Defined and implemented a new input schema for the workflow to accept CppCheck output. This includes:
        *   `File` (string: path to the file with the defect)
        *   `Line` (integer: line number of the defect)
        *   `Severity` (string: severity of the defect)
        *   `Id` (string: defect ID from CppCheck)
        *   `Summary` (string: CppCheck's summary of the defect)
        *   Implementation added to `src/workflow.py` with the new `run_cppcheck_analysis_async()` function.
    *   **Entry Point:** ✅ Created a dedicated entry point in `main.py` to parse CppCheck input and feed it to the modified workflow.
        *   Added a new "cppcheck" subcommand that accepts input either as a JSON file, inline JSON string, or individual command-line arguments.
        *   The `analyze_cppcheck()` function processes the input and calls the appropriate workflow function.

## 2. Planner Agent Enhancement

*   **Objective:** Adapt the "Planner" agent to process CppCheck inputs and gather necessary context.
*   **Tasks:**
    *   **Input Processing:** ✅ Modified the Planner (`src/graph/nodes.py`) to receive and parse the CppCheck data structure.
        *   Updated the `planner_node` function to look for CppCheck-specific fields in the state.
    *   **Source Code Context Retrieval:** ✅ Implemented logic to fetch the source code content from the specified file.
        *   Added code in `planner_node` to use the `ReadFileLinesTool` to retrieve the source code around the reported line number (+/- 20 lines).
    *   **Directory Tree Retrieval:** ✅ Implemented logic to obtain the directory tree structure of the project being analyzed.
        *   Added code in `planner_node` to traverse the directory structure and build a directory tree, limiting depth to manage output size.
    *   **Prompt Adjustment:** Existing planner prompt is sufficient as it receives the source context as part of the state.

## 3. Tool Implementation and Integration

*   **Objective:** Implement or adapt tools required for code analysis as per `docs/demands.md`.
*   **Tasks:**
    *   **"File Reading" Tool (`src/tools/`):** ✅
        *   **Implemented:** A new tool `ReadFileLinesTool` in `src/tools/file_reader.py` allows reading specific line ranges. It is exported in `src/tools/__init__.py`.
    *   **"Codebase Search" Tool (Exact Match) (`src/tools/`):** ✅
        *   **Implemented:** A new tool `CodebaseSearchTool` in `src/tools/codebase_search.py` uses `ripgrep` for fast exact searching. It provides results in JSON format with context and is exported in `src/tools/__init__.py`. Requires `ripgrep` to be installed on the system.
    *   **"Fuzzy Codebase Search" Tool (Semantic Search) (`src/tools/`):** ❌
        *   **Not Implemented:** The semantic search capability was deprioritized as the exact match search provides sufficient functionality for the initial version.
        *   Future work could include integrating an embedding model for code and setting up a vector store for semantic search.

## 4. Tool Integration in Agent Workflow

*   **Objective:** Ensure the tools are properly integrated into the agent workflow.
*   **Tasks:**
    *   **Tools in Researcher Node:** ✅
        *   Added `ReadFileLinesTool` and `CodebaseSearchTool` to the researcher agent's tools list in `src/graph/nodes.py`.
        *   Updated the `researcher.md` prompt to document the new tools and provide guidance on how to use them.
    *   **Tools in Coder Node:** ✅
        *   Added `ReadFileLinesTool` and `CodebaseSearchTool` to the coder agent's tools list in `src/graph/nodes.py`.
        *   Updated the `coder.md` prompt to document the new tools and provide guidance on how to use them.

## 5. Reporter Agent Modification

*   **Objective:** Update the "Reporter" agent to include a JSON summary in its output.
*   **Tasks:**
    *   **Output Enhancement:** The reporter node already produces markdown output. The JSON summary is expected to be part of this markdown output.
    *   **JSON Structure:** ✅ The expected JSON summary structure is documented in the prompts and code. It should conform to:
        ```json
        {
          "defect_type": "string", // e.g., "false_positive", "style", "perf", "bug"
          "defect_description": "string" // A concise explanation
        }
        ```
    *   **Defect Classification Logic:** ✅ 
        *   The researcher and coder agents are now informed through their prompts about the need to classify defects.
        *   The main.py file now includes logic to extract the JSON summary from the report and display it separately.

## 6. Prompt Engineering

*   **Objective:** Refine all relevant LLM prompts to support the new workflow and tasks.
*   **Tasks:**
    *   **Review Existing Prompts:** ✅ Examined prompts in `src/prompts/` for all involved agents (Planner, Research Team, Reporter).
    *   **Update Prompts:** ✅ Modified prompts to:
        *   Handle the new CppCheck input format.
        *   Guide LLMs to effectively use the new and modified tools.
        *   Instruct LLMs to generate information needed for the `defect_type` and `defect_description` in the JSON summary.
        *   Specifically updated the researcher.md and coder.md prompts with detailed instructions about the code analysis tools.

## 7. Configuration and Dependencies

*   **Objective:** Update project configuration and manage dependencies.
*   **Tasks:**
    *   **Configuration Files:** No changes needed for the new tools - they use standard libraries already in the project.
    *   **External Dependencies:** `ripgrep` is required for the CodebaseSearchTool to work. This should be documented in the README.

## 8. Testing and Validation

*   **Objective:** Ensure the modified system works correctly and meets requirements.
*   **Tasks:**
    *   **Unit Tests:** ❌ Not implemented yet. Need to write tests for the new tools and workflow.
    *   **Integration Tests:** ❌ Not implemented yet. Need to develop tests for the end-to-end workflow with sample CppCheck outputs.
    *   **Validation:** ❌ Not performed yet. Will require testing with a variety of CppCheck reports.

## 9. Documentation Update

*   **Objective:** Keep project documentation current.
*   **Tasks:**
    *   **README:** ❌ Not updated yet. Needs information about the new CppCheck analysis capability.
    *   **Tool Documentation:** ✅ The new tools are documented in their respective prompt files.
    *   **Workflow Documentation:** ✅ This dev.md file has been updated to reflect the development progress.

This plan provides a structured approach to the required modifications. Each section may involve further breakdown into smaller tasks during implementation.
