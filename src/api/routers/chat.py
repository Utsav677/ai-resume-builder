"""Chat endpoints for streaming LangGraph responses"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncIterator
import json
import uuid

from langchain_core.messages import HumanMessage

from ..dependencies import get_current_user_optional, get_current_user_from_firebase
from ...resume_agent.models import User
from ...resume_agent.graph import graph
from ...resume_agent.file_parser import extract_text_from_file


router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message request"""
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    thread_id: str
    response: str
    current_stage: str
    ats_score: Optional[float] = None
    latex_code: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_filename: Optional[str] = None  # For guest downloads


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatMessage,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Send a message to the resume builder agent

    This endpoint supports both:
    - **Authenticated users**: Full features with profile persistence
    - **Guest users**: No auth required, short-term memory only (no DB saves)

    Authenticated users:
    - If they have a profile, only need to paste job description
    - Profile automatically loaded from database
    - Resumes saved to database

    Guest users:
    - Must provide both resume AND job description
    - Nothing saved to database (short-term memory only)
    - Can still generate resumes
    """
    # Generate thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())

    # Create config with thread_id
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # Determine if user is guest or authenticated
    is_guest = current_user is None
    user_id = current_user.user_id if current_user else f"guest_{thread_id}"

    try:
        # Invoke the graph with the user's message, user_id, and guest flag
        result = graph.invoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "user_id": user_id,
                "is_guest": is_guest  # Flag to skip database operations
            },
            config
        )

        # Extract the last AI message
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None
        response_text = last_message.content if last_message else "No response"

        # Extract PDF filename for guest downloads
        pdf_filename = None
        pdf_path = result.get("pdf_path")
        if pdf_path and is_guest:
            import os
            pdf_filename = os.path.basename(pdf_path)

        return ChatResponse(
            thread_id=thread_id,
            response=response_text,
            current_stage=result.get("current_stage", "unknown"),
            ats_score=result.get("ats_score"),
            latex_code=result.get("latex_code"),
            pdf_path=result.get("pdf_path"),
            pdf_filename=pdf_filename
        )

    except Exception as e:
        print(f"Error invoking graph: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Graph invocation error: {str(e)}")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Upload and parse a resume file (PDF, DOCX, TXT, or image)

    Extracts text from the uploaded file and returns it.
    The frontend can then send this text to the /message endpoint.

    Supports:
    - PDF (with OCR for scanned documents)
    - DOCX
    - TXT
    - Images (PNG, JPG, JPEG) via OCR

    Returns:
    - extracted_text: The text content from the file
    - filename: Original filename
    - file_size: Size in bytes
    """
    try:
        # Read file content
        file_content = await file.read()

        # Validate file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")

        # Extract text from file
        extracted_text = extract_text_from_file(file_content, file.filename or "unknown")

        # Validate extracted text
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract enough text from file. Please ensure the file contains readable text."
            )

        return {
            "extracted_text": extracted_text,
            "filename": file.filename,
            "file_size": len(file_content),
            "success": True
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/stream")
async def stream_message(
    request: ChatMessage,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Stream responses from the resume builder agent (Server-Sent Events)

    This endpoint streams the agent's responses in real-time,
    providing a better UX for longer operations like resume generation.

    Supports both authenticated and guest users.
    """
    thread_id = request.thread_id or str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # Determine if user is guest or authenticated
    is_guest = current_user is None
    user_id = current_user.user_id if current_user else f"guest_{thread_id}"

    async def event_generator() -> AsyncIterator[str]:
        """Generate Server-Sent Events"""
        try:
            # Stream graph execution
            for chunk in graph.stream(
                {
                    "messages": [HumanMessage(content=request.message)],
                    "user_id": user_id,
                    "is_guest": is_guest
                },
                config
            ):
                # Send each node's output as an event
                event_data = {
                    "thread_id": thread_id,
                    "chunk": chunk
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            error_data = {
                "error": str(e),
                "thread_id": thread_id
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/threads")
async def list_threads(
    current_user: User = Depends(get_current_user_from_firebase)
):
    """
    List all conversation threads for the current user

    Returns a list of thread IDs and metadata.
    Note: This requires storing thread metadata in the database.
    """
    # TODO: Implement thread listing from database
    # For now, return empty list
    return {
        "user_id": current_user.user_id,
        "threads": []
    }


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user_from_firebase)
):
    """
    Delete a conversation thread

    This removes the thread's checkpoint data.
    """
    # TODO: Implement thread deletion from checkpointer
    return {
        "message": f"Thread {thread_id} deleted",
        "thread_id": thread_id
    }
