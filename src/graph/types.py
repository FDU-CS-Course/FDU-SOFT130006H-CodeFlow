# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import operator
from typing import Annotated

from langgraph.graph import MessagesState

from src.prompts.planner_model import Plan


class State(MessagesState):
    """State for the agent system, extends MessagesState with next field."""

    # Runtime Variables
    locale: str = "en-US"
    observations: list[str] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None

    # CppCheck Input
    cppcheck_file: str | None = None
    cppcheck_line: int | None = None
    cppcheck_severity: str | None = None
    cppcheck_id: str | None = None
    cppcheck_summary: str | None = None

    # Context for Planner
    source_code_context: str | None = None
    directory_tree: str | None = None
