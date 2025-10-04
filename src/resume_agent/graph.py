"""LangGraph workflow definition for Studio - SIMPLE LINEAR FLOW"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os
from .state import ResumeBuilderState
from .nodes import (
    initialize_session,
    wait_for_resume,
    extract_profile,
    wait_for_job_description,
    analyze_job,
    select_content,
    optimize_ats,
    generate_resume
)

# Create persistent SQLite connection and checkpointer ONLY for standalone mode
# When running in LangGraph Studio/API, persistence is handled by the platform
USE_CUSTOM_CHECKPOINTER = os.getenv("LANGGRAPH_USE_CUSTOM_CHECKPOINTER", "false").lower() == "true"

if USE_CUSTOM_CHECKPOINTER:
    conn = sqlite3.connect("resume_builder_checkpoints.db", check_same_thread=False)
    memory = SqliteSaver(conn)
else:
    memory = None


def create_graph():
    """Create the resume builder graph with simple linear flow"""

    workflow = StateGraph(ResumeBuilderState)

    # Add all nodes
    workflow.add_node("router", initialize_session)  # Renamed for clarity
    workflow.add_node("wait_for_resume", wait_for_resume)
    workflow.add_node("extract_profile", extract_profile)
    workflow.add_node("wait_for_job_description", wait_for_job_description)
    workflow.add_node("analyze_job", analyze_job)
    workflow.add_node("select_content", select_content)
    workflow.add_node("optimize_ats", optimize_ats)
    workflow.add_node("generate_resume", generate_resume)

    # Entry point routes based on current state
    workflow.set_entry_point("router")

    # Router decides where to go based on current stage and profile status
    def route_to_next_node(state):
        current_stage = state.get("current_stage", "init")
        profile_complete = state.get("profile_complete", False)

        # If just initialized, check if they have profile
        if current_stage == "initialized":
            if profile_complete:
                return "wait_for_job_description"
            else:
                return "wait_for_resume"

        # If waiting for resume, check if we got it (new message), then extract
        elif current_stage == "waiting_for_resume":
            return "extract_profile"

        # If waiting for JD, check if we got it, then analyze
        elif current_stage == "waiting_for_job_description":
            return "analyze_job"

        # Default fallback
        return "wait_for_resume"

    workflow.add_conditional_edges(
        "router",
        route_to_next_node,
        {
            "wait_for_resume": "wait_for_resume",
            "wait_for_job_description": "wait_for_job_description",
            "extract_profile": "extract_profile",
            "analyze_job": "analyze_job"
        }
    )

    # Wait nodes END the graph (pause for user input)
    workflow.add_edge("wait_for_resume", END)
    workflow.add_edge("wait_for_job_description", END)

    # Processing flows
    workflow.add_edge("extract_profile", "wait_for_job_description")
    workflow.add_edge("analyze_job", "select_content")
    workflow.add_edge("select_content", "optimize_ats")
    workflow.add_edge("optimize_ats", "generate_resume")
    workflow.add_edge("generate_resume", END)

    # Compile with checkpointing only for standalone mode
    # In LangGraph Studio/API, persistence is provided by the platform
    if memory is not None:
        graph = workflow.compile(checkpointer=memory)
    else:
        graph = workflow.compile()

    return graph


graph = create_graph()