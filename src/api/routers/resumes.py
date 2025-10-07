"""Resume management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

from ..dependencies import get_db, get_current_user_from_firebase
from ...resume_agent.models import User, UserProfile, ResumeGeneration


router = APIRouter()


class ResumeListItem(BaseModel):
    """Resume list item response"""
    id: int
    job_title: str
    company_name: Optional[str]
    version: int
    resume_filename: str
    ats_score: Optional[float]
    created_at: str
    has_pdf: bool


class ResumeDetail(BaseModel):
    """Detailed resume response"""
    id: str  # Changed to str for generation_id (UUID)
    job_title: str
    company_name: Optional[str]
    job_description: str
    ats_score: Optional[float]
    latex_code: str
    pdf_path: Optional[str]
    created_at: str


class ProfileResponse(BaseModel):
    """User profile response"""
    has_profile: bool
    contact: Optional[dict]
    education: Optional[List[dict]]
    experience: Optional[List[dict]]
    projects: Optional[List[dict]]
    technical_skills: Optional[dict]


@router.get("/", response_model=List[ResumeListItem])
async def list_resumes(
    current_user: User = Depends(get_current_user_from_firebase),
    db: Session = Depends(get_db)
):
    """
    Get all resumes for the current user

    Returns a list of all resumes the user has generated,
    sorted by creation date (newest first).
    """
    resumes = db.query(ResumeGeneration).filter(
        ResumeGeneration.user_id == current_user.user_id
    ).order_by(ResumeGeneration.created_at.desc()).all()

    return [
        ResumeListItem(
            id=r.generation_id,  # Changed from r.id to r.generation_id
            job_title=r.job_title or "Untitled Position",
            company_name=r.company_name,
            version=int(r.version) if r.version is not None else 0,
            resume_filename=r.resume_filename or "resume",
            ats_score=r.ats_score,
            created_at=r.created_at.isoformat() if r.created_at else "",
            has_pdf=bool(r.pdf_path)
        )
        for r in resumes
    ]


@router.get("/{resume_id}", response_model=ResumeDetail)
async def get_resume(
    resume_id: str,  # Changed to str for generation_id (UUID)
    current_user: User = Depends(get_current_user_from_firebase),
    db: Session = Depends(get_db)
):
    """
    Get a specific resume by ID

    Returns the full resume data including LaTeX code and PDF path.
    """
    resume = db.query(ResumeGeneration).filter(
        ResumeGeneration.generation_id == resume_id,
        ResumeGeneration.user_id == current_user.user_id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    return ResumeDetail(
        id=resume.generation_id,
        job_title=resume.job_title or "Untitled Position",
        company_name=resume.company_name,
        job_description=resume.job_description or "",
        ats_score=resume.ats_score,
        latex_code=resume.latex_code or "",
        pdf_path=resume.pdf_path,
        created_at=resume.created_at.isoformat() if resume.created_at else ""
    )


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user_from_firebase),
    db: Session = Depends(get_db)
):
    """
    Download a resume PDF

    Returns the PDF file for download.
    """
    resume = db.query(ResumeGeneration).filter(
        ResumeGeneration.generation_id == resume_id,
        ResumeGeneration.user_id == current_user.user_id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    if not resume.pdf_path or not os.path.exists(resume.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )

    filename = resume.resume_filename + ".pdf" if resume.resume_filename else "resume.pdf"

    return FileResponse(
        path=resume.pdf_path,
        media_type="application/pdf",
        filename=filename
    )


@router.get("/download/guest/{filename}")
async def download_guest_resume(filename: str):
    """
    Download a guest resume PDF (temporary, no auth required)

    For security, only allow downloads of files matching guest resume pattern.
    """
    # Security: Only allow guest resume files
    if not filename.startswith("resume_guest_") or not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    pdf_path = os.path.join("outputs", filename)

    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found or expired"
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"optimized_resume.pdf"
    )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,  # Changed to str for generation_id
    current_user: User = Depends(get_current_user_from_firebase),
    db: Session = Depends(get_db)
):
    """
    Delete a resume

    Removes the resume from the database and optionally deletes the PDF file.
    """
    resume = db.query(ResumeGeneration).filter(
        ResumeGeneration.generation_id == resume_id,
        ResumeGeneration.user_id == current_user.user_id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    # Delete PDF file if exists
    if resume.pdf_path and os.path.exists(resume.pdf_path):
        try:
            os.remove(resume.pdf_path)
        except Exception as e:
            print(f"Error deleting PDF file: {e}")

    db.delete(resume)
    db.commit()

    return {"message": "Resume deleted successfully", "resume_id": resume_id}


@router.get("/profile/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user_from_firebase),
    db: Session = Depends(get_db)
):
    """
    Get the current user's profile

    Returns the extracted resume data (contact, education, experience, etc.)
    """
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.user_id
    ).first()

    if not profile:
        return ProfileResponse(
            has_profile=False,
            contact=None,
            education=None,
            experience=None,
            projects=None,
            technical_skills=None
        )

    return ProfileResponse(
        has_profile=True,
        contact=profile.contact,
        education=profile.education,
        experience=profile.experience,
        projects=profile.projects,
        technical_skills=profile.technical_skills
    )


@router.delete("/profile/me")
async def delete_my_profile(
    current_user: User = Depends(get_current_user_from_firebase),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's profile

    This allows the user to re-upload their resume and start fresh.
    """
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    db.delete(profile)
    db.commit()

    return {"message": "Profile deleted successfully"}
