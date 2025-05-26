# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
import dataclasses
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from langgraph.prebuilt.chat_agent_executor import AgentState
from src.config.configuration import Configuration

# Initialize Jinja2 environment
env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_prompt_template(prompt_name: str) -> str:
    """
    Load and return a prompt template using Jinja2.

    Args:
        prompt_name: Name of the prompt template file (without .md extension)

    Returns:
        The template string with proper variable substitution syntax
        
    Raises:
        ValueError: If template cannot be loaded
    """
    try:
        template = env.get_template(f"{prompt_name}.md")
        return template.render()
    except Exception as e:
        raise ValueError(f"Error loading template {prompt_name}: {e}")


def prepare_cppcheck_context(state: AgentState) -> Dict[str, Any]:
    """
    Prepare CppCheck-specific context variables from the state.
    
    Args:
        state: Current agent state containing CppCheck data
        
    Returns:
        Dict containing CppCheck context variables
    """
    return {
        "cppcheck_file": state.get("cppcheck_file"),
        "cppcheck_line": state.get("cppcheck_line"),
        "cppcheck_severity": state.get("cppcheck_severity"),
        "cppcheck_id": state.get("cppcheck_id"),
        "cppcheck_summary": state.get("cppcheck_summary"),
        "source_code_context": state.get("source_code_context"),
        "directory_tree": state.get("directory_tree"),
    }


def apply_prompt_template(
    prompt_name: str, 
    state: AgentState, 
    configurable: Optional[Configuration] = None
) -> list:
    """
    Apply template variables to a prompt template and return formatted messages.

    Args:
        prompt_name: Name of the prompt template to use
        state: Current agent state containing variables to substitute
        configurable: Optional configuration object with additional settings

    Returns:
        List of messages with the system prompt as the first message
        
    Raises:
        ValueError: If template cannot be applied
    """
    # Convert state to dict for template rendering
    state_vars = {
        "CURRENT_TIME": datetime.now().strftime("%a %b %d %Y %H:%M:%S %z"),
        **state,
    }

    # Add configurable variables
    if configurable:
        state_vars.update(dataclasses.asdict(configurable))

    # Add CppCheck-specific context for relevant templates
    if prompt_name in ["planner", "reporter"]:
        cppcheck_context = prepare_cppcheck_context(state)
        
        # For reporter, wrap CppCheck data in cppcheck_details structure
        if prompt_name == "reporter":
            state_vars["cppcheck_details"] = cppcheck_context
        else:
            # For planner, add CppCheck variables directly
            state_vars.update(cppcheck_context)

    # Set default values for common template variables
    state_vars.setdefault("locale", "en-US")
    state_vars.setdefault("max_step_num", 6)

    try:
        template = env.get_template(f"{prompt_name}.md")
        system_prompt = template.render(**state_vars)
        return [{"role": "system", "content": system_prompt}] + state.get("messages", [])
    except Exception as e:
        raise ValueError(f"Error applying template {prompt_name}: {e}")


def validate_template_variables(prompt_name: str, state: AgentState) -> bool:
    """
    Validate that required template variables are present in the state.
    
    Args:
        prompt_name: Name of the template to validate
        state: Current agent state
        
    Returns:
        True if all required variables are present, False otherwise
    """
    required_vars = {
        "planner": ["locale"],
        "researcher": ["locale"],
        "coder": ["locale"],
        "reporter": ["locale"],
        "coordinator": ["locale"],
    }
    
    template_vars = required_vars.get(prompt_name, [])
    
    for var in template_vars:
        if var not in state:
            return False
    
    return True
