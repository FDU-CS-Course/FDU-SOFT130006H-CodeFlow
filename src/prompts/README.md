# Prompt Templates for CppCheck Defect Analysis

This directory contains specialized prompt templates for the AI-based defect analysis and false positive detection system. The templates have been refactored to support CppCheck static analysis workflows.

## Template Overview

### Core Templates

1. **`planner.md`** - Static Code Analysis Expert
   - Specializes in CppCheck defect analysis planning
   - Processes CppCheck input context (file, line, severity, ID, summary)
   - Incorporates source code context and directory tree
   - Focuses on defect classification rather than general research

2. **`researcher.md`** - Code Investigation Specialist  
   - Conducts thorough code investigations
   - Uses specialized code analysis tools (ReadFileLinesTool, CodebaseSearchTool)
   - Focuses on pattern analysis and evidence gathering
   - Minimizes web search in favor of codebase analysis

3. **`coder.md`** - Code Analysis and Classification Expert
   - Performs detailed code analysis and pattern recognition
   - Implements classification algorithms using Python
   - Specializes in security analysis and performance assessment
   - Provides quantitative analysis and risk assessment

4. **`reporter.md`** - Software Quality Analyst
   - Writes comprehensive defect analysis reports
   - Includes required JSON summary with defect classification
   - Focuses on technical accuracy and evidence-based conclusions
   - Supports four defect types: false_positive, style, perf, bug

5. **`coordinator.md`** - Customer Communication (Bypassed)
   - Handles initial user interaction and handoffs
   - Currently bypassed in the CppCheck workflow
   - Retained for potential future use cases

## Template Features

### CppCheck Context Support

All relevant templates now support CppCheck-specific context variables:

- `cppcheck_file`: Path to the file with the defect
- `cppcheck_line`: Line number of the defect  
- `cppcheck_severity`: Severity level from CppCheck
- `cppcheck_id`: CppCheck rule ID that triggered
- `cppcheck_summary`: CppCheck's description of the issue
- `source_code_context`: Code around the defect location
- `directory_tree`: Project structure for context

### Defect Classification

The system supports four classification types:

- **`false_positive`**: Valid code incorrectly flagged by CppCheck
- **`style`**: Code style/convention issues that don't affect functionality  
- **`perf`**: Performance-related issues affecting efficiency
- **`bug`**: Genuine logical errors or security vulnerabilities

### JSON Summary Format

The reporter template includes a mandatory JSON summary:

```json
{
  "defect_type": "false_positive|style|perf|bug",
  "defect_description": "Brief technical description of the finding"
}
```

## Template System

### Core Files

- **`template.py`**: Template engine with Jinja2 support
- **`planner_model.py`**: Data models for plan structures
- **`__init__.py`**: Module exports

### Key Functions

- `apply_prompt_template()`: Renders templates with context variables
- `prepare_cppcheck_context()`: Extracts CppCheck context from state
- `validate_template_variables()`: Validates required template variables
- `get_prompt_template()`: Loads raw template content

## Usage Examples

### Basic Template Application

```python
from src.prompts import apply_prompt_template

# Apply planner template with CppCheck context
messages = apply_prompt_template("planner", state, configurable)
```

### CppCheck Context Preparation

```python
from src.prompts import prepare_cppcheck_context

# Extract CppCheck context from state
context = prepare_cppcheck_context(state)
```

### Template Validation

```python
from src.prompts import validate_template_variables

# Validate template requirements
is_valid = validate_template_variables("reporter", state)
```

## Workflow Integration

The templates integrate with the modified workflow:

1. **Planner**: Receives CppCheck input and creates analysis plan
2. **Research Team**: Investigates code using specialized tools
3. **Researcher**: Gathers evidence from codebase analysis
4. **Coder**: Performs detailed analysis and classification logic
5. **Reporter**: Generates final report with JSON classification

## Code Analysis Tools

Templates support specialized tools for code analysis:

- **ReadFileLinesTool**: Read specific file sections
- **CodebaseSearchTool**: Search for patterns across codebase
- **python_repl_tool**: Execute analysis algorithms
- **web_search_tool**: Research best practices (minimal use)

## Best Practices

### Template Development

1. **Context Awareness**: Use CppCheck context variables appropriately
2. **Tool Integration**: Leverage code analysis tools effectively  
3. **Evidence Focus**: Emphasize concrete evidence over speculation
4. **Classification Clarity**: Provide clear reasoning for defect types
5. **Locale Support**: Include proper internationalization

### Quality Guidelines

1. **Technical Accuracy**: Use precise technical language
2. **Evidence-Based**: Support conclusions with code analysis
3. **Reproducible**: Ensure analysis can be reproduced
4. **Comprehensive**: Cover all aspects of defect investigation
5. **Actionable**: Provide clear recommendations

## Maintenance Notes

- Templates use Jinja2 syntax for variable substitution
- All templates support locale-based internationalization
- CppCheck context is automatically prepared for relevant templates
- Default values are provided for common variables
- Error handling includes descriptive error messages

## Future Enhancements

Potential improvements for the template system:

1. **Dynamic Tool Loading**: Better integration with MCP tools
2. **Custom Validators**: Template-specific validation rules
3. **Performance Metrics**: Template rendering performance tracking
4. **Cache System**: Template compilation caching
5. **Testing Framework**: Automated template testing 