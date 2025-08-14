from PIL import Image
import numpy as np
from moviepy.editor import VideoFileClip
import os

def get_video_info(video_path: str) -> dict:
    """Extract basic information about a video file using moviepy."""
    try:
        with VideoFileClip(video_path) as clip:
            return {
                "width": int(clip.w),
                "height": int(clip.h),
                "fps": clip.fps,
                "duration": clip.duration,
                "frame_count": int(clip.fps * clip.duration),
                "codec": "h264"  # Default, moviepy handles codec internally
            }
    except Exception as e:
        raise Exception(f"Error getting video info: {str(e)}")
    
def extract_frames(video_path: str, output_dir: str, frame_interval: int = 10) -> list:
    """Extract frames from video at specified intervals using moviepy."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        frame_paths = []
        
        with VideoFileClip(video_path) as clip:
            for t in np.arange(0, clip.duration, frame_interval):
                frame = clip.get_frame(t)
                frame_img = Image.fromarray(frame)
                frame_path = os.path.join(output_dir, f"frame_{int(t * 1000)}.jpg")
                frame_img.save(frame_path)
                frame_paths.append(frame_path)
        
        return frame_paths
    except Exception as e:
        raise Exception(f"Error extracting frames: {str(e)}")