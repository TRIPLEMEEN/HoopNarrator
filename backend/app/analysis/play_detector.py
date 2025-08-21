import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class PlayerState:
    """Tracks the state of a player across frames."""
    player_id: int
    position_history: deque = field(default_factory=lambda: deque(maxlen=30))  # Store last N positions
    speed_history: deque = field(default_factory=lambda: deque(maxlen=10))  # Store last N speeds
    current_speed: float = 0.0
    has_ball: bool = False
    last_ball_distance: float = float('inf')
    jump_state: str = 'grounded'  # 'grounded', 'ascending', 'descending', 'peak'
    jump_height: float = 0.0
    
    def update_position(self, position: Tuple[float, float], frame_idx: int):
        """Update player's position and calculate speed."""
        if self.position_history:
            prev_pos, prev_time = self.position_history[-1]
            dt = frame_idx - prev_time
            if dt > 0:
                distance = np.linalg.norm(np.array(position) - np.array(prev_pos))
                self.current_speed = distance / dt
                self.speed_history.append(self.current_speed)
        
        self.position_history.append((position, frame_idx))
        self._update_jump_state()
    
    def _update_jump_state(self):
        """Update the player's jump state based on vertical movement."""
        if len(self.position_history) < 2:
            return
            
        # Get vertical positions (assuming y increases downward)
        current_y = self.position_history[-1][0][1]
        prev_y = self.position_history[-2][0][1]
        
        # Simple jump detection
        dy = current_y - prev_y
        
        if dy < -2:  # Moving up
            if self.jump_state != 'ascending':
                self.jump_state = 'ascending'
                self.jump_height = 0.0
            else:
                self.jump_height += abs(dy)
        elif dy > 2:  # Moving down
            if self.jump_state in ['ascending', 'peak']:
                self.jump_state = 'descending'
        elif self.jump_state == 'ascending' and abs(dy) < 1:  # At peak
            self.jump_state = 'peak'
        elif self.jump_state == 'descending' and abs(dy) < 1:  # Landed
            self.jump_state = 'grounded'
            self.jump_height = 0.0

@dataclass
class BallState:
    """Tracks the state of the basketball across frames."""
    position_history: deque = field(default_factory=lambda: deque(maxlen=30))
    current_position: Optional[Tuple[float, float]] = None
    holder_id: Optional[int] = None  # ID of player holding the ball, None if in air
    in_air: bool = False
    shot_arc: List[Tuple[float, float]] = field(default_factory=list)  # For shot detection
    
    def update_position(self, position: Tuple[float, float], frame_idx: int):
        """Update ball's position and detect if it's in the air."""
        self.position_history.append((position, frame_idx))
        self.current_position = position
        
        # Simple in-air detection based on movement
        if len(self.position_history) > 1:
            prev_pos, _ = self.position_history[-2]
            distance = np.linalg.norm(np.array(position) - np.array(prev_pos))
            self.in_air = distance > 5.0  # Threshold for considering the ball in air
            
            if self.in_air and not self.shot_arc:
                self.shot_arc = [prev_pos, position]
            elif self.in_air:
                self.shot_arc.append(position)
            else:
                self.shot_arc = []
        
        if not self.in_air:
            self.holder_id = None

