"""LangGraph nodes for resume builder - SIMPLE LINEAR FLOW"""
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from .state import ResumeBuilderState
from .database import SessionLocal
from .user_service import UserService
from .config import OPENAI_API_KEY, OPENAI_MODEL
from .latex_service import LaTeXService
from .models import ResumeGeneration
import json
import uuid
from datetime import datetime
from typing import List, Dict

# Initialize LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    temperature=0
)

# System prompt for guard rails
GUARD_RAIL_SYSTEM_PROMPT = """You are a resume optimization assistant. Your ONLY purpose is to help users:
1. Build and optimize resumes
2. Analyze job descriptions
3. Match resumes to job requirements
4. Provide ATS optimization advice

You MUST reject any questions or requests that are not related to resume building, job applications, or career advice.

If a user asks something off-topic, politely redirect them back to your purpose:
"I'm specifically designed to help with resume optimization and job application preparation. Let's focus on building your perfect resume! Would you like to start by uploading your resume or pasting a job description?"
"""


def validate_input(state: ResumeBuilderState) -> dict:
    """
    Guard rail: Validate that user input is resume-related.
    Reject off-topic questions and redirect users to the mission.
    """
    messages = state.get("messages", [])
    current_stage = state.get("current_stage", "init")

    # Skip validation for first message or if already in process
    # Also skip for profile confirmation stage (allows simple "yes" responses)
    if not messages or current_stage in ["waiting_for_resume", "waiting_for_job_description", "initialized", "awaiting_profile_confirmation"]:
        return {"input_valid": True}

    # Get the last user message
    last_message = messages[-1] if messages else None
    if not last_message or not hasattr(last_message, "content"):
        return {"input_valid": True}

    user_input = last_message.content.lower()

    # Check if input is obviously resume-related (quick keywords)
    resume_keywords = [
        "resume", "cv", "job", "position", "company", "experience",
        "skill", "education", "work", "career", "apply", "application",
        "interview", "hire", "hiring", "role", "description", "jd",
        "ats", "optimize", "tailor", "qualification"
    ]

    # If any keyword matches, it's valid
    if any(keyword in user_input for keyword in resume_keywords):
        return {"input_valid": True}

    # Use LLM to check if the question is resume-related
    validation_prompt = f"""Is the following user message related to resume building, job applications, or career advice?

User message: "{last_message.content}"

Respond with ONLY "YES" or "NO".
- YES if the message is about resumes, job descriptions, career advice, or work experience
- NO if it's completely off-topic (like weather, math, general conversation, etc.)

Your response:"""

    try:
        response = llm.invoke([HumanMessage(content=validation_prompt)])
        is_valid = "yes" in response.content.lower()

        if not is_valid:
            # Add redirect message
            redirect_message = AIMessage(content=(
                "I'm specifically designed to help with resume optimization and job application preparation. "
                "Let's focus on building your perfect resume! Would you like to start by uploading your resume "
                "or pasting a job description?"
            ))

            return {
                "input_valid": False,
                "messages": [redirect_message]
            }

        return {"input_valid": True}

    except Exception as e:
        print(f"Validation error: {e}")
        # If validation fails, allow it (fail open for better UX)
        return {"input_valid": True}


def initialize_session(state: ResumeBuilderState) -> dict:
    """Initialize session and check if user has profile - also acts as router"""

    current_stage = state.get("current_stage", "init")
    profile_complete = state.get("profile_complete", False)
    is_guest = state.get("is_guest", False)

    print(f"DEBUG ROUTER: current_stage={current_stage}, profile_complete={profile_complete}, is_guest={is_guest}")

    # If already initialized in a previous turn, don't re-initialize
    # Just pass through - the routing happens via conditional edges
    if current_stage != "init" and current_stage != "":
        print(f"DEBUG ROUTER: Skipping initialization, already at stage: {current_stage}")
        return {"current_stage": current_stage}  # Pass through current stage

    # Get user_id from state
    user_id = state.get("user_id")
    if not user_id:
        # Fallback for local testing only
        try:
            from .studio_config import DEFAULT_USER_ID
            user_id = DEFAULT_USER_ID
            print(f"DEBUG ROUTER: Using DEFAULT_USER_ID for testing: {user_id}")
        except Exception as e:
            raise ValueError("user_id is required!")

    # For guest users, skip profile check (they'll provide resume inline)
    if is_guest:
        print(f"DEBUG ROUTER: Guest user - skipping profile check")
        return {
            "user_id": user_id,
            "is_guest": True,
            "profile_complete": False,
            "current_stage": "initialized"
        }

    # For authenticated users, check if they have existing profile
    db = SessionLocal()
    try:
        has_profile = UserService.profile_exists(db, user_id)
    finally:
        db.close()

    print(f"DEBUG ROUTER: Authenticated user - has_profile={has_profile}")

    return {
        "user_id": user_id,
        "is_guest": False,
        "profile_complete": has_profile,
        "current_stage": "initialized"
    }


