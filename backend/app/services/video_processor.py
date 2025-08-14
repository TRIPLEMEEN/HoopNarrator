import os
import numpy as np
from PIL import Image
from moviepy.editor import VideoFileClip
from typing import List, Dict, Any
from pathlib import Path

class VideoProcessor:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.current_dir, '../../temp')
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_video(self, video_path: str) -> Dict[str, Any]:
        """Process video and return analysis results."""
        try:
            # Get video metadata
            with VideoFileClip(video_path) as clip:
                fps = clip.fps
                frame_count = int(clip.duration * fps)
                width, height = clip.size

                # Process frames
                frames_data = []
                for t in np.arange(0, clip.duration, 1.0/fps):  # Process at 1fps
                    frame = clip.get_frame(t)
                    frame_img = Image.fromarray(frame)
                    
                    # Process frame (example: get dominant color)
                    dominant_color = self._get_dominant_color(frame_img)
                    
                    frames_data.append({
                        'timestamp': t,
                        'dominant_color': dominant_color,
                        # Add more frame analysis as needed
                    })

            return {
                'status': 'completed',
                'fps': fps,
                'frame_count': frame_count,
                'resolution': f"{width}x{height}",
                'frames_analyzed': len(frames_data),
                'analysis': frames_data
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def _get_dominant_color(self, image: Image.Image) -> tuple:
        """Get dominant color from an image using Pillow."""
        # Resize for faster processing
        image = image.resize((100, 100))
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # Get colors and count them
        colors = image.getcolors(maxcolors=10000)
        if not colors:
            return (0, 0, 0)
        # Get the most frequent color
        most_frequent = max(colors, key=lambda x: x[0])
        return most_frequent[1]

    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)