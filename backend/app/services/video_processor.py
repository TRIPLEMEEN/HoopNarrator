import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import shutil
import logging

from app.utils.cv_utils import BasketballCV
from app.core.config import settings

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(settings.UPLOAD_DIR, 'temp')
        self.output_dir = os.path.join(settings.UPLOAD_DIR, 'processed')
        
        # Create necessary directories
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize computer vision system
        self.cv_system = BasketballCV()
        
        # Court detection parameters
        self.court_corners = None
        self.court_dimensions = None
        
    async def process_video(self, video_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Process a basketball video to detect plays and generate analysis.
        
        Args:
            video_path: Path to the input video file
            output_dir: Directory to save output files
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        start_time = datetime.now()
        video_id = Path(video_path).stem
        
        try:
            logger.info(f"Starting video processing for: {video_path}")
            
            # Create output directory for this video
            video_output_dir = os.path.join(output_dir, video_id)
            os.makedirs(video_output_dir, exist_ok=True)
            
            # Process video with computer vision
            logger.info("Running computer vision analysis...")
            analysis_results = self.cv_system.process_video(
                video_path=video_path,
                output_dir=video_output_dir
            )
            
            # Process and format the results
            plays = analysis_results.get('plays', [])
            
            # Generate video highlights
            highlight_path = self._generate_highlights(
                video_path=video_path,
                plays=plays,
                output_dir=video_output_dir
            )
            
            # Generate analysis report
            report = self._generate_analysis_report(
                plays=plays,
                video_info=analysis_results,
                output_dir=video_output_dir
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Video processing completed in {processing_time:.2f} seconds")
            
            return {
                'status': 'completed',
                'video_id': video_id,
                'plays': plays,
                'highlight_video': highlight_path,
                'analysis_report': report,
                'processing_time_seconds': processing_time,
                'output_dir': video_output_dir,
                'frame_count': analysis_results.get('frame_count', 0),
                'duration': analysis_results.get('duration', 0),
                'fps': analysis_results.get('fps', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f"Error processing video: {str(e)}",
                'video_id': video_id,
                'error': str(e)
            }
    
    def _generate_highlights(
        self,
        video_path: str,
        plays: List[Dict],
        output_dir: str,
        highlight_duration: float = 5.0
    ) -> str:
        """
        Generate a highlight reel from detected plays.
        
        Args:
            video_path: Path to the original video
            plays: List of detected plays
            output_dir: Directory to save the highlight video
            highlight_duration: Duration of each highlight in seconds
            
        Returns:
            Path to the generated highlight video
        """
        if not plays:
            logger.info("No plays detected for highlights")
            return ""
            
        highlight_path = os.path.join(output_dir, "highlights.mp4")
        
        # For now, we'll just copy the original video as a placeholder
        # In a real implementation, we would extract and concatenate highlight clips
        shutil.copy2(video_path, highlight_path)
        
        return highlight_path
    
    def _generate_analysis_report(
        self,
        plays: List[Dict],
        video_info: Dict,
        output_dir: str
    ) -> Dict:
        """
        Generate an analysis report from the detected plays.
        
        Args:
            plays: List of detected plays
            video_info: Video metadata
            output_dir: Directory to save the report
            
        Returns:
            Dictionary containing the analysis report
        """
        # Count plays by type
        play_counts = {}
        for play in plays:
            play_type = play.get('type', 'unknown')
            play_counts[play_type] = play_counts.get(play_type, 0) + 1
        
        # Generate report
        report = {
            'play_summary': play_counts,
            'total_plays': len(plays),
            'video_duration': video_info.get('duration', 0),
            'plays_per_minute': (len(plays) / (video_info.get('duration', 1) / 60)) if video_info.get('duration', 0) > 0 else 0,
            'play_timeline': [
                {
                    'type': play.get('type'),
                    'timestamp': play.get('timestamp'),
                    'confidence': play.get('confidence'),
                    'player_id': play.get('player_id')
                }
                for play in plays
            ]
        }
        
        # Save report to JSON file
        report_path = os.path.join(output_dir, 'analysis_report.json')
        with open(report_path, 'w') as f:
            import json
            json.dump(report, f, indent=2)
        
        return report
    
    def cleanup(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        
        # Recreate the temp directory
        os.makedirs(self.temp_dir, exist_ok=True)