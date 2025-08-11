from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import os
import uuid
from pathlib import Path
import shutil
import asyncio

from ....core.config import settings
from ....services.processing_pipeline import ProcessingPipeline
from ....models.video import VideoStatus

router = APIRouter()

# In-memory storage for video processing status (replace with Redis in production)
processing_status = {}

@router.post("/upload", response_model=dict)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    personality: str = "hype",
    language: str = "en"
):
    """Upload a video for processing"""
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".mp4", ".webm", ".mov"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload an MP4, WebM, or MOV file."
        )
    
    # Generate unique ID for this video
    video_id = str(uuid.uuid4())
    filename = f"{video_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save uploaded file
    try:
        with open(file_path, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Initialize processing status
    processing_status[video_id] = {
        "status": "uploaded",
        "progress": 0,
        "message": "Video uploaded successfully",
        "result": None,
        "error": None
    }
    
    # Start background task for processing
    background_tasks.add_task(
        process_video_background,
        video_id=video_id,
        file_path=file_path,
        personality=personality,
        language=language
    )
    
    return {
        "video_id": video_id,
        "status": "processing",
        "message": "Video upload successful. Processing has started.",
        "check_status_url": f"/api/v1/videos/{video_id}/status"
    }

@router.get("/{video_id}/status", response_model=dict)
async def get_processing_status(video_id: str):
    """Get the status of a video processing job"""
    if video_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail=f"Video with ID {video_id} not found"
        )
    
    status = processing_status[video_id]
    
    # If processing is complete, include the result
    if status["status"] == "completed" and status["result"]:
        return {
            "video_id": video_id,
            "status": status["status"],
            "progress": 100,
            "message": status["message"],
            "result": {
                "output_file": status["result"]["output_file"],
                "download_url": f"/api/v1/videos/{video_id}/download",
                "preview_url": f"/api/v1/videos/{video_id}/preview"
            }
        }
    
    # If there was an error
    if status["status"] == "error":
        return {
            "video_id": video_id,
            "status": "error",
            "progress": 0,
            "message": status["message"],
            "error": status.get("error", "Unknown error occurred")
        }
    
    # Processing is still in progress
    return {
        "video_id": video_id,
        "status": status["status"],
        "progress": status["progress"],
        "message": status["message"]
    }

@router.get("/{video_id}/download")
async def download_video(video_id: str):
    """Download the processed video"""
    if video_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail=f"Video with ID {video_id} not found"
        )
    
    status = processing_status[video_id]
    
    if status["status"] != "completed" or not status["result"]:
        raise HTTPException(
            status_code=400,
            detail=f"Video {video_id} is not ready for download"
        )
    
    output_file = status["result"]["output_file"]
    
    if not os.path.exists(output_file):
        raise HTTPException(
            status_code=404,
            detail="Processed video file not found"
        )
    
    return FileResponse(
        output_file,
        media_type="video/mp4",
        filename=f"hoopnarrator_{video_id}.mp4"
    )

@router.get("/{video_id}/preview")
async def get_video_preview(video_id: str):
    """Get a preview of the processed video"""
    # This could be implemented to return a lower resolution or shorter preview
    # For now, we'll just return the same as download
    return await download_video(video_id)

async def process_video_background(
    video_id: str,
    file_path: str,
    personality: str,
    language: str
):
    """Background task to process the video"""
    try:
        pipeline = ProcessingPipeline()
        
        # Update status to processing
        processing_status[video_id].update({
            "status": "processing",
            "progress": 10,
            "message": "Starting video analysis..."
        })
        
        # Process the video
        result = await pipeline.process_video(
            video_path=file_path,
            personality=personality,
            language=language,
            vertical_format=True
        )
        
        if result["status"] == "completed":
            # Update status to completed
            processing_status[video_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Video processing completed successfully",
                "result": {
                    "output_file": result["output_file"],
                    "commentary": result["commentary"],
                    "events_detected": result["events_detected"]
                }
            })
        else:
            # Update status with error
            processing_status[video_id].update({
                "status": "error",
                "message": result.get("message", "Unknown error occurred"),
                "error": str(result)
            })
    
    except Exception as e:
        # Handle any unexpected errors
        processing_status[video_id].update({
            "status": "error",
            "message": "An unexpected error occurred during processing",
            "error": str(e)
        })
