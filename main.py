# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Entry point script for the DeerFlow project.
"""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any, Optional

from InquirerPy import inquirer

from src.config.questions import BUILT_IN_QUESTIONS, BUILT_IN_QUESTIONS_ZH_CN
from src.workflow import run_agent_workflow_async, run_cppcheck_analysis_async


def ask(
    question,
    debug=False,
    max_plan_iterations=1,
    max_step_num=3,
    enable_background_investigation=True,
):
    """Run the agent workflow with the given question.

    Args:
        question: The user's query or request
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning to enhance context
    """
    asyncio.run(
        run_agent_workflow_async(
            user_input=question,
            debug=debug,
            max_plan_iterations=max_plan_iterations,
            max_step_num=max_step_num,
            enable_background_investigation=enable_background_investigation,
        )
    )


def analyze_cppcheck(
    cppcheck_data: Dict[str, Any],
    debug=False,
    max_plan_iterations=1,
    max_step_num=3,
    enable_background_investigation=False,
):
    """Run the defect analysis workflow with CppCheck input.

    Args:
        cppcheck_data: Dictionary containing CppCheck defect information
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
        enable_background_investigation: If True, performs web search before planning
    """
    return asyncio.run(
        run_cppcheck_analysis_async(
            cppcheck_data=cppcheck_data,
            debug=debug,
            max_plan_iterations=max_plan_iterations,
            max_step_num=max_step_num,
            enable_background_investigation=enable_background_investigation,
        )
    )


def main(
    debug=False,
    max_plan_iterations=1,
    max_step_num=3,
    enable_background_investigation=True,
):
    """Interactive mode with built-in questions.

    Args:
        enable_background_investigation: If True, performs web search before planning to enhance context
        debug: If True, enables debug level logging
        max_plan_iterations: Maximum number of plan iterations
        max_step_num: Maximum number of steps in a plan
    """
    # First select language
    language = inquirer.select(
        message="Select language / 选择语言:",
        choices=["English", "中文"],
    ).execute()

    # Choose questions based on language
    questions = (
        BUILT_IN_QUESTIONS if language == "English" else BUILT_IN_QUESTIONS_ZH_CN
    )
    ask_own_option = (
        "[Ask my own question]" if language == "English" else "[自定义问题]"
    )

    # Select a question
    initial_question = inquirer.select(
        message=(
            "What do you want to know?" if language == "English" else "您想了解什么?"
        ),
        choices=[ask_own_option] + questions,
    ).execute()

    if initial_question == ask_own_option:
        initial_question = inquirer.text(
            message=(
                "What do you want to know?"
                if language == "English"
                else "您想了解什么?"
            ),
        ).execute()

    # Pass all parameters to ask function
    ask(
        question=initial_question,
        debug=debug,
        max_plan_iterations=max_plan_iterations,
        max_step_num=max_step_num,
        enable_background_investigation=enable_background_investigation,
    )


def parse_cppcheck_args(args):
    """Parse command-line arguments for CppCheck mode."""
    if args.cppcheck_json:
        try:
            # Load JSON from file
            with open(args.cppcheck_json, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading CppCheck JSON file: {e}")
            sys.exit(1)
    elif args.cppcheck_inline_csv:
        try:
            # Parse inline CSV string
            file, line, severity, id_, summary = args.cppcheck_inline_csv.split(',', 5)
            return {
                'file': file,
                'line': line,
                'severity': severity,
                'id': id_,
                'summary': summary
            }
        except Exception as e:
            print(f"Error parsing inline CppCheck CSV: {e}")
            sys.exit(1)
    elif args.cppcheck_inline:
        try:
            # Parse inline JSON string
            return json.loads(args.cppcheck_inline)
        except json.JSONDecodeError as e:
            print(f"Error parsing inline CppCheck JSON: {e}")
            sys.exit(1)
    else:
        # Construct from individual arguments
        cppcheck_data = {
            'file': args.file,
            'line': args.line,
            'severity': args.severity,
            'id': args.id,
            'summary': args.summary
        }
        # Validate required fields
        missing_fields = [k for k, v in cppcheck_data.items() if v is None]
        if missing_fields:
            print(f"Error: Missing required CppCheck fields: {', '.join(missing_fields)}")
            print("Please provide all required fields either individually or via JSON.")
            sys.exit(1)
        return cppcheck_data


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Code-Flow: AI-based Code Analysis")
    
    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    
    # Regular mode (original)
    regular_parser = subparsers.add_parser("query", help="Process a general query")
    regular_parser.add_argument("query", nargs="*", help="The query to process")
    regular_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode with built-in questions",
    )
    
    # CppCheck analysis mode
    cppcheck_parser = subparsers.add_parser("cppcheck", help="Analyze a CppCheck defect report")
    
    # Three ways to provide CppCheck data
    cppcheck_group = cppcheck_parser.add_mutually_exclusive_group(required=True)
    cppcheck_group.add_argument("--cppcheck-json", help="Path to JSON file containing CppCheck data")
    cppcheck_group.add_argument("--cppcheck-inline-csv", help="Inline CSV string containing CppCheck data")
    cppcheck_group.add_argument("--cppcheck-inline", help="Inline JSON string containing CppCheck data")
    
    # Individual CppCheck fields (alternative to JSON)
    cppcheck_group.add_argument("--file", help="Path to the file with the defect")
    cppcheck_parser.add_argument("--line", type=int, help="Line number of the defect")
    cppcheck_parser.add_argument("--severity", help="Severity of the defect")
    cppcheck_parser.add_argument("--id", help="Defect ID from CppCheck")
    cppcheck_parser.add_argument("--summary", help="CppCheck's summary of the defect")
    
    # Common arguments for all modes
    for subparser in [regular_parser, cppcheck_parser]:
        subparser.add_argument(
            "--max_plan_iterations",
            type=int,
            default=1,
            help="Maximum number of plan iterations (default: 1)",
        )
        subparser.add_argument(
            "--max_step_num",
            type=int,
            default=3,
            help="Maximum number of steps in a plan (default: 3)",
        )
        subparser.add_argument("--debug", action="store_true", help="Enable debug logging")
        subparser.add_argument(
            "--no-background-investigation",
            action="store_false",
            dest="enable_background_investigation",
            help="Disable background investigation before planning",
        )
    
    args = parser.parse_args()
    
    # Default to query mode if no mode specified
    if not args.mode:
        args.mode = "query"
        args.query = []
        
    if args.mode == "query":
        if args.interactive:
            # Pass command line arguments to main function
            main(
                debug=args.debug,
                max_plan_iterations=args.max_plan_iterations,
                max_step_num=args.max_step_num,
                enable_background_investigation=args.enable_background_investigation,
            )
        else:
            # Parse user input from command line arguments or user input
            if hasattr(args, 'query') and args.query:
                user_query = " ".join(args.query)
            else:
                user_query = input("Enter your query: ")

            # Run the agent workflow with the provided parameters
            ask(
                question=user_query,
                debug=args.debug,
                max_plan_iterations=args.max_plan_iterations,
                max_step_num=args.max_step_num,
                enable_background_investigation=args.enable_background_investigation,
            )
    elif args.mode == "cppcheck":
        # Parse CppCheck arguments and run analysis
        cppcheck_data = parse_cppcheck_args(args)
        result = analyze_cppcheck(
            cppcheck_data=cppcheck_data,
            debug=args.debug,
            max_plan_iterations=args.max_plan_iterations,
            max_step_num=args.max_step_num,
            enable_background_investigation=args.enable_background_investigation,
        )
        
        # Extract and print the final JSON summary if available
        final_message = result.get("messages", [])[-1] if result else None
        if final_message and hasattr(final_message, "content"):
            content = final_message.content
            # Try to extract the JSON summary
            try:
                # Look for JSON-like structure in the markdown report
                import re
                json_match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
                if json_match:
                    json_summary = json.loads(json_match.group(1))
                    print("\nJSON Summary:")
                    print(json.dumps(json_summary, indent=2))
            except Exception as e:
                print(f"Error extracting JSON summary: {e}")
                # Just print the full content if we can't extract the JSON
                print("\nFull Analysis Report:")
                print(content)
