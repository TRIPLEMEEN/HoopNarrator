import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from ultralytics import YOLO
import mediapipe as mp

class VideoProcessor:
    def __init__(self):
        # Initialize YOLO model
        self.model = YOLO('yolov8x.pt')  # Using YOLOv8x for better accuracy
        
        # Initialize MediaPipe for pose estimation
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Court and player detection classes
        self.court_class_id = 32  # sports ball
        self.person_class_id = 0  # person
        
    async def process_video(self, video_path: str, output_dir: str) -> Dict[str, Any]:
        """Process video and extract basketball events"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Initialize variables
        frame_number = 0
        events = []
        
        # Process video frame by frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process every 5th frame for performance
            if frame_number % 5 == 0:
                # Detect objects using YOLO
                results = self.model(frame, verbose=False)
                
                # Process detections
                for result in results:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    scores = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy()
                    
                    # Process each detection
                    for box, score, class_id in zip(boxes, scores, class_ids):
                        if score < 0.5:  # Confidence threshold
                            continue
                            
                        # Get class name
                        class_name = result.names[int(class_id)]
                        
                        # Process player detections
                        if int(class_id) == self.person_class_id:
                            # Use MediaPipe for pose estimation
                            results_pose = self.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            if results_pose.pose_landmarks:
                                # Extract key points of interest
                                landmarks = results_pose.pose_landmarks.landmark
                                
                                # Detect shooting motion (simplified)
                                if self._is_shooting(landmarks):
                                    events.append({
                                        "frame": frame_number,
                                        "time": frame_number / fps,
                                        "event": "shot_attempt",
                                        "confidence": float(score),
                                        "position": box.tolist()
                                    })
            
            frame_number += 1
            
            # For MVP, just process first 100 frames
            if frame_number >= 100:
                break
        
        # Release resources
        cap.release()
        
        # Save events to JSON
        output_path = os.path.join(output_dir, "events.json")
        with open(output_path, 'w') as f:
            json.dump(events, f, indent=2)
        
        return {
            "status": "completed",
            "events_found": len(events),
            "events_file": output_path,
            "total_frames_processed": frame_number
        }
    
    def _is_shooting(self, landmarks) -> bool:
        """Detect shooting motion based on pose landmarks"""
        # Simplified shooting detection
        try:
            # Get relevant landmarks
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            
            # Calculate angles
            # This is a simplified version - in production, you'd want more sophisticated detection
            arm_angle = self._calculate_angle(
                (right_shoulder.x, right_shoulder.y),
                (right_elbow.x, right_elbow.y),
                (right_wrist.x, right_wrist.y)
            )
            
            # Check if arm is in shooting position
            return 70 < arm_angle < 110
            
        except Exception as e:
            print(f"Error in shooting detection: {e}")
            return False
    
    @staticmethod
    def _calculate_angle(a, b, c):
        """Calculate angle between three points"""
        ba = (a[0] - b[0], a[1] - b[1])
        bc = (c[0] - b[0], c[1] - b[1])
        
        dot_product = ba[0] * bc[0] + ba[1] * bc[1]
        mag_ba = (ba[0] ** 2 + ba[1] ** 2) ** 0.5
        mag_bc = (bc[0] ** 2 + bc[1] ** 2) ** 0.5
        
        # Avoid division by zero
        if mag_ba * mag_bc == 0:
            return 0
            
        # Calculate angle in degrees
        angle = np.arccos(dot_product / (mag_ba * mag_bc))
        return np.degrees(angle)
