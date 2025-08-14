from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
from pathlib import Path
import uuid
from datetime import datetime

from app.core.config import settings

from .endpoints import videos

api_router = APIRouter()

# Include routers
api_router.include_router(
    videos.router,
    prefix="/videos",
    tags=["videos"]
)

# Available commentary personalities
COMMENTARY_PERSONALITIES = [
    {
        "id": "hype",
        "name": "Hype Beast",
        "description": "Energetic and over-the-top streetball style commentary"
    },
    {
        "id": "analytical",
        "name": "Analyst",
        "description": "Technical breakdown of plays and strategies"
    },
    {
        "id": "trash_talk",
        "name": "Trash Talk",
        "description": "Funny and competitive trash talking commentary"
    },
    {
        "id": "classic",
        "name": "Classic ESPN",
        "description": "Professional sports commentary style"
    },
    {
        "id": "shakespeare",
        "name": "Shakespearean",
        "description": "Basketball commentary in the style of Shakespeare"
    }
]

@api_router.get("/personalities", response_model=List[dict])
async def get_commentary_personalities():
    """Get available commentary personalities"""
    return COMMENTARY_PERSONALITIES

@api_router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing"""
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".mp4", ".webm", ".mov"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload an MP4, WebM, or MOV file."
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    try:
        with open(file_path, "wb+") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving file: {str(e)}"
        )
    
    return {
        "id": file_id,
        "filename": filename,
        "content_type": file.content_type,
        "size": os.path.getsize(file_path)
    }

@api_router.post("/process")
async def process_video(
    video_id: str,
    personality: str = "hype",
    language: str = "en"
):
    """Process video with selected commentary personality"""
    # TODO: Implement video processing pipeline
    # 1. Extract frames and run computer vision
    # 2. Generate commentary using LLM
    # 3. Generate voiceover
    # 4. Combine with video
    
    return {
        "status": "processing",
        "job_id": str(uuid.uuid4()),
        "video_id": video_id,
        "personality": personality,
        "language": language
    }
