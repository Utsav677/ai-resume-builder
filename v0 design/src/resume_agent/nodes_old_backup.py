"""LangGraph nodes for resume builder"""
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


def profile_check_node(state: ResumeBuilderState) -> dict:
    """Check if user has a complete profile"""
    
    # Get user_id from state, or use default
    user_id = state.get("user_id")
    if not user_id:
        from .studio_config import DEFAULT_USER_ID
        user_id = DEFAULT_USER_ID
    
    db = SessionLocal()
    try:
        has_profile = UserService.profile_exists(db, user_id)
        
        if has_profile:
            return {
                "user_id": user_id,
                "profile_complete": True,
                "current_stage": "job_input",
                "messages": [AIMessage(content=(
                    "Welcome back! I see you already have a profile set up.\n\n"
                    "Let's create a tailored resume for your next opportunity!\n\n"
                    "Please paste the **job description** you're applying for."
                ))]
            }
        else:
            return {
                "user_id": user_id,
                "profile_complete": False,
                "current_stage": "profile_input",
                "messages": [AIMessage(content=(
                    "Welcome to the AI Resume Builder!\n\n"
                    "I'll help you create an ATS-optimized resume tailored to any job.\n\n"
                    "First, I need to build your profile. Please provide ONE of the following:\n"
                    "1. Your current resume (paste the full text)\n"
                    "2. A detailed summary of your experience\n\n"
                    "Paste it below, and I'll extract all the important information!"
                ))]
            }
    finally:
        db.close()


def profile_extraction_node(state: ResumeBuilderState) -> dict:
    """Extract structured profile data from user's resume"""
    
    # Debug: Print all messages to understand the flow
    print(f"DEBUG: Total messages in state: {len(state.get('messages', []))}")
    for i, msg in enumerate(state.get("messages", [])):
        print(f"DEBUG: Message {i}: type={getattr(msg, 'type', 'unknown')}, content_preview={str(getattr(msg, 'content', 'no content'))[:50]}...")

    # Get the last human message only (ignore AI messages)
    user_message = None
    human_messages = []

    for msg in state.get("messages", []):
        if hasattr(msg, 'type') and msg.type == "human":
            human_messages.append(msg.content)

    if human_messages:
        user_message = human_messages[-1]  # Get the most recent human message
        print(f"DEBUG: Found user message: {user_message[:100]}...")
    else:
        print("DEBUG: No human messages found")
    
    # Don't re-extract if we already have a profile
    if state.get("profile_complete"):
        return {
            "current_stage": "complete"
        }

    # Check if we have enough content
    if not user_message or len(user_message) < 100:
        return {
            "messages": [AIMessage(content=(
                "I need more information. Please paste your full resume or a detailed summary (at least 100 characters)."
            ))],
            "current_stage": "profile_extraction",
            "profile_complete": False,
            "needs_user_input": True
        }
    
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
      "dates": "Month Year – Month Year"
    }}
  ],
  "experience": [
    {{
      "title": "string",
      "dates": "Month Year – Month Year",
      "organization": "string",
      "location": "string",
      "bullets": ["achievement with metrics", "another achievement"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "technologies": "comma-separated tech stack",
      "dates": "Month Year – Month Year",
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
        
        # Clean response (remove markdown code blocks if present)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        profile_data = json.loads(content)
        
        # Save to database
        user_id = state.get("user_id")
        if not user_id:
            from .studio_config import DEFAULT_USER_ID
            user_id = DEFAULT_USER_ID
            
        db = SessionLocal()
        try:
            UserService.save_user_profile(db, user_id, profile_data)
        finally:
            db.close()
        
        exp_count = len(profile_data.get("experience", []))
        proj_count = len(profile_data.get("projects", []))
        
        return {
            "profile_complete": True,
            "current_stage": "job_input",
            "messages": [AIMessage(content=(
                f"✅ Profile Created!\n\n"
                f"Extracted:\n"
                f"- {exp_count} work experience(s)\n"
                f"- {proj_count} project(s)\n\n"
                f"Great! Now paste the **job description** for the position you're applying to."
            ))]
        }
        
    except Exception as e:
        return {
            "messages": [AIMessage(content=(
                f"Sorry, I had trouble parsing your resume. Error: {str(e)}\n\n"
                f"Please try again with clearer formatting or paste a text version of your resume."
            ))],
            "current_stage": "profile_extraction",
            "profile_complete": False,
            "needs_user_input": True
        }


def job_input_node(state: ResumeBuilderState) -> dict:
    """Wait for user to provide job description"""

    # If we already have a job description stored, skip asking again
    if state.get("job_description"):
        return {
            "current_stage": "job_analysis"
        }

    # Check if we already have a job description from the latest human message
    # Look for messages that came AFTER profile was completed
    human_messages = []
    for msg in state.get("messages", []):
        if hasattr(msg, 'type') and msg.type == "human":
            human_messages.append(msg.content)

    # Get the most recent message
    if human_messages:
        latest_message = human_messages[-1]

        # Check if this looks like a job description (reasonable length)
        # Exclude LaTeX resumes (they start with %)
        if len(latest_message) > 100 and not latest_message.strip().startswith('%'):
            return {
                "job_description": latest_message,
                "current_stage": "job_analysis",
                "messages": [AIMessage(content=(
                    "Got it! Analyzing the job description to understand what they're looking for..."
                ))]
            }

    # If no job description yet, ask for it (but DON'T go to complete - stay here)
    return {
        "current_stage": "job_input",
        "needs_user_input": True,
        "messages": [AIMessage(content=(
            "Please paste the **job description** for the position you're applying to.\n\n"
            "Include as much detail as possible (requirements, qualifications, responsibilities)."
        ))]
    }


def job_analysis_node(state: ResumeBuilderState) -> dict:
    """Analyze job description to extract requirements and keywords"""

    job_description = state.get("job_description")

    # If no job description yet, this means job_input_node asked for it
    # We should go to complete to end this turn and wait for user input
    if not job_description:
        return {
            "current_stage": "complete",
            "messages": []  # Don't add another message, job_input already did
        }

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
            "job_analysis": job_analysis,
            "current_stage": "content_selection",
            "messages": [AIMessage(content=(
                f"Job Analysis Complete!\n\n"
                f"Position: {job_analysis.get('job_title', 'N/A')}\n"
                f"Level: {job_analysis.get('experience_level', 'N/A')}\n"
                f"Key Skills: {', '.join(job_analysis.get('required_skills', [])[:5])}...\n\n"
                f"Now selecting the most relevant experiences from your profile..."
            ))]
        }

    except Exception as e:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content=(
                f"Error analyzing job description: {str(e)}\n"
                "Please try with a different job description."
            ))]
        }


