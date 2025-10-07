"""LangGraph workflow definition for Studio - SIMPLE LINEAR FLOW"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os
from .state import ResumeBuilderState
from .nodes import (
    validate_input,
    initialize_session,
    wait_for_resume,
    extract_profile,
    verify_profile,
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
    """Create the resume builder graph with guard rails and validation"""

    workflow = StateGraph(ResumeBuilderState)

    # Add all nodes
    workflow.add_node("validate_input", validate_input)  # Guard rail
    workflow.add_node("router", initialize_session)  # Renamed for clarity
    workflow.add_node("wait_for_resume", wait_for_resume)
    workflow.add_node("extract_profile", extract_profile)
    workflow.add_node("verify_profile", verify_profile)  # NEW: Profile verification
    workflow.add_node("wait_for_job_description", wait_for_job_description)
    workflow.add_node("analyze_job", analyze_job)
    workflow.add_node("select_content", select_content)
    workflow.add_node("optimize_ats", optimize_ats)
    workflow.add_node("generate_resume", generate_resume)

    # Entry point: validate input first
    workflow.set_entry_point("validate_input")

    # Validation routes to router if valid, END if off-topic
    def route_after_validation(state):
        if state.get("input_valid", True):  # Default to True for first run
            return "router"
        else:
            return END

    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "router": "router",
            END: END
        }
    )

    # Router decides where to go based on current stage and profile status
    def route_to_next_node(state):
        current_stage = state.get("current_stage", "init")
        profile_complete = state.get("profile_complete", False)
        messages = state.get("messages", [])

        # Helper: Check if current message contains resume data
        def message_contains_resume():
            if not messages:
                return False
            last_msg = messages[-1]
            content = last_msg.content if hasattr(last_msg, 'content') else ""
            # Check for resume indicators: substantial length + key phrases
            resume_indicators = ["here's my resume", "here is my resume", "my resume", "experience:", "education:", "skills:"]
            is_substantial = len(content) > 200  # Resume should be substantial
            has_indicators = any(indicator in content.lower() for indicator in resume_indicators)
            return is_substantial and has_indicators

        # If just initialized, check if they have profile OR if they sent resume data
        if current_stage == "initialized":
            if profile_complete:
                return "wait_for_job_description"
            elif message_contains_resume():
                # Skip wait_for_resume if they already sent it!
                print("DEBUG ROUTER: Resume detected in first message, extracting directly")
                return "extract_profile"
            else:
                return "wait_for_resume"

        # If waiting for resume, check if we got it (new message), then extract
        elif current_stage == "waiting_for_resume":
            return "extract_profile"

        # If awaiting profile confirmation, verify the profile
        elif current_stage == "awaiting_profile_confirmation":
            return "verify_profile"

        # If profile confirmed, proceed to job description
        elif current_stage == "profile_confirmed":
            return "wait_for_job_description"

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
            "verify_profile": "verify_profile",
            "analyze_job": "analyze_job"
        }
    )

    # Wait nodes END the graph (pause for user input)
    workflow.add_edge("wait_for_resume", END)
    workflow.add_edge("wait_for_job_description", END)
    workflow.add_edge("extract_profile", END)  # Pause after extraction for user review

    # Profile verification routing
    def route_after_verification(state):
        """Route from verify_profile based on confirmation status"""
        if state.get("profile_needs_confirmation"):
            return END  # Still needs confirmation, pause for user
        else:
            return "wait_for_job_description"  # Confirmed, proceed

    workflow.add_conditional_edges(
        "verify_profile",
        route_after_verification,
        {
            END: END,
            "wait_for_job_description": "wait_for_job_description"
        }
    )

    # Processing flows
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


# Export a function that creates a fresh graph to avoid caching issues
def get_graph():
    """Get a fresh graph instance with latest node implementations"""
    return create_graph()

# Create default graph instance
graph = create_graph()
