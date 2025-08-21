"""
Training module for basketball analysis models.

This module contains utilities for training and fine-tuning computer vision models
for basketball play detection and analysis.
"""

from pathlib import Path

# Create necessary directories
DATA_DIR = Path(__file__).parent / 'data'
MODELS_DIR = Path(__file__).parent / 'models'
OUTPUT_DIR = Path(__file__).parent / 'output'

for directory in [DATA_DIR, MODELS_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Training configuration
class TrainingConfig:
    """Configuration for model training."""
    # Model architecture
    MODEL_NAME = 'yolov8n.pt'  # Base model to fine-tune
    IMG_SIZE = 640  # Input image size
    BATCH_SIZE = 16  # Batch size
    EPOCHS = 50  # Number of training epochs
    PATIENCE = 10  # Early stopping patience
    
    # Learning rate
    LR0 = 0.01  # Initial learning rate
    LRF = 0.01  # Final learning rate (lr0 * lrf)
    MOMENTUM = 0.937  # SGD momentum/Adam beta1
    WEIGHT_DECAY = 0.0005  # Optimizer weight decay
    
    # Dataset
    TRAIN_VAL_SPLIT = 0.8  # Train/validation split ratio
    
    # Augmentation
    HFLIP = 0.5  # Horizontal flip probability
    VFLIP = 0.1  # Vertical flip probability
    HSV_H = 0.015  # Image HSV-Hue augmentation (fraction)
    HSV_S = 0.7  # Image HSV-Saturation augmentation (fraction)
    HSV_V = 0.4  # Image HSV-Value augmentation (fraction)
    
    # Training resources
    DEVICE = '0'  # CUDA device, i.e. 0 or 0,1,2,3 or cpu
    WORKERS = 8  # Number of worker threads for data loading
    
    # Output
    PROJECT = 'basketball_analysis'
    NAME = 'yolov8n_basketball'
    EXIST_OK = False  # Whether to overwrite existing output
    
    def to_dict(self):
        """Convert config to dictionary for YOLO training."""
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}

# Initialize default config
DEFAULT_CONFIG = TrainingConfig()
