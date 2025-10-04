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

# Initialize LLM
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    temperature=0
)


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
    """Ask user to paste resume - graph will pause here"""

    return {
        "current_stage": "waiting_for_resume",
        "needs_user_input": True,
        "messages": [AIMessage(content=(
            " Welcome to the AI Resume Builder!\n\n"
            "I'll help you create an ATS-optimized resume tailored to any job.\n\n"
            "**Step 1:** Please paste your resume below.\n"
            "You can paste:\n"
            "- Plain text resume\n"
            "- LaTeX resume code\n"
            "- Detailed summary of your experience\n\n"
            "Paste it now, and I'll extract all the important information!"
        ))]
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
      "dates": "Month Year  Month Year"
    }}
  ],
  "experience": [
    {{
      "title": "string",
      "dates": "Month Year  Month Year",
      "organization": "string",
      "location": "string",
      "bullets": ["achievement with metrics", "another achievement"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "technologies": "comma-separated tech stack",
      "dates": "Month Year  Month Year",
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

        exp_count = len(profile_data.get("experience", []))
        proj_count = len(profile_data.get("projects", []))

        # Different message for guests vs authenticated users
        if is_guest:
            message = (
                f"✓ **Profile Extracted!**\n\n"
                f"Found:\n"
                f"- **{exp_count}** work experiences\n"
                f"- **{proj_count}** projects\n"
                f"- Contact info and skills\n\n"
                f"_(Guest mode: profile not saved)_"
            )
        else:
            message = (
                f"✓ **Profile Extracted Successfully!**\n\n"
                f"Found:\n"
                f"- **{exp_count}** work experiences\n"
                f"- **{proj_count}** projects\n"
                f"- Contact info and skills saved\n\n"
                f"Great! Your profile is saved to the database."
            )

        return {
            "profile_complete": True,
            "profile_data": profile_data,  # Store in state for guests
            "current_stage": "profile_extracted",
            "messages": [AIMessage(content=message)]
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


def wait_for_job_description(state: ResumeBuilderState) -> dict:
    """Ask user to paste job description - graph will pause here"""

    return {
        "current_stage": "waiting_for_job_description",
        "needs_user_input": True,
        "messages": [AIMessage(content=(
            " **Step 2:** Paste the job description\n\n"
            "Copy and paste the full job posting for the role you're applying to.\n"
            "Include:\n"
            "- Job title\n"
            "- Requirements & qualifications\n"
            "- Responsibilities\n"
            "- Preferred skills\n\n"
            "The more detail, the better the ATS optimization!"
        ))]
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

    # Get user profile from database
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

        return {
            "selected_experiences": selected_experiences,
            "selected_projects": selected_projects,
            "current_stage": "content_selected",
            "messages": [AIMessage(content=(
                f" **Content Selection Complete!**\n\n"
                f" Selected **{len(selected_experiences)}** experiences and **{len(selected_projects)}** projects\n"
                f" {selection.get('reasoning', '')}\n\n"
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

    # Calculate match (case-insensitive)
    user_skills_lower = set([s.lower().strip() for s in user_skill_list])
    job_keywords_lower = set([k.lower().strip() for k in job_keywords])

    matched_keywords = job_keywords_lower.intersection(user_skills_lower)
    match_rate = len(matched_keywords) / len(job_keywords_lower) if job_keywords_lower else 0
    ats_score = round(match_rate * 100, 1)

    # Prioritize matching skills first in each category
    prioritized_skills = {
        "languages": [],
        "frameworks": [],
        "developer_tools": [],
        "libraries": []
    }

    for category, skills in user_skills.items():
        if not isinstance(skills, list):
            continue

        matching = [s for s in skills if s.lower().strip() in job_keywords_lower]
        non_matching = [s for s in skills if s.lower().strip() not in job_keywords_lower]

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
        "current_stage": "ats_optimized",
        "messages": [AIMessage(content=(
            f" **ATS Optimization Complete!**\n\n"
            f"{score_emoji} **ATS Score: {ats_score}%** - {score_msg}\n"
            f" Matched **{len(matched_keywords)}** out of **{len(job_keywords_lower)}** keywords\n\n"
            f"Generating your tailored resume..."
        ))]
    }


def generate_resume(state: ResumeBuilderState) -> dict:
    """Generate final resume: LaTeX + PDF"""

    user_id = state.get("user_id")
    is_guest = state.get("is_guest", False)
    selected_experiences = state.get("selected_experiences")
    selected_projects = state.get("selected_projects")
    prioritized_skills = state.get("prioritized_skills")
    job_analysis = state.get("job_analysis", {})
    ats_score = state.get("ats_score")

    # Get full profile - from state for guests, from DB for authenticated users
    if is_guest:
        profile_data = state.get("profile_data", {})
    else:
        db = SessionLocal()
        try:
            profile_data = UserService.get_user_profile(db, user_id)
        finally:
            db.close()

    # Generate LaTeX using service
    try:
        latex_service = LaTeXService()
        latex_code = latex_service.fill_template(
            profile_data=profile_data,
            selected_experiences=selected_experiences,
            selected_projects=selected_projects,
            prioritized_skills=prioritized_skills
        )

        # Try to compile PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{user_id}_{timestamp}"
        pdf_path = latex_service.compile_to_pdf(latex_code, filename)

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

        if pdf_path:
            result_message = (
                f"✓ **Resume Generated Successfully!**\n\n"
                f"**PDF saved to:** `{pdf_path}`\n"
                f"**ATS Score:** {ats_score}%\n"
                f"**Format:** Professional ATS-optimized LaTeX template\n\n"
                f"**LaTeX Code:**\n```latex\n{latex_code[:800]}...\n```\n\n"
                f"Download your PDF from the outputs folder!{guest_note}"
            )
        else:
            result_message = (
                f"✓ **Resume Generated (LaTeX only)**\n\n"
                f"LaTeX code generated successfully\n"
                f"PDF compilation failed (pdflatex not installed)\n"
                f"**ATS Score:** {ats_score}%\n\n"
                f"**LaTeX Code:**\n```latex\n{latex_code}\n```\n\n"
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
