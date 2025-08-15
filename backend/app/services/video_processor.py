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

    async def process_video(self, video_path: str, output_dir: str) -> Dict[str, Any]:
        """Process video and return analysis results."""
        try:
            print(f"Processing video: {video_path}")
            print(f"Output directory: {output_dir}")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Get video metadata
            with VideoFileClip(video_path) as clip:
                fps = clip.fps
                duration = clip.duration
                frame_count = int(duration * fps)
                width, height = clip.size
                
                print(f"Video info: {width}x{height} @ {fps}fps, duration: {duration}s")
                
                # For now, just save the first frame as a test
                first_frame_path = os.path.join(output_dir, "first_frame.jpg")
                if frame_count > 0:
                    frame = clip.get_frame(0)  # Get first frame
                    frame_img = Image.fromarray(frame)
                    frame_img.save(first_frame_path)
                    print(f"Saved first frame to: {first_frame_path}")
            
            # For now, return a mock analysis
            return {
                'status': 'completed',
                'fps': fps,
                'frame_count': frame_count,
                'resolution': f"{width}x{height}",
                'message': 'Video processing completed',
                'output_dir': output_dir,
                'events': [
                    {
                        'type': 'dunk',
                        'timestamp': 2.5,
                        'confidence': 0.95,
                        'description': 'Impressive dunk!'
                    },
                    {
                        'type': 'three_pointer',
                        'timestamp': 5.1,
                        'confidence': 0.92,
                        'description': 'Nothing but net!'
                    }
                ]
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