"""LangGraph state definition for resume builder"""
from typing import Literal, Optional, Annotated
from typing_extensions import TypedDict  # Changed from typing
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ResumeBuilderState(TypedDict):
    """State for the resume builder agent"""

    # User context
    user_id: str
    is_guest: bool  # Guest vs authenticated user

    # Conversation messages
    messages: Annotated[list[BaseMessage], add_messages]

    # Input validation (guard rails)
    input_valid: bool

    # Profile setup
    profile_complete: bool
    profile_data: Optional[dict]  # For guest users
    raw_input_text: Optional[str]
    
    # Job description
    job_description: Optional[str]
    job_analysis: Optional[dict]
    
    # Tailored content
    selected_experiences: Optional[list]
    selected_projects: Optional[list]
    prioritized_skills: Optional[dict]
    ats_score: Optional[float]
    matched_keywords: Optional[list]  # Keywords from ATS optimization
    
    # Output
    output_format: Literal["pdf", "latex"]
    latex_code: Optional[str]
    pdf_path: Optional[str]
    
    # Process control
    current_stage: Literal[
        "init",
        "initialized",
        "waiting_for_resume",
        "extracting_profile",
        "awaiting_profile_confirmation",
        "profile_confirmed",
        "waiting_for_job_description",
        "analyzing_job",
        "selecting_content",
        "optimizing_ats",
        "generating_resume",
        "complete",
        "error"
    ]
    needs_user_input: bool
    profile_needs_confirmation: Optional[bool]  # NEW: For human-in-the-loop