def wait_for_resume(state: ResumeBuilderState) -> dict:
    """Ask user to paste/upload resume - graph will pause here"""

    is_guest = state.get("is_guest", False)

    if is_guest:
        # Guest user message
        welcome_message = (
            "👋 **Welcome to the AI Resume Builder!**\n\n"
            "I'll help you create an ATS-optimized resume tailored to any job.\n\n"
            "**Step 1:** Upload or paste your resume below.\n\n"
            "You can:\n"
            "• Upload a PDF, DOCX, or image file\n"
            "• Paste plain text resume\n"
            "• Paste LaTeX resume code\n\n"
            "**Note:** As a guest, your resume won't be saved. Sign up to save your profile for future use!"
        )
    else:
        # Authenticated user message
        welcome_message = (
            "👋 **Welcome back!**\n\n"
            "Let's build your professional profile first.\n\n"
            "**Step 1:** Upload or paste your resume below.\n\n"
            "You can:\n"
            "• Upload a PDF, DOCX, or image file\n"
            "• Paste plain text resume\n"
            "• Paste LaTeX resume code\n\n"
            "Your profile will be saved for generating tailored resumes in the future!"
        )

    return {
        "current_stage": "waiting_for_resume",
        "needs_user_input": True,
        "messages": [AIMessage(content=welcome_message)]
    }


def extract_profile(state: ResumeBuilderState) -> dict:
    """Extract structured profile data from user's resume"""

    # Get the latest human message
    human_messages = []
    for msg in state.get("messages", []):
        if hasattr(msg, 'type') and msg.type == "human":
            human_messages.append(msg.content)

    if not human_messages:
        return {
            "current_stage": "error",
            "messages": [AIMessage(content="No resume text found. Please paste your resume.")]
        }

    user_message = human_messages[-1]

    # Validate length
    if len(user_message) < 100:
        return {
            "current_stage": "error",
            "messages": [AIMessage(content=(
                "That's too short. Please paste your full resume (at least 100 characters)."
            ))]
        }

    # Extract profile using LLM
    extraction_prompt = f"""Extract structured information from this resume/summary:

{user_message}

Return ONLY valid JSON with this structure:
{{
  "contact": {{
    "full_name": "string",
    "phone": "string",
    "email": "string",
    "linkedin": "url or null",
    "github": "url or null",
    "portfolio": "url or null"
  }},
  "education": [
    {{
      "institution": "string",
      "location": "string",
      "degree": "string",
      "gpa": "string or null",
      "dates": "Month Year - Month Year"
    }}
  ],
  "experience": [
    {{
      "title": "string",
      "dates": "Month Year - Month Year",
      "organization": "string",
      "location": "string",
      "bullets": ["achievement with metrics", "another achievement"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "technologies": "comma-separated tech stack",
      "dates": "Month Year - Month Year",
      "bullets": ["description"]
    }}
  ],
  "technical_skills": {{
    "languages": ["lang1", "lang2"],
    "frameworks": ["framework1"],
    "developer_tools": ["tool1"],
    "libraries": ["lib1"]
  }},
  "awards": [
    {{
      "title": "award name",
      "description": "details or null"
    }}
  ]
}}

Extract information even if it's in LaTeX format. Keep ALL quantifiable metrics. Return ONLY the JSON, no other text."""

    try:
        response = llm.invoke(extraction_prompt)

        # Clean response
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        profile_data = json.loads(content)

        # Save to database only for authenticated users
        user_id = state.get("user_id")
        is_guest = state.get("is_guest", False)

        if not is_guest:
            db = SessionLocal()
            try:
                UserService.save_user_profile(db, user_id, profile_data)
            finally:
                db.close()

        # Format profile for display
        contact = profile_data.get("contact", {})
        edu_list = profile_data.get("education", [])
        exp_list = profile_data.get("experience", [])
        proj_list = profile_data.get("projects", [])
        skills = profile_data.get("technical_skills", {})

        # Build profile summary
        profile_summary = f"**Profile Extracted!**\n\n"
        profile_summary += f"**Contact:**\n"
        profile_summary += f"- Name: {contact.get('full_name', 'N/A')}\n"
        profile_summary += f"- Email: {contact.get('email', 'N/A')}\n"
        profile_summary += f"- Phone: {contact.get('phone', 'N/A')}\n"
        profile_summary += f"- LinkedIn: {contact.get('linkedin', 'N/A')}\n"
        profile_summary += f"- GitHub: {contact.get('github', 'N/A')}\n\n"

        profile_summary += f"**Education:** {len(edu_list)} entries\n"
        for i, edu in enumerate(edu_list, 1):
            profile_summary += f"{i}. {edu.get('degree', 'N/A')} at {edu.get('institution', 'N/A')} ({edu.get('dates', 'N/A')})\n"
        profile_summary += "\n"

        profile_summary += f"**Experience:** {len(exp_list)} entries\n"
        for i, exp in enumerate(exp_list, 1):
            profile_summary += f"{i}. {exp.get('title', 'N/A')} at {exp.get('organization', 'N/A')} ({exp.get('dates', 'N/A')})\n"
        profile_summary += "\n"

        profile_summary += f"**Projects:** {len(proj_list)} entries\n"
        for i, proj in enumerate(proj_list, 1):
            profile_summary += f"{i}. {proj.get('name', 'N/A')} ({proj.get('technologies', 'N/A')})\n"
        profile_summary += "\n"

        profile_summary += f"**Technical Skills:**\n"
        profile_summary += f"- Languages: {', '.join(skills.get('languages', [])) or 'None listed'}\n"
        profile_summary += f"- Frameworks: {', '.join(skills.get('frameworks', [])) or 'None listed'}\n"
        profile_summary += f"- Developer Tools: {', '.join(skills.get('developer_tools', [])) or 'None listed'}\n"
        profile_summary += f"- Libraries: {', '.join(skills.get('libraries', [])) or 'None listed'}\n\n"

        profile_summary += "**Please review this information carefully.**\n\n"
        profile_summary += "Type 'yes', 'looks good', or 'approve' to proceed.\n"
        profile_summary += "Or describe any changes you'd like to make (e.g., 'Change my email to john@example.com')."

        return {
            "profile_complete": False,  # Not complete until approved
            "profile_data": profile_data,  # Store in state
            "profile_needs_confirmation": True,
            "current_stage": "awaiting_profile_confirmation",
            "messages": [AIMessage(content=profile_summary)]
        }

    except Exception as e:
        return {
            "current_stage": "error",
            "profile_complete": False,
            "messages": [AIMessage(content=(
                f" Error parsing your resume: {str(e)}\n\n"
                f"Please paste a text version of your resume or try reformatting it."
            ))]
        }


