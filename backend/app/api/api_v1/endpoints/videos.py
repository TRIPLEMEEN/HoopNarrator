from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
import os
import sys
import uuid
from pathlib import Path
import shutil
import asyncio
import logging
from datetime import datetime

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
    """
    Handle video upload and start processing.
    
    Args:
        request: The incoming request
        file: The uploaded video file
        personality: The commentary personality to use
        
    Returns:
        dict: Status and video ID for tracking processing
    """
    start_time = datetime.now()
    video_id = None
    file_path = None
    
    try:
        # Log the request details
        print(f"\n=== Received Request at {start_time} ===")
        print(f"Endpoint: {request.url}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Content type: {request.headers.get('content-type')}")
        print(f"Personality: {personality}")
        
        # Verify file was received
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Verify file has content
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        # Verify file content type
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.content_type}. Must be a video file."
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        print(f"Using upload directory: {settings.UPLOAD_DIR}")
        
        # Generate a unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        if not file_ext:
            file_ext = ".mp4"  # Default extension if none provided
            
        video_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}{file_ext}")
        
        # Save the uploaded file
        print(f"Saving uploaded file to: {file_path}")
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_size = os.path.getsize(file_path)
        print(f"File saved successfully. Size: {file_size} bytes")
        
        # Initialize processing status
        processing_status[video_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting video processing...",
            "start_time": start_time.isoformat(),
            "file_size": file_size,
            "original_filename": file.filename
        }
        
        # Start background processing
        print(f"Starting background processing for video {video_id}")
        asyncio.create_task(process_video_background(
            video_id=video_id,
            file_path=file_path,
            personality=personality,
            language="en"
        ))
        
        # Log successful upload
        upload_time = (datetime.now() - start_time).total_seconds()
        print(f"Video upload and processing started in {upload_time:.2f} seconds")
        
        # Return success response with video ID
        return {
            "status": "processing",
            "videoId": video_id,
            "message": "Video uploaded and processing started",
            "fileSize": file_size,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as-is
        print(f"HTTP error processing video: {he.detail}")
        raise
        
    except Exception as e:
        # Log the full error
        import traceback
        error_msg = f"Error processing video: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        
        # Clean up any partially uploaded files
        if video_id and video_id in processing_status:
            del processing_status[video_id]
            
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up file after error: {file_path}")
            except Exception as cleanup_error:
                print(f"Error cleaning up file {file_path}: {str(cleanup_error)}")
        
        # Return a 500 error with the error message
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process video: {str(e)}"
        )

@router.get("/{video_id}/status", response_model=dict)
async def get_processing_status(video_id: str):
    """Get the status of a video processing job"""
    print(f"Getting status for video {video_id}")
    
    if video_id not in processing_status:
        print(f"Video {video_id} not found in processing_status")
        raise HTTPException(
            status_code=404,
            detail=f"Video with ID {video_id} not found or processing hasn't started yet"
        )
    
    status = processing_status[video_id]
    print(f"Current status for {video_id}: {status}")
    
    # Prepare base response
    response = {
        "videoId": video_id,
        "status": status.get("status", "unknown"),
        "progress": status.get("progress", 0),
        "message": status.get("message", "Processing...")
    }
    
    # Add additional fields based on status
    if status["status"] == "completed":
        result = status.get("result", {})
        response.update({
            "downloadUrl": f"/api/v1/videos/{video_id}/download",
            "previewUrl": f"/api/v1/videos/{video_id}/preview",
            "outputFile": result.get("output_file", ""),
            "events": result.get("events_detected", []),
            "message": result.get("message", status.get("message", "Processing complete"))
        })
    elif status["status"] == "error":
        response.update({
            "error": status.get("error", "Unknown error occurred"),
            "message": status.get("message", "An error occurred during processing")
        })
    
    print(f"Returning status for {video_id}: {response}")
    return response

@router.get("/{video_id}/download")
async def download_video(video_id: str):
    """Download the processed video"""
    print(f"Download request for video {video_id}")
    
    if video_id not in processing_status:
        print(f"Video {video_id} not found in processing_status")
        raise HTTPException(
            status_code=404,
            detail=f"Video with ID {video_id} not found"
        )
    
    status = processing_status[video_id]
    
    # Check if processing is complete
    if status.get("status") != "completed" or "result" not in status:
        print(f"Video {video_id} not ready for download. Status: {status}")
        raise HTTPException(
            status_code=400,
            detail=f"Video {video_id} is not ready for download. Status: {status.get('status')}"
        )
    
    # Get the output file path
    result = status.get("result", {})
    output_file = result.get("output_file")
    
    if not output_file:
        print(f"No output file in result for video {video_id}")
        # Try to construct the default path
        output_file = os.path.join(settings.UPLOAD_DIR, "processed", video_id, f"final_hype.mp4")
        print(f"Trying default output file path: {output_file}")
    
    if not os.path.exists(output_file):
        print(f"Output file not found at {output_file}")
        raise HTTPException(
            status_code=404,
            detail=f"Processed video file not found at {output_file}"
        )
    
    print(f"Serving file: {output_file}")
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

