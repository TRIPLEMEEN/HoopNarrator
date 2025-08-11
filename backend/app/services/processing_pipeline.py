import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import json

from ..core.config import settings
from .video_processor import VideoProcessor
from .commentary_generator import CommentaryGenerator
from .voice_generator import VoiceGenerator
from ..utils.video_utils import (
    get_video_info,
    extract_frames,
    combine_audio_video,
    create_vertical_video
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingPipeline:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.commentary_generator = CommentaryGenerator()
        self.voice_generator = VoiceGenerator()
        
        # Create necessary directories
        self.upload_dir = settings.UPLOAD_DIR
        self.output_dir = os.path.join(settings.UPLOAD_DIR, "processed")
        self.temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
        
        for directory in [self.upload_dir, self.output_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
    
    async def process_video(
        self,
        video_path: str,
        personality: str = "hype",
        language: str = "en",
        vertical_format: bool = True
    ) -> Dict[str, Any]:
        """
        Process a video through the entire pipeline:
        1. Extract frames and analyze with computer vision
        2. Generate commentary based on detected events
        3. Generate voiceover from commentary
        4. Combine with original video
        """
        try:
            # Step 1: Get video info
            video_info = get_video_info(video_path)
            video_id = Path(video_path).stem
            
            # Create output directory for this video
            video_output_dir = os.path.join(self.output_dir, video_id)
            os.makedirs(video_output_dir, exist_ok=True)
            
            # Step 2: Process video with computer vision
            logger.info("Processing video with computer vision...")
            events = await self.video_processor.process_video(video_path, video_output_dir)
            
            # Step 3: Generate commentary
            logger.info("Generating commentary...")
            commentary_result = await self.commentary_generator.generate_commentary(
                events=events,
                personality=personality,
                context={"video_info": video_info}
            )
            
            if commentary_result["status"] != "success":
                raise Exception(f"Failed to generate commentary: {commentary_result.get('message')}")
            
            # Save commentary to file
            commentary_file = os.path.join(video_output_dir, "commentary.txt")
            with open(commentary_file, "w") as f:
                f.write(commentary_result["commentary"])
            
            # Step 4: Generate voiceover
            logger.info("Generating voiceover...")
            voiceover_result = await self.voice_generator.generate_voiceover(
                text=commentary_result["commentary"],
                personality=personality,
                output_path=video_output_dir
            )
            
            if voiceover_result["status"] != "success":
                raise Exception(f"Failed to generate voiceover: {voiceover_result.get('message')}")
            
            # Step 5: Combine audio with video
            logger.info("Combining audio with video...")
            voiceover_path = voiceover_result["output_file"]
            
            # Create a version of the video without audio
            video_no_audio = os.path.join(video_output_dir, "video_no_audio.mp4")
            self._remove_audio(video_path, video_no_audio)
            
            # Combine video with new audio
            final_output = os.path.join(video_output_dir, f"final_{personality}.mp4")
            combine_audio_video(video_no_audio, voiceover_path, final_output)
            
            # Create vertical version if requested
            if vertical_format:
                vertical_output = os.path.join(video_output_dir, f"final_{personality}_vertical.mp4")
                create_vertical_video(final_output, vertical_output)
                final_output = vertical_output
            
            # Clean up temporary files
            if os.path.exists(video_no_audio):
                os.remove(video_no_audio)
            
            return {
                "status": "completed",
                "video_id": video_id,
                "output_file": final_output,
                "commentary": commentary_result["commentary"],
                "personality": personality,
                "events_detected": len(events)
            }
            
        except Exception as e:
            logger.error(f"Error in processing pipeline: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "video_id": video_id if 'video_id' in locals() else None
            }
    
    def _remove_audio(self, input_path: str, output_path: str) -> None:
        """Remove audio from video"""
        import subprocess
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "copy",
            "-an",  # Disable audio
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            raise RuntimeError(f"Failed to remove audio: {error_msg}")
