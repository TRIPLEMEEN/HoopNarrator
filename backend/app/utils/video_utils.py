import os
import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
import subprocess
import shlex


def get_video_info(video_path: str) -> Dict[str, Any]:
    """Extract basic information about a video file"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
            "codec": int(cap.get(cv2.CAP_PROP_FOURCC)),
            "format": Path(video_path).suffix.lower()
        }
    finally:
        cap.release()


def extract_frames(
    video_path: str,
    output_dir: str,
    frame_rate: int = 1,
    max_frames: Optional[int] = None
) -> List[str]:
    """Extract frames from video at specified frame rate"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(round(fps / frame_rate)) if frame_rate > 0 else 1
        
        frame_paths = []
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                if max_frames is not None and saved_count >= max_frames:
                    break
                    
                frame_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                saved_count += 1
                
            frame_count += 1
            
        return frame_paths
    finally:
        cap.release()


def combine_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    overwrite: bool = False
) -> bool:
    """Combine video and audio files using ffmpeg"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Build ffmpeg command
    cmd = (
        f"ffmpeg -y -i {shlex.quote(video_path)} -i {shlex.quote(audio_path)} "
        f"-c:v copy -c:a aac -strict experimental {shlex.quote(output_path)}"
    )
    
    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise RuntimeError(f"Failed to combine audio and video: {error_msg}")


def create_vertical_video(
    input_path: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    bg_color: str = "black"
) -> bool:
    """Convert video to vertical (9:16) aspect ratio"""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Build ffmpeg command
    cmd = (
        f"ffmpeg -y -i {shlex.quote(input_path)} "
        f"-vf \"scale={width}:-1,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:{bg_color}\" "
        f"-c:a copy {shlex.quote(output_path)}"
    )
    
    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise RuntimeError(f"Failed to create vertical video: {error_msg}")


def trim_video(
    input_path: str,
    output_path: str,
    start_time: float = 0,
    duration: Optional[float] = None,
    overwrite: bool = False
) -> bool:
    """Trim video to specified start time and duration"""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")
    
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Format time for ffmpeg (HH:MM:SS.mmm)
    def format_time(seconds: float) -> str:
        hh = int(seconds // 3600)
        mm = int((seconds % 3600) // 60)
        ss = seconds % 60
        return f"{hh:02d}:{mm:02d}:{ss:06.3f}"
    
    # Build ffmpeg command
    cmd = f"ffmpeg -y -ss {format_time(start_time)}"
    
    if duration is not None:
        cmd += f" -t {format_time(duration)}"
    
    cmd += f" -i {shlex.quote(input_path)} -c copy {shlex.quote(output_path)}"
    
    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise RuntimeError(f"Failed to trim video: {error_msg}")