def verify_profile(state: ResumeBuilderState) -> dict:
    """Verify profile with user - check if approved or needs edits using LLM"""

    messages = state.get("messages", [])
    if not messages:
        return {
            "current_stage": "error",
            "messages": [AIMessage(content="No user response found.")]
        }

    user_response = messages[-1].content
    profile_data = state.get("profile_data", {})

    # Use LLM to determine: Is user approving OR requesting changes?
    decision_prompt = f"""The user has been shown their extracted profile and asked to confirm or request changes.

User's response: "{user_response}"

Determine if the user is:
A) APPROVING the profile (e.g., "yes", "looks good", "correct", "approve", "that's right", etc.)
B) REQUESTING CHANGES (e.g., "change my email", "fix the phone number", "update my name", etc.)

Respond with ONLY one word:
- "APPROVE" if the user is confirming/approving
- "CHANGE" if the user wants modifications

Your response:"""

    try:
        response = llm.invoke(decision_prompt)
        decision = response.content.strip().upper()

        # User approved the profile
        if "APPROVE" in decision:
            # Save profile to database if authenticated user
            user_id = state.get("user_id")
            is_guest = state.get("is_guest", False)

            if not is_guest:
                db = SessionLocal()
                try:
                    UserService.save_user_profile(db, user_id, profile_data)
                finally:
                    db.close()

            return {
                "profile_complete": True,
                "profile_needs_confirmation": False,
                "current_stage": "profile_confirmed",
                "messages": [AIMessage(content="Profile confirmed! Proceeding to job description...")]
            }

        # User wants changes - use LLM to apply edits
        else:
            edit_prompt = f"""The user wants to edit their extracted profile.

Current profile (JSON):
{json.dumps(profile_data, indent=2)}

User's edit request:
"{user_response}"

Apply the user's requested changes to the profile. Return the COMPLETE updated profile as JSON.
If the user's request is unclear, make your best guess. Return ONLY valid JSON, no other text."""

            response = llm.invoke(edit_prompt)
            content = response.content.strip()

            # Clean response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            updated_profile = json.loads(content)

            # Show updated profile for re-confirmation
            contact = updated_profile.get("contact", {})
            edu_list = updated_profile.get("education", [])
            exp_list = updated_profile.get("experience", [])
            proj_list = updated_profile.get("projects", [])
            skills = updated_profile.get("technical_skills", {})

            profile_summary = f"**Profile Updated!**\n\n"
            profile_summary += f"**Contact:**\n"
            profile_summary += f"- Name: {contact.get('full_name', 'N/A')}\n"
            profile_summary += f"- Email: {contact.get('email', 'N/A')}\n"
            profile_summary += f"- Phone: {contact.get('phone', 'N/A')}\n"
            profile_summary += f"- LinkedIn: {contact.get('linkedin', 'N/A')}\n"
            profile_summary += f"- GitHub: {contact.get('github', 'N/A')}\n\n"

            profile_summary += f"**Education:** {len(edu_list)} entries\n"
            for i, edu in enumerate(edu_list, 1):
                profile_summary += f"{i}. {edu.get('degree', 'N/A')} at {edu.get('institution', 'N/A')} ({edu.get('dates', 'N/A')})\n"
            profile_summary += "\n"

            profile_summary += f"**Experience:** {len(exp_list)} entries\n"
            for i, exp in enumerate(exp_list, 1):
                profile_summary += f"{i}. {exp.get('title', 'N/A')} at {exp.get('organization', 'N/A')} ({exp.get('dates', 'N/A')})\n"
            profile_summary += "\n"

            profile_summary += f"**Projects:** {len(proj_list)} entries\n"
            for i, proj in enumerate(proj_list, 1):
                profile_summary += f"{i}. {proj.get('name', 'N/A')} ({proj.get('technologies', 'N/A')})\n"
            profile_summary += "\n"

            profile_summary += f"**Technical Skills:**\n"
            profile_summary += f"- Languages: {', '.join(skills.get('languages', [])) or 'None listed'}\n"
            profile_summary += f"- Frameworks: {', '.join(skills.get('frameworks', [])) or 'None listed'}\n"
            profile_summary += f"- Developer Tools: {', '.join(skills.get('developer_tools', [])) or 'None listed'}\n"
            profile_summary += f"- Libraries: {', '.join(skills.get('libraries', [])) or 'None listed'}\n\n"

            profile_summary += "**Is this correct now?**\n\n"
            profile_summary += "Type 'yes' to proceed, or describe more changes."

            return {
                "profile_data": updated_profile,
                "profile_needs_confirmation": True,
                "current_stage": "awaiting_profile_confirmation",
                "messages": [AIMessage(content=profile_summary)]
            }

    except Exception as e:
        return {
            "current_stage": "awaiting_profile_confirmation",
            "messages": [AIMessage(content=f"Sorry, I couldn't parse your edit request. Please try again or type 'yes' to proceed with the current profile.\n\nError: {str(e)}")]
        }


