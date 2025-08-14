from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import os
import uuid
from pathlib import Path
import shutil
import asyncio

from app.core.config import settings
from app.services.processing_pipeline import ProcessingPipeline
from app.models.video import VideoStatus

router = APIRouter()

# In-memory storage for video processing status (replace with Redis in production)
processing_status = {}


@router.post("/process")
async def process_video(
    request: Request,
    file: UploadFile = File(...),
    personality: str = Form(...)
):
    try:
        # Log the request details
        print("\n=== Received Request ===")
        print(f"Headers: {dict(request.headers)}")
        print(f"Content type: {request.headers.get('content-type')}")
        
        # Verify file was received
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
            
        # Verify file content type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
            
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate a unique filename
        file_ext = os.path.splitext(file.filename)[1]
        video_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}{file_ext}")
        
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        print(f"Saved uploaded file to: {file_path}")
        print(f"File size: {os.path.getsize(file_path)} bytes")
        print(f"Personality: {personality}")
        
        # Return success response with video ID
        return {
            "status": "processing",
            "videoId": video_id,
            "message": "Video uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")

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


