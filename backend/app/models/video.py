from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoBase(BaseModel):
    video_id: str = Field(..., description="Unique identifier for the video")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the video")
    size: int = Field(..., description="Size of the video file in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the video was uploaded")

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    status: VideoStatus = Field(..., description="Current processing status")
    progress: int = Field(0, description="Processing progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing results")
    error: Optional[str] = Field(None, description="Error message if processing failed")

class VideoProcessingResult(BaseModel):
    video_id: str = Field(..., description="ID of the processed video")
    status: VideoStatus = Field(..., description="Final processing status")
    output_file: Optional[str] = Field(None, description="Path to the processed video file")
    commentary: Optional[str] = Field(None, description="Generated commentary text")
    events_detected: int = Field(0, description="Number of basketball events detected")
    processing_time: Optional[float] = Field(None, description="Time taken to process in seconds")

class CommentaryStyle(BaseModel):
    id: str = Field(..., description="Unique identifier for the style")
    name: str = Field(..., description="Display name of the style")
    description: str = Field(..., description="Description of the commentary style")

class VideoProcessingRequest(BaseModel):
    video_id: str = Field(..., description="ID of the uploaded video")
    personality: str = Field("hype", description="Commentary style/personality to use")
    language: str = Field("en", description="Language for the commentary")
    vertical_format: bool = Field(True, description="Whether to format the output for vertical viewing")

class VideoProcessingResponse(BaseModel):
    video_id: str = Field(..., description="ID of the video being processed")
    status: str = Field(..., description="Current processing status")
    progress: int = Field(..., description="Processing progress percentage")
    message: str = Field(..., description="Status message")
    check_status_url: Optional[str] = Field(None, description="URL to check processing status")