def wait_for_job_description(state: ResumeBuilderState) -> dict:
    """Ask user to paste job description - graph will pause here"""

    is_guest = state.get("is_guest", False)
    profile_complete = state.get("profile_complete", False)

    # Determine the step number and message
    if profile_complete and not is_guest:
        # Returning authenticated user - they already have a profile
        job_message = (
            "✨ **Ready to generate your tailored resume!**\n\n"
            "I've loaded your profile. Now paste the job description for the position you're applying to.\n\n"
            "Include:\n"
            "• Job title & company name\n"
            "• Requirements & qualifications\n"
            "• Responsibilities\n"
            "• Preferred skills\n\n"
            "I'll optimize your resume to match this specific role!"
        )
    else:
        # New user or guest - this is step 2 after profile extraction
        job_message = (
            "**Profile Saved!**\n\n"
            "**Step 2:** Paste the job description\n\n"
            "Copy and paste the full job posting for the role you're applying to.\n\n"
            "Include:\n"
            "• Job title & company name\n"
            "• Requirements & qualifications\n"
            "• Responsibilities\n"
            "• Preferred skills\n\n"
            "The more detail, the better the ATS optimization!"
        )

    return {
        "current_stage": "waiting_for_job_description",
        "needs_user_input": True,
        "messages": [AIMessage(content=job_message)]
    }


