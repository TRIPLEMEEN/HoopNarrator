import os
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union

import torch
from ultralytics import YOLO
import numpy as np
from sklearn.model_selection import train_test_split

from . import DATA_DIR, MODELS_DIR, OUTPUT_DIR, DEFAULT_CONFIG

class BasketballYOLOTrainer:
    """Class for training YOLO models on basketball data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the trainer with configuration.
        
        Args:
            config: Training configuration. If None, uses default config.
        """
        self.config = DEFAULT_CONFIG.to_dict()
        if config:
            self.config.update(config)
        
        # Set device
        self.device = 'cuda' if torch.cuda.is_available() and self.config['DEVICE'] != 'cpu' else 'cpu'
        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True
        
        # Initialize model
        self.model = None
        self._setup_paths()
    
    def _setup_paths(self):
        """Set up directory paths for training."""
        # Create run directory with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_dir = OUTPUT_DIR / f"{self.config['NAME']}_{timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=self.config['EXIST_OK'])
        
        # Create model save directory
        self.weights_dir = self.run_dir / 'weights'
        self.weights_dir.mkdir(exist_ok=True)
        
        # Create data directory structure
        self.data_dir = DATA_DIR / 'basketball'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths for YOLO dataset
        self.dataset_yaml = self.data_dir / 'dataset.yaml'
        self.images_dir = self.data_dir / 'images'
        self.labels_dir = self.data_dir / 'labels'
        
        # Create required directories
        for d in [self.images_dir, self.labels_dir]:
            d.mkdir(exist_ok=True)
    
    def prepare_dataset(self, data_path: Optional[Union[str, Path]] = None):
        """Prepare the dataset for YOLO training.
        
        Args:
            data_path: Path to the dataset. If None, uses default location.
        """
        if data_path is None:
            data_path = self.data_dir
        else:
            data_path = Path(data_path)
        
        # Check if dataset already exists
        if (self.images_dir / 'train').exists() and (self.labels_dir / 'train').exists():
            print("Dataset already prepared. Skipping preparation.")
            return
        
        # TODO: Implement dataset preparation logic here
        # This should include:
        # 1. Downloading/loading the dataset
        # 2. Splitting into train/val/test
        # 3. Converting annotations to YOLO format
        # 4. Creating dataset.yaml file
        
        # Example structure for dataset.yaml:
        dataset_yaml = {
            'path': str(self.data_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'names': {
                0: 'player',
                1: 'ball',
                2: 'hoop',
                3: 'backboard',
                4: 'court_line'
            },
            'nc': 5  # number of classes
        }
        
        # Save dataset YAML
        with open(self.dataset_yaml, 'w') as f:
            yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    def train(self):
        """Train the YOLO model on basketball data."""
        print(f"Starting training with config: {self.config}")
        
        # Load model
        model_path = MODELS_DIR / self.config['MODEL_NAME']
        if model_path.exists():
            print(f"Loading model from {model_path}")
            self.model = YOLO(model_path)
        else:
            print(f"Downloading {self.config['MODEL_NAME']}...")
            self.model = YOLO(self.config['MODEL_NAME'])
        
        # Set device
        self.model.to(self.device)
        
        # Prepare dataset
        self.prepare_dataset()
        
        # Train the model
        results = self.model.train(
            data=str(self.dataset_yaml),
            epochs=self.config['EPOCHS'],
            batch=self.config['BATCH_SIZE'],
            imgsz=self.config['IMG_SIZE'],
            device=self.config['DEVICE'],
            workers=self.config['WORKERS'],
            project=str(self.run_dir),
            name=self.config['NAME'],
            exist_ok=self.config['EXIST_OK'],
            lr0=self.config['LR0'],
            lrf=self.config['LRF'],
            momentum=self.config['MOMENTUM'],
            weight_decay=self.config['WEIGHT_DECAY'],
            hsv_h=self.config['HSV_H'],
            hsv_s=self.config['HSV_S'],
            hsv_v=self.config['HSV_V'],
            flipud=self.config['VFLIP'],
            fliplr=self.config['HFLIP'],
            patience=self.config['PATIENCE']
        )
        
        # Save the best model
        best_model_path = Path(self.model.trainer.best) if hasattr(self.model.trainer, 'best') else None
        if best_model_path and best_model_path.exists():
            shutil.copy2(best_model_path, self.weights_dir / 'best.pt')
        
        return results
    
    def evaluate(self, data_path: Optional[Union[str, Path]] = None):
        """Evaluate the trained model on test data.
        
        Args:
            data_path: Path to test data. If None, uses validation split.
        """
        if self.model is None:
            raise ValueError("No model loaded. Train or load a model first.")
        
        if data_path is None:
            data_path = self.dataset_yaml
        
        # Run evaluation
        metrics = self.model.val(
            data=str(data_path),
            batch=self.config['BATCH_SIZE'],
            imgsz=self.config['IMG_SIZE'],
            device=self.config['DEVICE'],
            workers=self.config['WORKERS']
        )
        
        return metrics

def train_basketball_detector():
    """Main function to train the basketball detector."""
    # Example of custom configuration
    config = {
        'MODEL_NAME': 'yolov8n.pt',
        'EPOCHS': 100,
        'BATCH_SIZE': 16,
        'IMG_SIZE': 640,
        'DEVICE': '0' if torch.cuda.is_available() else 'cpu',
        'NAME': 'basketball_detector',
    }
    
    # Initialize and train
    trainer = BasketballYOLOTrainer(config)
    trainer.train()
    
    # Evaluate
    metrics = trainer.evaluate()
    print(f"Evaluation metrics: {metrics}")

if __name__ == "__main__":
    train_basketball_detector()
