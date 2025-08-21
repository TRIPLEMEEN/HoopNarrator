"""
Basketball Detection Training Script

This script handles training a YOLOv8 model on the Roboflow Basketball dataset with CSV support.
"""
import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import torch
from ultralytics import YOLO
from tqdm import tqdm

from app.config.datasets import get_dataset_config
from app.training.roboflow_loader import RoboflowDatasetLoader

class BasketballTrainer:
    """Trainer for basketball detection models with CSV support."""
    
    def __init__(self, config_path: str):
        """Initialize the trainer.
        
        Args:
            config_path: Path to the training configuration YAML file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.device = self._get_device()
        
        # Initialize dataset loader
        self.dataset_config = get_dataset_config("roboflow")
        self.loader = RoboflowDatasetLoader(self.dataset_config)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load training configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_device(self) -> str:
        """Get the device to use for training."""
        if self.config['training'].get('device'):
            return self.config['training']['device']
        return 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    def prepare_data(self, force_download: bool = False) -> bool:
        """Prepare the dataset for training.
        
        Args:
            force_download: If True, force re-download and re-process the dataset
            
        Returns:
            bool: True if preparation was successful
        """
        print("Preparing dataset...")
        
        # Download and prepare dataset
        if not self.loader.download_dataset(force=force_download):
            print("Failed to prepare dataset")
            return False
        
        # Verify dataset
        if not self.loader.verify_dataset():
            print("Dataset verification failed")
            return False
            
        print("Dataset prepared successfully!")
        return True
    
    def train(self, resume: bool = False):
        """Train the model.
        
        Args:
            resume: If True, resume training from the last checkpoint
        """
        print(f"Starting training on {self.device}...")
        
        # Get dataset info
        dataset_info = self.loader.get_dataset_info()
        
        # Update config with dataset info
        self.config['model']['nc'] = dataset_info['nc']  # Number of classes
        
        # Load YOLO model
        model_size = self.config['model']['size']
        model = YOLO(f'yolov8{model_size}.pt')
        
        # Prepare training arguments
        train_args = {
            'data': str(self.loader.yolo_dir / 'data.yaml'),
            'epochs': self.config['model']['epochs'],
            'batch': self.config['model']['batch'],
            'imgsz': self.config['model']['imgsz'],
            'device': self.device,
            'workers': self.config['training']['workers'],
            'project': self.config['training']['project'],
            'name': self.config['training']['name'],
            'exist_ok': self.config['training']['exist_ok'],
            'resume': resume,
            'optimizer': self.config['model']['optimizer'],
            'lr0': self.config['model']['lr0'],
            'lrf': self.config['model']['lrf'],
            'momentum': self.config['model']['momentum'],
            'weight_decay': self.config['model']['weight_decay'],
            'warmup_epochs': self.config['model']['warmup_epochs'],
            'warmup_momentum': self.config['model']['warmup_momentum'],
            'warmup_bias_lr': self.config['model']['warmup_bias_lr'],
            'box': 0.05,  # box loss gain
            'cls': 0.5,   # cls loss gain
            'dfl': 1.5,   # dfl loss gain
            'hsv_h': self.config['augment']['hsv_h'],
            'hsv_s': self.config['augment']['hsv_s'],
            'hsv_v': self.config['augment']['hsv_v'],
            'degrees': self.config['augment']['degrees'],
            'translate': self.config['augment']['translate'],
            'scale': self.config['augment']['scale'],
            'shear': self.config['augment']['shear'],
            'perspective': self.config['augment']['perspective'],
            'flipud': self.config['augment']['flipud'],
            'fliplr': self.config['augment']['fliplr'],
            'mosaic': self.config['augment']['mosaic'],
            'mixup': self.config['augment']['mixup'],
        }
        
        # Start training
        results = model.train(**train_args)
        
        print("Training completed!")
        return results

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train a YOLOv8 model on the Roboflow Basketball dataset')
    parser.add_argument('--config', type=str, default='app/training/configs/roboflow_basketball.yaml',
                       help='Path to training configuration YAML file')
    parser.add_argument('--resume', action='store_true',
                       help='Resume training from the last checkpoint')
    parser.add_argument('--force-download', action='store_true',
                       help='Force re-download and re-process the dataset')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Initialize trainer
    trainer = BasketballTrainer(args.config)
    
    # Prepare data
    if not trainer.prepare_data(force_download=args.force_download):
        print("Failed to prepare data. Exiting...")
        return 1
    
    # Train model
    trainer.train(resume=args.resume)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