def content_selection_node(state: ResumeBuilderState) -> dict:
    """Select most relevant experiences and projects for the job"""

    job_analysis = state.get("job_analysis")
    user_id = state.get("user_id")

    if not job_analysis or not user_id:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content="Missing required data for content selection.")]
        }

    # Get user profile
    db = SessionLocal()
    try:
        profile_data = UserService.get_user_profile(db, user_id)
    finally:
        db.close()

    if not profile_data:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content="Profile not found.")]
        }

    # Use LLM to rank and select experiences
    experiences = profile_data.get("experience", [])
    projects = profile_data.get("projects", [])

    selection_prompt = f"""Given this job analysis:
{json.dumps(job_analysis, indent=2)}

And these experiences:
{json.dumps(experiences, indent=2)}

And these projects:
{json.dumps(projects, indent=2)}

Select and rank the MOST RELEVANT experiences and projects for this job. Return ONLY valid JSON:
{{
  "selected_experience_indices": [0, 2, 1],
  "selected_project_indices": [1, 0],
  "reasoning": "brief explanation of selections"
}}

Prioritize experiences/projects that:
1. Match required skills
2. Demonstrate relevant accomplishments
3. Show progression in the field
4. Include quantifiable results

Return indices in priority order (most relevant first). Include ALL experiences but rank them."""

    try:
        response = llm.invoke(selection_prompt)
        content = response.content.strip()

        # Clean response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        selection = json.loads(content)

        # Reorder experiences and projects based on selection
        exp_indices = selection.get("selected_experience_indices", list(range(len(experiences))))
        proj_indices = selection.get("selected_project_indices", list(range(len(projects))))

        selected_experiences = [experiences[i] for i in exp_indices if i < len(experiences)]
        selected_projects = [projects[i] for i in proj_indices if i < len(projects)]

        return {
            "selected_experiences": selected_experiences,
            "selected_projects": selected_projects,
            "current_stage": "ats_optimization",
            "messages": [AIMessage(content=(
                f"Content Selection Complete!\n\n"
                f"Selected {len(selected_experiences)} experiences and {len(selected_projects)} projects.\n"
                f"{selection.get('reasoning', '')}\n\n"
                f"Now optimizing for ATS..."
            ))]
        }

    except Exception as e:
        # Fallback: use all content in original order
        return {
            "selected_experiences": experiences,
            "selected_projects": projects,
            "current_stage": "ats_optimization",
            "messages": [AIMessage(content=(
                f"Using all experiences and projects. Proceeding to ATS optimization..."
            ))]
        }


