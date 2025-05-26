# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import asyncio
import logging
from typing import Dict, Optional, Union, Any
from src.graph import build_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default level is INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    logging.getLogger("src").setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)

# Create the graph
graph = build_graph()


async def run_agent_workflow_async(
    user_input: str,
    debug: bool = False,
    max_plan_iterations: int = 1,
    max_step_num: int = 3,
    enable_background_investigation: bool = True,
):
    """Run the agent workflow asynchronously with the given user input.

    Args:
        user_input: The user's query or request
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning to enhance context

    Returns:
        The final state after the workflow completes
    """
    if not user_input:
        raise ValueError("Input could not be empty")

    if debug:
        enable_debug_logging()

    logger.info(f"Starting async workflow with user input: {user_input}")
    initial_state = {
        # Runtime Variables
        "messages": [{"role": "user", "content": user_input}],
        "auto_accepted_plan": True,
        "enable_background_investigation": enable_background_investigation,
        "locale": "en-US",  # Default locale previously set by coordinator
    }
    config = {
        "configurable": {
            "thread_id": "default",
            "max_plan_iterations": max_plan_iterations,
            "max_step_num": max_step_num,
            "mcp_settings": {
                "servers": {
                    "mcp-github-trending": {
                        "transport": "stdio",
                        "command": "uvx",
                        "args": ["mcp-github-trending"],
                        "enabled_tools": ["get_github_trending_repositories"],
                        "add_to_agents": ["researcher"],
                    }
                }
            },
        },
        "recursion_limit": 100,
    }
    last_message_cnt = 0
    async for s in graph.astream(
        input=initial_state, config=config, stream_mode="values"
    ):
        try:
            if isinstance(s, dict) and "messages" in s:
                if len(s["messages"]) <= last_message_cnt:
                    continue
                last_message_cnt = len(s["messages"])
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()
            else:
                # For any other output format
                print(f"Output: {s}")
        except Exception as e:
            logger.error(f"Error processing stream output: {e}")
            print(f"Error processing output: {str(e)}")

    logger.info("Async workflow completed successfully")


async def run_cppcheck_analysis_async(
    cppcheck_data: Dict[str, Any],
    debug: bool = False,
    max_plan_iterations: int = 1,
    max_step_num: int = 3,
    enable_background_investigation: bool = False,
):
    """Run the agent workflow for analyzing CppCheck defect reports.

    Args:
        cppcheck_data: Dictionary containing CppCheck defect information
            Required fields:
                - file (str): Path to the file with the defect
                - line (int): Line number of the defect
                - severity (str): Severity of the defect
                - id (str): Defect ID from CppCheck
                - summary (str): CppCheck's summary of the defect
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning

    Returns:
        The final state after the workflow completes
    """
    # Validate required fields
    required_fields = ['file', 'line', 'severity', 'id', 'summary']
    for field in required_fields:
        if field not in cppcheck_data:
            raise ValueError(f"Required field '{field}' is missing from CppCheck data")
    
    # Ensure line is an integer
    if not isinstance(cppcheck_data['line'], int):
        try:
            cppcheck_data['line'] = int(cppcheck_data['line'])
        except ValueError:
            raise ValueError(f"Line number must be an integer, got: {cppcheck_data['line']}")

    if debug:
        print(graph.get_graph(xray=True).draw_mermaid())
        print('='*100)
        enable_debug_logging()

    logger.info(f"Starting CppCheck analysis workflow for defect {cppcheck_data['id']} in {cppcheck_data['file']}:{cppcheck_data['line']}")
    
    # Format user message for the agent
    user_message = (
        f"Analyze the following potential code defect reported by CppCheck:\n\n"
        f"- File: {cppcheck_data['file']}\n"
        f"- Line: {cppcheck_data['line']}\n"
        f"- Severity: {cppcheck_data['severity']}\n"
        f"- ID: {cppcheck_data['id']}\n"
        f"- Summary: {cppcheck_data['summary']}\n\n"
        f"Please determine if this is a genuine defect or a false positive, explain the issue, "
        f"and provide a concise classification in your final JSON summary."
    )
    
    initial_state = {
        # Runtime Variables
        "messages": [{"role": "user", "content": user_message}],
        "auto_accepted_plan": True,
        "enable_background_investigation": enable_background_investigation,
        "locale": "en-US",  # Default locale
        
        # CppCheck specific fields
        "cppcheck_file": cppcheck_data['file'],
        "cppcheck_line": cppcheck_data['line'],
        "cppcheck_severity": cppcheck_data['severity'],
        "cppcheck_id": cppcheck_data['id'],
        "cppcheck_summary": cppcheck_data['summary'],
    }
    
    config = {
        "configurable": {
            "thread_id": "default",
            "max_plan_iterations": max_plan_iterations,
            "max_step_num": max_step_num,
            "mcp_settings": {
                "servers": {}  # No MCP servers needed for code analysis
            },
        },
        "recursion_limit": 100,
    }
    
    last_message_cnt = 0
    result_state = None
    
    async for s in graph.astream(
        input=initial_state, config=config, stream_mode="values"
    ):
        try:
            if isinstance(s, dict):
                result_state = s
                if "messages" in s:
                    if len(s["messages"]) <= last_message_cnt:
                        continue
                    last_message_cnt = len(s["messages"])
                    message = s["messages"][-1]
                    if isinstance(message, tuple):
                        print(message)
                    else:
                        message.pretty_print()
            else:
                # For any other output format
                print(f"Output: {s}")
        except Exception as e:
            logger.error(f"Error processing stream output: {e}")
            print(f"Error processing output: {str(e)}")

    logger.info("CppCheck analysis workflow completed successfully")
    return result_state


if __name__ == "__main__":
    print(graph.get_graph(xray=True).draw_mermaid())
