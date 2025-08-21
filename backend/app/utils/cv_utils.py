import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import os
from ultralytics import YOLO
import torch

class BasketballCV:
    def __init__(self, model_path: str = None):
        """
        Initialize the basketball computer vision system.
        
        Args:
            model_path: Path to custom YOLO model weights. If None, uses default COCO model.
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        
        # Load YOLO model
        self.model = YOLO('yolov8n.pt' if model_path is None else model_path)
        self.model.to(self.device)
        
        # Define basketball-related classes (COCO dataset classes)
        self.basketball_class_id = 1  # Person
        self.ball_class_id = 32       # Sports ball
        self.hoop_class_id = 37       # Sports ball (we'll need to detect hoops separately)
        
        # Court dimensions and calibration data
        self.court_corners = None
        self.court_dimensions = None
        
    def detect_players_and_ball(self, frame: np.ndarray) -> Dict:
        """
        Detect players and ball in a single frame.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            Dictionary containing detected objects and their properties
        """
        # Run YOLO inference
        results = self.model(frame, verbose=False)
        
        detections = {
            'players': [],
            'ball': None,
            'hoop': None
        }
        
        # Process detections
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            
            for box, conf, class_id in zip(boxes, confs, class_ids):
                x1, y1, x2, y2 = box.astype(int)
                width = x2 - x1
                height = y2 - y1
                
                # Check if detection is a person (player)
                if class_id == self.basketball_class_id and conf > 0.5:
                    detections['players'].append({
                        'bbox': (x1, y1, width, height),
                        'confidence': float(conf),
                        'center': (int((x1 + x2) / 2), int((y1 + y2) / 2))
                    })
                # Check if detection is a ball
                elif class_id == self.ball_class_id and conf > 0.3:
                    detections['ball'] = {
                        'bbox': (x1, y1, width, height),
                        'confidence': float(conf),
                        'center': (int((x1 + x2) / 2), int((y1 + y2) / 2))
                    }
        
        return detections
    
    def track_objects(self, frame: np.ndarray, previous_detections: Dict) -> Dict:
        """
        Track objects between frames using simple IoU tracking.
        
        Args:
            frame: Current frame
            previous_detections: Detections from previous frame
            
        Returns:
            Updated detections with tracking IDs
        """
        current_detections = self.detect_players_and_ball(frame)
        
        # Simple tracking by finding closest match in previous frame
        if 'players' in previous_detections and 'players' in current_detections:
            for i, player in enumerate(current_detections['players']):
                if i < len(previous_detections['players']):
                    player['track_id'] = previous_detections['players'][i].get('track_id', i)
                else:
                    player['track_id'] = len(previous_detections['players']) + i
        
        return current_detections
    
    def detect_plays(self, frame: np.ndarray, detections: Dict) -> List[Dict]:
        """
        Detect basketball plays based on object detections.
        
        Args:
            frame: Current frame
            detections: Current frame detections
            
        Returns:
            List of detected plays with timestamps and confidence
        """
        plays = []
        
        # Check for dunk (player near rim with ball)
        if detections['ball'] and detections['players']:
            ball_center = detections['ball']['center']
            
            for player in detections['players']:
                player_center = player['center']
                # Simple distance check (in a real implementation, we'd use court calibration)
                distance = np.sqrt((player_center[0] - ball_center[0])**2 + 
                                 (player_center[1] - ball_center[1])**2)
                
                # If ball is close to player and player is high up (simple dunk detection)
                if distance < 100 and player_center[1] < frame.shape[0] * 0.5:
                    plays.append({
                        'type': 'dunk',
                        'confidence': min(detections['ball']['confidence'], player['confidence']),
                        'player_id': player.get('track_id', 0),
                        'position': player_center
                    })
        
        return plays
    
    def process_video(self, video_path: str, output_dir: str) -> Dict:
        """
        Process a basketball video to detect plays.
        
        Args:
            video_path: Path to input video
            output_dir: Directory to save output files
            
        Returns:
            Dictionary containing analysis results
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        print(f"Processing video: {video_path}")
        print(f"FPS: {fps}, Frames: {frame_count}, Duration: {duration:.2f}s")
        
        plays = []
        frame_number = 0
        previous_detections = {'players': []}
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every 5th frame for efficiency
            if frame_number % 5 == 0:
                # Track objects
                detections = self.track_objects(frame, previous_detections)
                previous_detections = detections
                
                # Detect plays
                frame_plays = self.detect_plays(frame, detections)
                if frame_plays:
                    timestamp = frame_number / fps
                    for play in frame_plays:
                        play['timestamp'] = timestamp
                        plays.append(play)
            
            frame_number += 1
            
            # Show progress
            if frame_number % 100 == 0:
                print(f"Processed {frame_number}/{frame_count} frames")
        
        cap.release()
        
        # Process and return results
        return {
            'status': 'completed',
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'plays': plays,
            'output_dir': output_dir
        }