def ats_optimization_node(state: ResumeBuilderState) -> dict:
    """Optimize skills and calculate ATS score"""

    job_analysis = state.get("job_analysis")
    user_id = state.get("user_id")
    selected_experiences = state.get("selected_experiences", [])
    selected_projects = state.get("selected_projects", [])

    if not job_analysis or not user_id:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content="Missing required data for ATS optimization.")]
        }

    # Get user profile for skills
    db = SessionLocal()
    try:
        profile_data = UserService.get_user_profile(db, user_id)
    finally:
        db.close()

    user_skills = profile_data.get("technical_skills", {})

    # Extract all keywords from job
    job_keywords = set()
    job_keywords.update(job_analysis.get("required_skills", []))
    job_keywords.update(job_analysis.get("keywords", []))
    job_keywords.update(job_analysis.get("nice_to_have", []))

    # Extract all skills from user profile
    user_skill_list = []
    for category, skills in user_skills.items():
        if isinstance(skills, list):
            user_skill_list.extend(skills)

    # Calculate keyword match (case-insensitive)
    user_skills_lower = set([s.lower() for s in user_skill_list])
    job_keywords_lower = set([k.lower() for k in job_keywords])

    matched_keywords = job_keywords_lower.intersection(user_skills_lower)
    match_rate = len(matched_keywords) / len(job_keywords_lower) if job_keywords_lower else 0
    ats_score = round(match_rate * 100, 1)

    # Prioritize skills that match job requirements
    prioritized_skills = {
        "languages": [],
        "frameworks": [],
        "developer_tools": [],
        "libraries": []
    }

    # Put matching skills first in each category
    for category, skills in user_skills.items():
        if not isinstance(skills, list):
            continue

        matching = [s for s in skills if s.lower() in job_keywords_lower]
        non_matching = [s for s in skills if s.lower() not in job_keywords_lower]

        prioritized_skills[category] = matching + non_matching

    return {
        "ats_score": ats_score,
        "prioritized_skills": prioritized_skills,
        "current_stage": "latex_generation",
        "messages": [AIMessage(content=(
            f"ATS Optimization Complete!\n\n"
            f"ATS Score: {ats_score}%\n"
            f"Matched {len(matched_keywords)}/{len(job_keywords_lower)} keywords\n\n"
            f"{'✓ Strong match!' if ats_score >= 70 else '⚠ Consider adding more relevant keywords'}\n\n"
            f"Generating resume..."
        ))]
    }


def latex_generation_node(state: ResumeBuilderState) -> dict:
    """Generate LaTeX code from profile and selections"""

    user_id = state.get("user_id")
    selected_experiences = state.get("selected_experiences")
    selected_projects = state.get("selected_projects")
    prioritized_skills = state.get("prioritized_skills")

    if not user_id:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content="Missing user ID.")]
        }

    # Get full profile
    db = SessionLocal()
    try:
        profile_data = UserService.get_user_profile(db, user_id)
    finally:
        db.close()

    if not profile_data:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content="Profile not found.")]
        }

    try:
        latex_service = LaTeXService()
        latex_code = latex_service.fill_template(
            profile_data=profile_data,
            selected_experiences=selected_experiences,
            selected_projects=selected_projects,
            prioritized_skills=prioritized_skills
        )

        return {
            "latex_code": latex_code,
            "current_stage": "pdf_compilation",
            "messages": [AIMessage(content=(
                "LaTeX code generated successfully!\n\n"
                "Compiling to PDF..."
            ))]
        }

    except Exception as e:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content=(
                f"Error generating LaTeX: {str(e)}"
            ))]
        }


def pdf_compilation_node(state: ResumeBuilderState) -> dict:
    """Compile LaTeX to PDF and save to database"""

    latex_code = state.get("latex_code")
    user_id = state.get("user_id")
    job_analysis = state.get("job_analysis", {})
    ats_score = state.get("ats_score")

    if not latex_code:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content="No LaTeX code to compile.")]
        }

    try:
        latex_service = LaTeXService()

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{user_id}_{timestamp}"

        pdf_path = latex_service.compile_to_pdf(latex_code, filename)

        if pdf_path:
            # Save to database
            db = SessionLocal()
            try:
                resume_gen = ResumeGeneration(
                    generation_id=str(uuid.uuid4()),
                    user_id=user_id,
                    job_title=job_analysis.get("job_title"),
                    company_name=job_analysis.get("company_name"),
                    job_description=state.get("job_description"),
                    tailored_content={
                        "selected_experiences": state.get("selected_experiences"),
                        "selected_projects": state.get("selected_projects"),
                        "prioritized_skills": state.get("prioritized_skills")
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

            return {
                "pdf_path": pdf_path,
                "current_stage": "complete",
                "messages": [AIMessage(content=(
                    f"✅ Resume Generated Successfully!\n\n"
                    f"PDF saved to: {pdf_path}\n"
                    f"ATS Score: {ats_score}%\n\n"
                    f"Your tailored resume is ready!\n\n"
                    f"**LaTeX Code:**\n```latex\n{latex_code[:500]}...\n```"
                ))]
            }
        else:
            # PDF compilation failed, but still return LaTeX
            return {
                "current_stage": "complete",
                "messages": [AIMessage(content=(
                    f"⚠ PDF compilation failed (pdflatex not installed?)\n\n"
                    f"But here's your LaTeX code:\n\n"
                    f"```latex\n{latex_code}\n```\n\n"
                    f"You can compile this manually or use an online LaTeX editor like Overleaf."
                ))]
            }

    except Exception as e:
        return {
            "current_stage": "complete",
            "messages": [AIMessage(content=(
                f"Error during PDF compilation: {str(e)}\n\n"
                f"LaTeX code:\n```latex\n{latex_code[:500]}...\n```"
            ))]
        }


def simple_complete_node(state: ResumeBuilderState) -> dict:
    """Completion node"""
    return {
        "current_stage": "complete"
    }