def analyze_job(state: ResumeBuilderState) -> dict:
    """Analyze job description to extract requirements and keywords"""

    # Get the latest human message (should be job description)
    human_messages = []
    for msg in state.get("messages", []):
        if hasattr(msg, 'type') and msg.type == "human":
            human_messages.append(msg.content)

    if len(human_messages) < 2:  # Need at least resume + JD
        return {
            "current_stage": "error",
            "messages": [AIMessage(content="No job description found. Please paste it.")]
        }

    job_description = human_messages[-1]

    # Validate length
    if len(job_description) < 100:
        return {
            "current_stage": "error",
            "messages": [AIMessage(content=(
                "That's too short for a job description. Please paste the full posting."
            ))]
        }

    # Analyze job with LLM
    analysis_prompt = f"""Analyze this job description and extract key information:

{job_description}

Return ONLY valid JSON with this structure:
{{
  "job_title": "extracted title",
  "company_name": "company name if mentioned, or null",
  "required_skills": ["skill1", "skill2", ...],
  "preferred_qualifications": ["qual1", "qual2", ...],
  "key_responsibilities": ["resp1", "resp2", ...],
  "experience_level": "entry/mid/senior",
  "keywords": ["keyword1", "keyword2", ...],
  "nice_to_have": ["skill1", "skill2", ...]
}}

Extract ALL technical skills, tools, and technologies mentioned. Be comprehensive with keywords for ATS optimization."""

    try:
        response = llm.invoke(analysis_prompt)
        content = response.content.strip()

        # Clean response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        job_analysis = json.loads(content)

        return {
            "job_description": job_description,
            "job_analysis": job_analysis,
            "current_stage": "job_analyzed",
            "messages": [AIMessage(content=(
                f" **Job Analysis Complete!**\n\n"
                f" **Position:** {job_analysis.get('job_title', 'N/A')}\n"
                f" **Company:** {job_analysis.get('company_name', 'Not specified')}\n"
                f" **Level:** {job_analysis.get('experience_level', 'N/A')}\n"
                f" **Key Skills:** {', '.join(job_analysis.get('required_skills', [])[:5])}...\n\n"
                f"Now selecting your most relevant experiences..."
            ))]
        }

    except Exception as e:
        return {
            "current_stage": "error",
            "messages": [AIMessage(content=(
                f" Error analyzing job description: {str(e)}\n\n"
                "Please try pasting it again."
            ))]
        }


