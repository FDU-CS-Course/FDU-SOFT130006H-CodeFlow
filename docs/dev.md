# Development Plan for AI-based Defect Analysis Tool

This document outlines the development plan to adapt the `deer-flow` codebase into an AI-based defect analysis and false positive detection tool, based on the requirements specified in `docs/demands.md`.

## 1. Workflow Modification

*   **Objective:** Modify the main workflow to align with the new processing requirements.
*   **Tasks:**
    *   **Identify Workflow Definition:** Locate the primary workflow definition file(s) (likely in `src/graph/` or `src/workflow.py`).
    *   **Bypass Coordinator:** Modify the workflow graph to skip the "Coordinator" agent. The workflow should start directly with the "Planner" agent.
    *   **Input Schema Update:** Define and implement a new input schema for the workflow to accept CppCheck output. This includes:
        *   `File` (string: path to the file with the defect)
        *   `Line` (integer: line number of the defect)
        *   `Severity` (string: severity of the defect)
        *   `Id` (string: defect ID from CppCheck)
        *   `Summary` (string: CppCheck's summary of the defect)
    *   **Entry Point:** Adjust or create an entry point (e.g., in `main.py` or a dedicated script) to parse CppCheck input and feed it to the modified workflow.

## 2. Planner Agent Enhancement

*   **Objective:** Adapt the "Planner" agent to process CppCheck inputs and gather necessary context.
*   **Tasks:**
    *   **Input Processing:** Modify the Planner (`src/agents/planner.py` or equivalent) to receive and parse the CppCheck data structure.
    *   **Source Code Context Retrieval:**
        *   Implement logic or integrate a tool call to fetch the source code content from the `File` specified in the CppCheck input.
        *   This should retrieve lines surrounding the reported `Line` number (e.g., +/- N lines, configurable).
    *   **Directory Tree Retrieval:**
        *   Implement logic or integrate a tool call to obtain the directory tree structure of the project being analyzed. This might involve using functionalities from `src/crawler/` or a new utility.
    *   **Prompt Adjustment:** Update the Planner's prompts (`src/prompts/`) to reflect the new input types and the task of defect analysis.

## 3. Tool Implementation and Integration

*   **Objective:** Implement or adapt tools required for code analysis as per `docs/demands.md`.
*   **Tasks:**
    *   **"File Reading" Tool (`src/tools/`):**
        *   Verify if an existing file reading tool can read specific line ranges from a file.
        *   If not, enhance or create a tool that accepts a file path and a line range (start, end) to return the content.
    *   **"Codebase Search" Tool (Exact Match) (`src/tools/`):**
        *   Implement a new tool for exact keyword searching (functions, classes, variables) within a specified scope (e.g., specific files or directories).
        *   The tool should return the location (file, line number) and surrounding context for each match.
        *   Consider leveraging robust command-line tools like `ripgrep` or static analysis capabilities if feasible.
    *   **"Fuzzy Codebase Search" Tool (Semantic Search) (`src/tools/`):**
        *   Design and implement a tool for semantic search across the entire codebase.
        *   **Components:**
            *   Select and integrate an embedding model suitable for code.
            *   Set up a vector store for indexing code embeddings.
            *   Develop functionality to:
                *   Embed the target codebase (or parts of it).
                *   Perform semantic similarity searches against the indexed embeddings.
            *   The tool should return relevant code snippets (location and context).
        *   This might build upon concepts from existing search tools (e.g., `src/tools/tavily_search/`) or require integration with specialized vector search libraries.

## 4. Reporter Agent Modification

*   **Objective:** Update the "Reporter" agent to include a JSON summary in its output.
*   **Tasks:**
    *   **Output Enhancement:** Modify the Reporter (`src/agents/reporter.py` or equivalent) to append a JSON object to its existing Markdown report.
    *   **JSON Structure:** The JSON summary should conform to:
        ```json
        {
          "defect_type": "string", // e.g., "false_positive", "style", "perf", "bug"
          "defect_description": "string" // A concise explanation
        }
        ```
    *   **Defect Classification Logic:**
        *   The Reporter (or the Research Team feeding into it) will need logic to determine the `defect_type` and generate the `defect_description` based on the analysis performed.
        *   This may require adjustments to the prompts for the Research Team and/or the Reporter to ensure they generate this information.

## 5. Prompt Engineering

*   **Objective:** Refine all relevant LLM prompts to support the new workflow and tasks.
*   **Tasks:**
    *   **Review Existing Prompts:** Examine prompts in `src/prompts/` for all involved agents (Planner, Research Team, Reporter).
    *   **Update Prompts:** Modify prompts to:
        *   Handle the new CppCheck input format.
        *   Guide LLMs to effectively use the new and modified tools.
        *   Instruct LLMs to generate information needed for the `defect_type` and `defect_description` in the JSON summary.
        *   Ensure prompts are clear, concise, and encourage accurate analysis.

## 6. Configuration and Dependencies

*   **Objective:** Update project configuration and manage dependencies.
*   **Tasks:**
    *   **Configuration Files (`conf.yaml.example`, `src/config/`):** Add any new configuration parameters required for the new tools (e.g., API keys for embedding services, default line context for file reading, paths to external tools).
    *   **Dependency Management (`pyproject.toml`, `requirements.txt` if used):** Add any new Python packages required for the implemented tools (e.g., vector database clients, embedding model libraries).

## 7. Testing and Validation

*   **Objective:** Ensure the modified system works correctly and meets requirements.
*   **Tasks:**
    *   **Unit Tests:** Write unit tests for new tools and significant modifications to agents.
    *   **Integration Tests:** Develop integration tests for the end-to-end workflow, using sample CppCheck outputs.
    *   **Validation:** Test with a variety of CppCheck reports to validate the accuracy of defect analysis and classification.

## 8. Documentation Update

*   **Objective:** Keep project documentation current.
*   **Tasks:**
    *   **README:** Update the main `README.md` to reflect the project's new purpose, features, and usage instructions.
    *   **Tool Documentation:** Document any new tools created, including their parameters and expected output.
    *   **Workflow Documentation:** Update any existing workflow diagrams or descriptions.
    *   This `dev.md` file will serve as the living document for the development plan and can be updated as development progresses.

This plan provides a structured approach to the required modifications. Each section may involve further breakdown into smaller tasks during implementation.
