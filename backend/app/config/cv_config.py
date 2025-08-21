from pydantic import BaseModel, Field
from typing import Dict, List, Tuple, Optional

class CVConfig(BaseModel):
    """Configuration for computer vision settings."""
    
    # YOLO model configuration
    model_name: str = "yolov8n.pt"  # Default model
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    
    # Detection parameters
    min_confidence_person: float = 0.5
    min_confidence_ball: float = 0.3
    min_confidence_hoop: float = 0.4
    
    # Tracking parameters
    max_cosine_distance: float = 0.3
    max_iou_distance: float = 0.7
    max_age: int = 30  # frames
    n_init: int = 3
    
    # Play detection parameters
    dunk_confidence: float = 0.6
    three_point_confidence: float = 0.6
    layup_confidence: float = 0.55
    steal_confidence: float = 0.5
    block_confidence: float = 0.5
    
    # Court detection parameters
    court_line_color: Tuple[int, int, int] = (255, 255, 255)  # White
    court_line_thickness: int = 2
    
    # Visualization settings
    draw_boxes: bool = True
    show_confidence: bool = True
    show_track_ids: bool = True
    
    # Performance settings
    process_every_n_frames: int = 5
    frame_skip: int = 1
    
    # Output settings
    save_annotated_frames: bool = False
    output_video_quality: int = 18  # Lower is better quality, 18-28 is a good range
    
    # Class IDs (COCO dataset)
    class_ids: Dict[str, int] = {
        'person': 0,
        'sports_ball': 32,
        'basketball_hoop': 37  # Note: May need custom training for better hoop detection
    }
    
    # Play types to detect
    play_types: List[str] = [
        'dunk',
        'three_pointer',
        'layup',
        'steal',
        'block',
        'assist',
        'rebound',
        'turnover'
    ]
    
    # Court dimensions (standard NBA)
    court_dimensions: Dict[str, float] = {
        'length_ft': 94.0,
        'width_ft': 50.0,
        'key_width_ft': 16.0,
        'three_point_line_ft': 23.75,
        'hoop_height_ft': 10.0
    }

# Create a default configuration instance
DEFAULT_CV_CONFIG = CVConfig()
