import os
import cv2
import json
import random
import shutil
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import yaml

from . import DATA_DIR

@dataclass
class BoundingBox:
    """Bounding box with class label and confidence."""
    x: float  # center x (normalized)
    y: float  # center y (normalized)
    w: float  # width (normalized)
    h: float  # height (normalized)
    class_id: int
    confidence: float = 1.0
    
    @classmethod
    def from_yolo(cls, line: str) -> 'BoundingBox':
        """Create BoundingBox from YOLO format line."""
        parts = line.strip().split()
        if len(parts) < 5:
            raise ValueError(f"Invalid YOLO format: {line}")
            
        class_id = int(parts[0])
        x, y, w, h = map(float, parts[1:5])
        confidence = float(parts[5]) if len(parts) > 5 else 1.0
        
        return cls(x=x, y=y, w=w, h=h, class_id=class_id, confidence=confidence)
    
    def to_yolo(self) -> str:
        """Convert to YOLO format string."""
        return f"{self.class_id} {self.x:.6f} {self.y:.6f} {self.w:.6f} {self.h:.6f} {self.confidence:.6f}"

class BasketballDataset:
    """Class for handling basketball dataset preparation and augmentation."""
    
    def __init__(self, data_dir: Union[str, Path] = None):
        """Initialize with dataset directory."""
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR / 'basketball'
        self.images_dir = self.data_dir / 'images'
        self.labels_dir = self.data_dir / 'labels'
        
        # Create directories if they don't exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Class names and IDs
        self.classes = {
            0: 'player',
            1: 'ball',
            2: 'hoop',
            3: 'backboard',
            4: 'court_line'
        }
        self.class_to_id = {v: k for k, v in self.classes.items()}
    
    def load_dataset(self, dataset_path: Union[str, Path] = None):
        """Load dataset from a directory or file.
        
        Args:
            dataset_path: Path to dataset directory or annotation file.
        """
        if dataset_path is None:
            dataset_path = self.data_dir
            
        dataset_path = Path(dataset_path)
        
        if dataset_path.is_file():
            # Load from COCO or other annotation format
            if dataset_path.suffix == '.json':
                self._load_coco(dataset_path)
            else:
                raise ValueError(f"Unsupported annotation format: {dataset_path.suffix}")
        else:
            # Load from YOLO format directory
            self._load_yolo(dataset_path)
    
    def _load_yolo(self, data_dir: Path):
        """Load dataset in YOLO format."""
        # This is a placeholder. In a real implementation, you would:
        # 1. Scan for image files
        # 2. Find corresponding label files
        # 3. Parse the annotations
        pass
    
    def _load_coco(self, annotation_file: Path):
        """Load dataset from COCO format annotations."""
        # This is a placeholder. In a real implementation, you would:
        # 1. Load the COCO JSON file
        # 2. Convert annotations to YOLO format
        # 3. Save images and labels in the appropriate directories
        pass
    
    def split_dataset(self, train_ratio: float = 0.8, val_ratio: float = 0.1):
        """Split dataset into train/val/test sets.
        
        Args:
            train_ratio: Ratio of training data (0-1).
            val_ratio: Ratio of validation data (0-1).
        """
        # Get list of all images
        image_files = list(self.images_dir.glob('*.*'))
        random.shuffle(image_files)
        
        # Calculate split indices
        total = len(image_files)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        
        # Split into train/val/test
        splits = {
            'train': image_files[:train_end],
            'val': image_files[train_end:val_end],
            'test': image_files[val_end:]
        }
        
        # Create split directories
        for split in ['train', 'val', 'test']:
            # Create image directories
            img_dir = self.images_dir / split
            img_dir.mkdir(exist_ok=True)
            
            # Create label directories
            label_dir = self.labels_dir / split
            label_dir.mkdir(exist_ok=True)
            
            # Move files
            for img_path in splits[split]:
                # Move image
                dst_img = img_dir / img_path.name
                if img_path != dst_img:
                    shutil.copy2(img_path, dst_img)
                
                # Move corresponding label
                label_path = self.labels_dir / f"{img_path.stem}.txt"
                if label_path.exists():
                    dst_label = label_dir / f"{img_path.stem}.txt"
                    if label_path != dst_label:
                        shutil.copy2(label_path, dst_label)
        
        # Create dataset YAML
        self._create_dataset_yaml()
    
    def _create_dataset_yaml(self):
        """Create YAML file for YOLO training."""
        dataset_yaml = {
            'path': str(self.data_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'names': self.classes,
            'nc': len(self.classes)
        }
        
        with open(self.data_dir / 'dataset.yaml', 'w') as f:
            yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    def augment(self):
        """Apply data augmentation to the dataset."""
        # This is a placeholder. In a real implementation, you would:
        # 1. Apply various augmentations (flips, rotations, color changes, etc.)
        # 2. Generate new images and corresponding annotations
        # 3. Add them to the training set
        pass

def prepare_basketball_dataset():
    """Prepare the basketball dataset for training."""
    # Initialize dataset
    dataset = BasketballDataset()
    
    # Load dataset (replace with actual path to your dataset)
    dataset_path = "path/to/your/dataset"  # Update this path
    if os.path.exists(dataset_path):
        dataset.load_dataset(dataset_path)
    else:
        print(f"Dataset not found at {dataset_path}. Using sample data.")
        # In a real implementation, you might download a sample dataset here
    
    # Split into train/val/test
    dataset.split_dataset(train_ratio=0.8, val_ratio=0.1)
    
    # Apply data augmentation
    dataset.augment()
    
    print("Dataset preparation complete!")

if __name__ == "__main__":
    prepare_basketball_dataset()