class PlayDetector:
    """Detects basketball plays like dunks, three-pointers, etc."""
    
    def __init__(self, court_dimensions: Dict[str, float] = None):
        """Initialize the play detector with court dimensions."""
        self.players: Dict[int, PlayerState] = {}
        self.ball = BallState()
        self.frame_idx = 0
        self.play_history = []
        self.court_dimensions = court_dimensions or {
            'length_ft': 94.0,
            'width_ft': 50.0,
            'three_point_line_ft': 23.75,
            'hoop_height_ft': 10.0
        }
        
        # Play detection thresholds
        self.DUNK_JUMP_HEIGHT = 1.5  # feet
        self.THREE_POINT_DISTANCE = self.court_dimensions['three_point_line_ft']
        self.SHOT_ARC_THRESHOLD = 1.5  # Minimum arc height in feet for a shot
    
    def update_frame(self, detections: List[Dict[str, Any]]):
        """Update the detector with new frame detections."""
        self.frame_idx += 1
        
        # Process detections
        current_players = {}
        ball_detected = False
        
        for det in detections:
            if det['class_name'] == 'player':
                player_id = det.get('track_id', det['bbox'][0])  # Use tracking ID or bbox as ID
                if player_id not in self.players:
                    self.players[player_id] = PlayerState(player_id=player_id)
                
                # Update player position
                bbox = det['bbox']
                center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                self.players[player_id].update_position(center, self.frame_idx)
                
                # Check if player has the ball
                if 'ball_bbox' in det:  # If using a model that detects ball possession
                    self.ball.holder_id = player_id
                    self.ball.in_air = False
                    self.players[player_id].has_ball = True
                
                current_players[player_id] = self.players[player_id]
                
            elif det['class_name'] == 'ball':
                ball_detected = True
                bbox = det['bbox']
                center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                self.ball.update_position(center, self.frame_idx)
        
        # Update ball holder if not detected
        if not ball_detected and self.ball.holder_id is None:
            self.ball.in_air = True
        
        # Detect plays
        self._detect_plays(current_players)
    
    def _detect_plays(self, current_players: Dict[int, PlayerState]):
        """Detect basketball plays based on current state."""
        # Check for dunks
        for player_id, player in current_players.items():
            if player.has_ball and player.jump_state == 'peak' and player.jump_height >= self.DUNK_JUMP_HEIGHT:
                self._record_play('dunk', player_id=player_id)
            
            # Check for three-pointers
            if player.has_ball and player.jump_state == 'descending':
                # Check distance from hoop (simplified)
                hoop_position = (self.court_dimensions['length_ft'] / 2, 0)
                player_pos = player.position_history[-1][0] if player.position_history else (0, 0)
                distance = np.linalg.norm(np.array(player_pos) - np.array(hoop_position))
                
                if distance >= self.THREE_POINT_DISTANCE:
                    self._record_play('three_pointer', player_id=player_id)
                else:
                    self._record_play('two_pointer', player_id=player_id)
            
            # Check for layups (simplified)
            if (player.has_ball and 
                player.jump_state in ['ascending', 'peak'] and 
                player.jump_height < self.DUNK_JUMP_HEIGHT and
                len(player.position_history) > 5):
                self._record_play('layup', player_id=player_id)
        
        # Check for steals and blocks (simplified)
        if self.ball.in_air and len(self.ball.shot_arc) > 3:
            # If ball changes direction significantly, it might be a block
            arc = np.array(self.ball.shot_arc)
            if len(arc) > 5:
                # Check for significant change in direction (block)
                dy = np.diff(arc[:, 1])
                if np.any(dy < -5):  # Ball suddenly goes up (blocked)
                    # Find nearest defender
                    if self.ball.current_position:
                        nearest_defender = min(
                            ((p_id, p) for p_id, p in current_players.items() if p_id != self.ball.holder_id),
                            key=lambda x: np.linalg.norm(np.array(x[1].position_history[-1][0]) - 
                                                       np.array(self.ball.current_position)),
                            default=(None, None)
                        )
                        if nearest_defender[0] is not None:
                            self._record_play('block', player_id=nearest_defender[0])
    
    def _record_play(self, play_type: str, player_id: int, confidence: float = 0.9):
        """Record a detected play."""
        play = {
            'frame': self.frame_idx,
            'play_type': play_type,
            'player_id': player_id,
            'confidence': confidence,
            'timestamp': self.frame_idx / 30.0  # Assuming 30 FPS
        }
        
        # Add additional context based on play type
        if play_type == 'dunk':
            play['jump_height'] = self.players[player_id].jump_height
        elif play_type in ['three_pointer', 'two_pointer']:
            play['distance'] = np.linalg.norm(
                np.array(self.players[player_id].position_history[-1][0]) - 
                np.array([self.court_dimensions['length_ft'] / 2, 0])
            )
        
        self.play_history.append(play)
        logger.info(f"Detected {play_type} by player {player_id} at frame {self.frame_idx}")
    
    def get_recent_plays(self, last_n_seconds: float = 5.0) -> List[Dict]:
        """Get plays from the last N seconds."""
        if not self.play_history:
            return []
        
        current_time = self.play_history[-1]['timestamp']
        min_timestamp = current_time - last_n_seconds
        
        return [p for p in self.play_history if p['timestamp'] >= min_timestamp]

# Example usage
if __name__ == "__main__":
    # Initialize detector
    detector = PlayDetector()
    
    # Simulate frame updates with detections
    for frame_idx in range(100):
        # Mock detections (in a real app, these would come from YOLO)
        detections = [
            {
                'class_name': 'player',
                'bbox': [100, 200, 150, 250],  # x1, y1, x2, y2
                'track_id': 1,
                'ball_bbox': [120, 220, 130, 230]  # If player has the ball
            },
            {
                'class_name': 'ball',
                'bbox': [125, 225, 135, 235],
                'track_id': 2
            }
        ]
        
        # Update detector
        detector.update_frame(detections)
        
        # Get recent plays
        if frame_idx % 10 == 0:  # Check every 10 frames
            recent_plays = detector.get_recent_plays()
            for play in recent_plays:
                print(f"Frame {frame_idx}: {play}")