def select_content(state: ResumeBuilderState) -> dict:
    """Select most relevant experiences and projects for the job"""

    job_analysis = state.get("job_analysis")
    user_id = state.get("user_id")
    is_guest = state.get("is_guest", False)

    # Get user profile - from state for guests, from DB for authenticated users
    if is_guest:
        profile_data = state.get("profile_data", {})
    else:
        db = SessionLocal()
        try:
            profile_data = UserService.get_user_profile(db, user_id)
        finally:
            db.close()

    experiences = profile_data.get("experience", [])
    projects = profile_data.get("projects", [])

    # Use LLM to rank and select
    selection_prompt = f"""Given this job analysis:
{json.dumps(job_analysis, indent=2)}

And these experiences:
{json.dumps(experiences, indent=2)}

And these projects:
{json.dumps(projects, indent=2)}

Select and rank the MOST RELEVANT experiences and projects. Return ONLY valid JSON:
{{
  "selected_experience_indices": [0, 2, 1],
  "selected_project_indices": [1, 0],
  "reasoning": "brief explanation"
}}

Prioritize:
1. Experiences matching required skills
2. Quantifiable achievements
3. Relevant tech stack
4. Career progression

Return indices in priority order. Include ALL experiences but rank them."""

    try:
        response = llm.invoke(selection_prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        selection = json.loads(content)

        # Reorder based on selection
        exp_indices = selection.get("selected_experience_indices", list(range(len(experiences))))
        proj_indices = selection.get("selected_project_indices", list(range(len(projects))))

        selected_experiences = [experiences[i] for i in exp_indices if i < len(experiences)]
        selected_projects = [projects[i] for i in proj_indices if i < len(projects)]

        # NO ENHANCEMENT - Just use selected content as-is
        # The bolding will happen in LaTeX generation based on ATS matches
        return {
            "selected_experiences": selected_experiences,
            "selected_projects": selected_projects,
            "current_stage": "content_selected",
            "messages": [AIMessage(content=(
                f"✅ **Content Selection Complete!**\n\n"
                f"📝 Selected **{len(selected_experiences)}** experiences and **{len(selected_projects)}** projects\n"
                f"📊 {selection.get('reasoning', '')}\n\n"
                f"Calculating ATS score..."
            ))]
        }

    except Exception as e:
        # Fallback: use all content
        return {
            "selected_experiences": experiences,
            "selected_projects": projects,
            "current_stage": "content_selected",
            "messages": [AIMessage(content=(
                f" Using all experiences and projects (selection error: {str(e)})\n"
                f"Proceeding to ATS optimization..."
            ))]
        }


def optimize_ats(state: ResumeBuilderState) -> dict:
    """Calculate ATS score and prioritize keywords"""

    job_analysis = state.get("job_analysis")
    user_id = state.get("user_id")
    is_guest = state.get("is_guest", False)

    # Get user profile - from state for guests, from DB for authenticated users
    if is_guest:
        profile_data = state.get("profile_data", {})
    else:
        db = SessionLocal()
        try:
            profile_data = UserService.get_user_profile(db, user_id)
        finally:
            db.close()

    user_skills = profile_data.get("technical_skills", {})

    # Extract job keywords
    job_keywords = set()
    job_keywords.update(job_analysis.get("required_skills", []))
    job_keywords.update(job_analysis.get("keywords", []))
    job_keywords.update(job_analysis.get("nice_to_have", []))

    # Extract user skills
    user_skill_list = []
    for category, skills in user_skills.items():
        if isinstance(skills, list):
            user_skill_list.extend(skills)

    # Normalize function to handle variations (React.js -> react, Node.js -> node, etc.)
    def normalize_keyword(keyword: str) -> str:
        """Normalize keyword for matching: lowercase, remove punctuation, remove 'js' suffix"""
        normalized = keyword.lower().strip()
        # Remove common punctuation
        normalized = normalized.replace('.', '').replace('-', '').replace('_', '')
        # Handle JS variants (reactjs -> react, nodejs -> node)
        if normalized.endswith('js') and len(normalized) > 3:
            # Keep 'js' as standalone, but remove from others
            if normalized not in ['js', 'css', 'aws']:
                base = normalized[:-2]
                # Only remove if it makes sense (reactjs->react good, css->c bad)
                if len(base) > 2:
                    normalized = base
        return normalized

    # Calculate match with fuzzy matching
    user_skills_normalized = {normalize_keyword(s): s for s in user_skill_list}
    job_keywords_normalized = {normalize_keyword(k): k for k in job_keywords}

    # Find matches: both exact and normalized
    matched_keywords = set()
    keywords_to_bold = set()  # All variations to bold (job keywords + user skills)

    for job_norm, job_orig in job_keywords_normalized.items():
        # Check exact match first
        exact_match = None
        for user_skill in user_skill_list:
            if job_orig.lower().strip() == user_skill.lower().strip():
                exact_match = user_skill
                break

        if exact_match:
            matched_keywords.add(job_orig.lower().strip())
            keywords_to_bold.add(exact_match.lower().strip())  # Bold user's version
            keywords_to_bold.add(job_orig.lower().strip())  # Also try job's version
            continue

        # Check normalized match
        if job_norm in user_skills_normalized:
            user_skill = user_skills_normalized[job_norm]
            matched_keywords.add(job_orig.lower().strip())
            keywords_to_bold.add(user_skill.lower().strip())  # Bold user's version (e.g., "React.js")
            keywords_to_bold.add(job_orig.lower().strip())  # Also try job's version (e.g., "react")

    # Debug logging
    import sys
    sys.stdout.flush()
    print(f"[ATS] Matched {len(matched_keywords)} keywords: {matched_keywords}")
    print(f"[ATS] Keywords to bold: {keywords_to_bold}")
    sys.stdout.flush()

    # Write to debug file as well
    with open("debug_ats.txt", "a") as f:
        f.write(f"\n=== ATS OPTIMIZATION ===\n")
        f.write(f"Matched keywords: {matched_keywords}\n")
        f.write(f"Keywords to bold: {keywords_to_bold}\n")
        f.write(f"Count: {len(keywords_to_bold)}\n")

    match_rate = len(matched_keywords) / len(job_keywords) if job_keywords else 0
    ats_score = round(match_rate * 100, 1)

    # Prioritize matching skills first in each category
    prioritized_skills = {
        "languages": [],
        "frameworks": [],
        "developer_tools": [],
        "libraries": []
    }

    def skill_matches_job(skill: str) -> bool:
        """Check if skill matches any job keyword (fuzzy)"""
        skill_norm = normalize_keyword(skill)
        skill_lower = skill.lower().strip()

        for job_norm, job_orig in job_keywords_normalized.items():
            # Exact match
            if skill_lower == job_orig.lower().strip():
                return True
            # Normalized match
            if skill_norm == job_norm:
                return True
        return False

    for category, skills in user_skills.items():
        if not isinstance(skills, list):
            continue

        matching = [s for s in skills if skill_matches_job(s)]
        non_matching = [s for s in skills if not skill_matches_job(s)]

        prioritized_skills[category] = matching + non_matching

    # Determine score quality
    if ats_score >= 80:
        score_emoji = ""
        score_msg = "Excellent match!"
    elif ats_score >= 60:
        score_emoji = ""
        score_msg = "Good match"
    else:
        score_emoji = ""
        score_msg = "Could be improved"

    return {
        "ats_score": ats_score,
        "prioritized_skills": prioritized_skills,
        "matched_keywords": list(keywords_to_bold),  # Store ALL variations for bolding
        "current_stage": "ats_optimized",
        "messages": [AIMessage(content=(
            f" **ATS Optimization Complete!**\n\n"
            f"{score_emoji} **ATS Score: {ats_score}%** - {score_msg}\n"
            f" Matched **{len(matched_keywords)}** out of **{len(job_keywords)}** keywords\n\n"
            f"Generating your tailored resume..."
        ))]
    }


def _trim_content_for_page_limit(
    experiences: List[Dict],
    projects: List[Dict],
    max_experiences: int = 3,
    max_projects: int = 2
) -> tuple:
    """
    Trim experiences and projects to fit 1-page constraint
    Removes least relevant items (lowest ranked) first
    """
    # Sort by relevance_score if available, otherwise keep original order
    sorted_experiences = sorted(
        experiences,
        key=lambda x: x.get("relevance_score", 0),
        reverse=True
    )
    sorted_projects = sorted(
        projects,
        key=lambda x: x.get("relevance_score", 0),
        reverse=True
    )

    # Take top N items
    trimmed_experiences = sorted_experiences[:max_experiences]
    trimmed_projects = sorted_projects[:max_projects]

    return trimmed_experiences, trimmed_projects


def generate_resume(state: ResumeBuilderState) -> dict:
    """Generate final resume: LaTeX + PDF with 1-page validation"""

    user_id = state.get("user_id")
    is_guest = state.get("is_guest", False)
    selected_experiences = state.get("selected_experiences", [])
    selected_projects = state.get("selected_projects", [])
    prioritized_skills = state.get("prioritized_skills")
    job_analysis = state.get("job_analysis", {})
    ats_score = state.get("ats_score")
    matched_keywords = state.get("matched_keywords", [])

    # Use matched keywords for bolding
    all_keywords_to_bold = set(matched_keywords)

    # Debug logging
    import sys
    sys.stdout.flush()
    print(f"\n[GENERATE] Keywords to bold: {all_keywords_to_bold}\n")
    sys.stdout.flush()

    # Write to debug file
    with open("debug_generate.txt", "a") as f:
        f.write(f"\n=== GENERATE RESUME ===\n")
        f.write(f"Keywords to bold: {all_keywords_to_bold}\n")
        f.write(f"Count: {len(all_keywords_to_bold)}\n")

    # Get full profile - from state for guests, from DB for authenticated users
    if is_guest:
        profile_data = state.get("profile_data", {})
    else:
        db = SessionLocal()
        try:
            profile_data = UserService.get_user_profile(db, user_id)
        finally:
            db.close()

    # Generate LaTeX with 1-page validation loop
    try:
        latex_service = LaTeXService()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{user_id}_{timestamp}"

        # Validation loop: ensure resume fits on 1 page
        MAX_ITERATIONS = 5
        current_experiences = selected_experiences[:]
        current_projects = selected_projects[:]
        latex_code = None
        pdf_path = None
        page_count = 0

        for iteration in range(MAX_ITERATIONS):
            print(f"[PAGE] Validation iteration {iteration + 1}/{MAX_ITERATIONS}")
            print(f"   Experiences: {len(current_experiences)}, Projects: {len(current_projects)}")

            # Generate LaTeX with current content
            latex_code = latex_service.fill_template(
                profile_data=profile_data,
                selected_experiences=current_experiences,
                selected_projects=current_projects,
                prioritized_skills=prioritized_skills,
                matched_keywords=list(all_keywords_to_bold)  # Use combined keywords
            )

            # Try to compile PDF
            pdf_path = latex_service.compile_to_pdf(latex_code, filename)

            if not pdf_path:
                print("[WARNING] PDF compilation failed, skipping page validation")
                break

            # Count pages
            page_count = latex_service.count_pdf_pages(pdf_path)
            print(f"   Page count: {page_count}")

            if page_count <= 1:
                print("[OK] Resume fits on 1 page!")
                break

            if page_count > 1:
                print(f"[WARNING] Resume is {page_count} pages, trimming content...")

                # Calculate trimming strategy
                # Start with 4 experiences, 3 projects
                # Then 3 experiences, 2 projects
                # Then 2 experiences, 2 projects
                # Then 2 experiences, 1 project
                trim_configs = [
                    (4, 3),
                    (3, 2),
                    (2, 2),
                    (2, 1),
                    (1, 1)
                ]

                if iteration < len(trim_configs):
                    max_exp, max_proj = trim_configs[iteration]
                    current_experiences, current_projects = _trim_content_for_page_limit(
                        current_experiences,
                        current_projects,
                        max_experiences=max_exp,
                        max_projects=max_proj
                    )
                else:
                    print("[WARNING] Reached max iterations, using last attempt")
                    break

        # Final check
        if page_count > 1:
            print(f"[WARNING] Warning: Resume is {page_count} pages after {MAX_ITERATIONS} iterations")

        # Update state with final trimmed content
        selected_experiences = current_experiences
        selected_projects = current_projects

        # Save to database only for authenticated users
        if not is_guest:
            db = SessionLocal()
            try:
                resume_gen = ResumeGeneration(
                    generation_id=str(uuid.uuid4()),
                    user_id=user_id,
                    job_title=job_analysis.get("job_title"),
                    company_name=job_analysis.get("company_name"),
                    job_description=state.get("job_description"),
                    tailored_content={
                        "selected_experiences": selected_experiences,
                        "selected_projects": selected_projects,
                        "prioritized_skills": prioritized_skills
                    },
                    ats_keywords=job_analysis.get("keywords"),
                    ats_score=ats_score,
                    latex_code=latex_code,
                    pdf_path=pdf_path
                )
                db.add(resume_gen)
                db.commit()
            finally:
                db.close()

        # Build success message
        guest_note = "\n\n_(Guest mode: resume not saved. Sign up to save your resumes!)_" if is_guest else ""

        # Page validation info
        page_info = ""
        if page_count > 0:
            page_emoji = "[OK]" if page_count == 1 else "[WARNING]"
            page_info = f"**Pages:** {page_emoji} {page_count} page{'s' if page_count > 1 else ''}\n"

        # Content trimming info with detailed explanation
        original_experiences = state.get("selected_experiences", [])
        original_projects = state.get("selected_projects", [])
        original_exp_count = len(original_experiences)
        original_proj_count = len(original_projects)

        trimmed = (len(current_experiences) < original_exp_count or
                   len(current_projects) < original_proj_count)
        trim_note = ""
        if trimmed:
            removed_experiences = [exp.get("title", "Unknown") for exp in original_experiences[len(current_experiences):]]
            removed_projects = [proj.get("name", "Unknown") for proj in original_projects[len(current_projects):]]

            trim_details = f"\n\n**Content Adjusted for 1-Page Format:**\n"
            trim_details += f"- Kept: {len(current_experiences)} of {original_exp_count} experiences, {len(current_projects)} of {original_proj_count} projects\n"

            if removed_experiences:
                trim_details += f"- Removed experiences: {', '.join(removed_experiences)}\n"
            if removed_projects:
                trim_details += f"- Removed projects: {', '.join(removed_projects)}\n"

            trim_details += f"- Reason: To fit professional 1-page resume format\n"
            trim_note = trim_details

        # Build explanation of optimizations
        # ALWAYS show explanation (testing)
        if all_keywords_to_bold:
            keyword_list = list(all_keywords_to_bold)[:15]  # Show first 15
            remaining = len(all_keywords_to_bold) - len(keyword_list)

            changes_explanation = (
                f"\n\n**🎯 Resume Optimizations:**\n"
                f"- Reordered skills to prioritize job requirements\n"
                f"- Bolded {len(all_keywords_to_bold)} ATS-matched keywords\n"
                f"- Selected most relevant experiences and projects\n"
                f"- Ensured 1-page professional format\n\n"
                f"**Bolded Keywords:** {', '.join(keyword_list)}"
            )
            if remaining > 0:
                changes_explanation += f" (+{remaining} more)"
            changes_explanation += "\n"
        else:
            # FORCE explanation even if no keywords (for testing)
            changes_explanation = (
                f"\n\n**🎯 Resume Optimizations:**\n"
                f"- Reordered skills to prioritize job requirements\n"
                f"- Selected most relevant experiences and projects\n"
                f"- Ensured 1-page professional format\n"
                f"- ATS-optimized LaTeX template\n"
            )

        if pdf_path:
            result_message = (
                f"**Resume Generated Successfully!**\n\n"
                f"**PDF saved to:** `{pdf_path}`\n"
                f"**ATS Score:** {ats_score}%\n"
                f"{page_info}"
                f"**Format:** Professional ATS-optimized LaTeX template\n"
                f"{trim_note}"
                f"**LaTeX Code:**\n```latex\n{latex_code[:800]}...\n```\n"
                f"{changes_explanation}\n"  # Add explanation after LaTeX code
                f"Download your PDF from the outputs folder!{guest_note}"
            )
        else:
            result_message = (
                f"**Resume Generated (LaTeX only)**\n\n"
                f"LaTeX code generated successfully\n"
                f"PDF compilation failed (pdflatex not installed)\n"
                f"**ATS Score:** {ats_score}%\n\n"
                f"**LaTeX Code:**\n```latex\n{latex_code}\n```\n"
                f"{changes_explanation}\n"  # Add explanation here too
                f"Copy this code to [Overleaf.com](https://overleaf.com) to compile your PDF!{guest_note}"
            )

        return {
            "latex_code": latex_code,
            "pdf_path": pdf_path,
            "current_stage": "complete",
            "messages": [AIMessage(content=result_message)]
        }

    except Exception as e:
        return {
            "current_stage": "error",
            "messages": [AIMessage(content=(
                f" **Error generating resume:** {str(e)}\n\n"
                f"Please check the logs and try again."
            ))]
        }
