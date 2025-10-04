"""LangGraph state definition for resume builder"""
from typing import Literal, Optional, Annotated
from typing_extensions import TypedDict  # Changed from typing
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ResumeBuilderState(TypedDict):
    """State for the resume builder agent"""
    
    # User context
    user_id: str
    
    # Conversation messages
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Profile setup
    profile_complete: bool
    raw_input_text: Optional[str]
    
    # Job description
    job_description: Optional[str]
    job_analysis: Optional[dict]
    
    # Tailored content
    selected_experiences: Optional[list]
    selected_projects: Optional[list]
    prioritized_skills: Optional[dict]
    ats_score: Optional[float]
    
    # Output
    output_format: Literal["pdf", "latex"]
    latex_code: Optional[str]
    pdf_path: Optional[str]
    
    # Process control
    current_stage: Literal[
        "init",
        "profile_check",
        "profile_input",
        "profile_extraction",
        "job_input",
        "job_analysis",
        "content_selection",
        "ats_optimization",
        "latex_generation",
        "pdf_compilation",
        "complete"
    ]
    needs_user_input: bool