def update_processing_status(video_id: str, status_updates: Dict[str, Any]):
    """Helper function to safely update processing status"""
    if video_id not in processing_status:
        processing_status[video_id] = {}
    
    # Always include timestamp
    status_updates["last_updated"] = datetime.now().isoformat()
    
    # If this is an error status, ensure we have an error timestamp
    if status_updates.get("status") == "error" and "error_time" not in status_updates:
        status_updates["error_time"] = status_updates["last_updated"]
    
    processing_status[video_id].update(status_updates)
    
    # Log the status update
    print(f"Status update for {video_id}: {status_updates}")


async def process_video_background(
    video_id: str,
    file_path: str,
    personality: str,
    language: str
):
    """
    Background task to process the video asynchronously.
    
    This function handles the entire video processing pipeline including:
    1. Input validation
    2. Video analysis
    3. Commentary generation
    4. Video processing
    5. Final output generation
    
    Args:
        video_id: Unique identifier for the video
        file_path: Path to the uploaded video file
        personality: Commentary personality to use
        language: Language for the commentary
    """
    start_time = datetime.now()
    pipeline = None
    
    try:
        print(f"\n=== Starting background processing for video {video_id} ===")
        print(f"Start time: {start_time}")
        print(f"File path: {file_path}")
        print(f"Personality: {personality}, Language: {language}")
        
        # Initialize processing status
        update_processing_status(video_id, {
            "status": "processing",
            "progress": 0,
            "message": "Initializing video processing...",
            "start_time": start_time.isoformat(),
            "file_path": file_path,
            "personality": personality,
            "language": language
        })
        
        # Validate input file
        if not os.path.exists(file_path):
            error_msg = f"Input video file not found: {file_path}"
            print(f"ERROR: {error_msg}")
            update_processing_status(video_id, {
                "status": "error",
                "progress": 0,
                "message": error_msg,
                "error": error_msg
            })
            return
        
        # Get file info
        file_size = os.path.getsize(file_path)
        print(f"Processing video file. Size: {file_size} bytes")
        
        # Create pipeline instance
        update_processing_status(video_id, {
            "progress": 5,
            "message": "Initializing processing pipeline..."
        })
        
        pipeline = ProcessingPipeline()
        
        # Process the video in stages
        stages = [
            (10, "Analyzing video content..."),
            (30, "Detecting key moments..."),
            (50, "Generating commentary..."),
            (70, "Processing video effects..."),
            (90, "Finalizing output...")
        ]
        
        for progress, message in stages:
            update_processing_status(video_id, {
                "progress": progress,
                "message": message
            })
            
            # Simulate processing time for each stage
            await asyncio.sleep(1)
        
        # Process the video
        update_processing_status(video_id, {
            "progress": 95,
            "message": "Processing video..."
        })
        
        result = await pipeline.process_video(
            video_path=file_path,
            personality=personality,
            language=language,
            vertical_format=True
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Update status to completed
        update_processing_status(video_id, {
            "status": "completed",
            "progress": 100,
            "message": "Video processing completed successfully",
            "processing_time_seconds": processing_time,
            "completed_at": datetime.now().isoformat(),
            "result": {
                "output_file": result.get("output_file", ""),
                "message": result.get("message", "Processing complete"),
                "events_detected": result.get("events", [])
            }
        })
        
        print(f"Successfully processed video {video_id} in {processing_time:.2f} seconds")
        
    except Exception as e:
        import traceback
        error_msg = f"Error processing video: {str(e)}"
        print(f"ERROR: {error_msg}")
        traceback.print_exc()
        
        # Update status with error
        update_processing_status(video_id, {
            "status": "error",
            "message": error_msg,
            "error": str(e),
            "error_traceback": traceback.format_exc()
        })
        
    finally:
        # Clean up resources if needed
        if pipeline:
            # Add any cleanup code for the pipeline here
            pass


