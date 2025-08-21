"""
Roboflow Basketball Dataset Loader

This module provides functionality to download, convert, and load the Roboflow Basketball Players dataset
with support for CSV annotations.
"""
import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import requests
from tqdm import tqdm
import zipfile
import pandas as pd
import numpy as np
from PIL import Image

from app.config.datasets import ROBOFLOW_BASKETBALL

class RoboflowDatasetLoader:
    """Loader for Roboflow Basketball Players dataset with CSV support."""
    
    def __init__(self, config=ROBOFLOW_BASKETBALL):
        """Initialize the dataset loader.
        
        Args:
            config: Dataset configuration object
        """
        self.config = config
        self.dataset_dir = config.local_dir
        self.dataset_zip = self.dataset_dir / "dataset.zip"
        self.dataset_url = "https://universe.roboflow.com/ds/4RZIXRJ6Uw?key=YOUR_API_KEY"  # Replace with actual URL
        
        # CSV to YOLO converter configuration
        self.class_map = {name: i for i, name in config.classes.items()}
        self.csv_path = self.dataset_dir / "_annotations.csv"
        self.images_dir = self.dataset_dir / "images"
        self.yolo_dir = self.dataset_dir / "yolo_format"
        
    def download_dataset(self, force: bool = False) -> bool:
        """Download and prepare the Roboflow dataset.
        
        Args:
            force: If True, force re-download even if files exist
            
        Returns:
            bool: True if download and preparation was successful
        """
        # Check if dataset already exists in YOLO format
        if not force and self._check_yolo_format_exists():
            print(f"Dataset already prepared in YOLO format at {self.yolo_dir}")
            return True
            
        # Create dataset directory
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the dataset if needed
        if not self._download_roboflow_dataset():
            return False
            
        # Convert to YOLO format
        if not self._convert_to_yolo_format():
            return False
            
        return True
    
    def _check_yolo_format_exists(self) -> bool:
        """Check if the dataset is already in YOLO format."""
        required_dirs = [
            self.yolo_dir / "train" / "images",
            self.yolo_dir / "train" / "labels",
            self.yolo_dir / "val" / "images",
            self.yolo_dir / "val" / "labels",
            self.yolo_dir / "test" / "images",
            self.yolo_dir / "test" / "labels",
        ]
        return all(d.exists() and any(d.iterdir()) for d in required_dirs)
    
    def _download_roboflow_dataset(self) -> bool:
        """Download the Roboflow dataset."""
        print(f"Downloading Roboflow Basketball dataset to {self.dataset_dir}...")
        
        try:
            # Download the dataset
            response = requests.get(self.dataset_url, stream=True)
            response.raise_for_status()
            
            # Save the zip file
            with open(self.dataset_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract the dataset
            print("Extracting dataset...")
            with zipfile.ZipFile(self.dataset_zip, 'r') as zip_ref:
                zip_ref.extractall(self.dataset_dir)
            
            # Clean up zip file
            self.dataset_zip.unlink()
            
            print("Dataset downloaded and extracted successfully!")
            return True
            
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            if self.dataset_zip.exists():
                self.dataset_zip.unlink()
            return False
    
    def _convert_to_yolo_format(self) -> bool:
        """Convert the downloaded dataset to YOLO format."""
        print("Converting dataset to YOLO format...")
        
        try:
            # Create YOLO directory structure
            for split in ['train', 'val', 'test']:
                (self.yolo_dir / split / 'images').mkdir(parents=True, exist_ok=True)
                (self.yolo_dir / split / 'labels').mkdir(parents=True, exist_ok=True)
            
            # Process CSV file
            if not self.csv_path.exists():
                raise FileNotFoundError(f"CSV annotations not found at {self.csv_path}")
                
            # Read CSV file
            df = pd.read_csv(self.csv_path)
            
            # Split into train/val/test
            image_files = df['filename'].unique()
            np.random.shuffle(image_files)
            
            n_total = len(image_files)
            n_train = int(n_total * 0.7)
            n_val = int(n_total * 0.15)
            
            splits = {
                'train': image_files[:n_train],
                'val': image_files[n_train:n_train + n_val],
                'test': image_files[n_train + n_val:]
            }
            
            # Process each split
            for split, files in splits.items():
                print(f"Processing {split} split...")
                split_df = df[df['filename'].isin(files)]
                
                for _, row in tqdm(split_df.iterrows(), total=len(split_df), desc=f"Processing {split}"):
                    # Process image
                    img_path = self.images_dir / row['filename']
                    if not img_path.exists():
                        print(f"Warning: Image not found: {img_path}")
                        continue
                        
                    # Get image dimensions
                    with Image.open(img_path) as img:
                        img_width, img_height = img.size
                    
                    # Create label file
                    label_path = self.yolo_dir / split / 'labels' / f"{img_path.stem}.txt"
                    
                    # Get all annotations for this image
                    img_annots = split_df[split_df['filename'] == row['filename']]
                    
                    with open(label_path, 'w') as f:
                        for _, annot in img_annots.iterrows():
                            # Convert to YOLO format
                            class_name = annot['class']
                            if class_name not in self.class_map:
                                print(f"Warning: Unknown class '{class_name}'. Skipping...")
                                continue
                                
                            class_id = self.class_map[class_name]
                            
                            # Convert bbox to YOLO format
                            x_center = (annot['xmin'] + annot['width'] / 2) / img_width
                            y_center = (annot['ymin'] + annot['height'] / 2) / img_height
                            width = annot['width'] / img_width
                            height = annot['height'] / img_height
                            
                            # Write to label file
                            f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
                    
                    # Copy image to YOLO directory
                    dest_img_path = self.yolo_dir / split / 'images' / row['filename']
                    shutil.copy2(img_path, dest_img_path)
            
            # Create YAML configuration
            self._create_yaml_config()
            
            print("Dataset converted to YOLO format successfully!")
            return True
            
        except Exception as e:
            print(f"Error converting dataset: {e}")
            return False
    
    def _create_yaml_config(self):
        """Create YAML configuration file for the YOLO dataset."""
        yaml_content = {
            'path': str(self.yolo_dir),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': len(self.class_map),
            'names': list(self.class_map.keys())
        }
        
        yaml_path = self.yolo_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)
        
        print(f"Created YAML configuration at {yaml_path}")
    
    def get_dataset_info(self) -> Dict:
        """Get information about the dataset.
        
        Returns:
            Dict containing dataset information
        """
        yaml_path = self.yolo_dir / 'data.yaml'
        if not yaml_path.exists():
            raise FileNotFoundError(f"Dataset YAML not found at {yaml_path}")
            
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_split_paths(self, split: str = 'train') -> Tuple[List[str], List[str]]:
        """Get paths to images and labels for a dataset split.
        
        Args:
            split: One of 'train', 'val', 'test'
            
        Returns:
            Tuple of (image_paths, label_paths)
        """
        if split not in ['train', 'val', 'test']:
            raise ValueError("split must be one of 'train', 'val', 'test'")
            
        split_dir = self.yolo_dir / split
        img_dir = split_dir / 'images'
        label_dir = split_dir / 'labels'
        
        if not img_dir.exists() or not label_dir.exists():
            raise FileNotFoundError(
                f"Image or label directory not found in {split_dir}"
            )
        
        # Get all image files
        img_exts = ['.jpg', '.jpeg', '.png']
        img_paths = [f for f in img_dir.iterdir() if f.suffix.lower() in img_exts]
        
        # Get corresponding label files
        label_paths = []
        for img_path in img_paths:
            label_path = label_dir / f"{img_path.stem}.txt"
            if label_path.exists():
                label_paths.append(label_path)
            else:
                print(f"Warning: Label not found for {img_path.name}")
        
        return [str(p) for p in img_paths], [str(p) for p in label_paths]
    
    def verify_dataset(self) -> bool:
        """Verify that the dataset is properly downloaded and structured.
        
        Returns:
            bool: True if dataset is valid, False otherwise
        """
        try:
            # Check YOLO format directories
            required_dirs = [
                self.yolo_dir / 'train' / 'images',
                self.yolo_dir / 'train' / 'labels',
                self.yolo_dir / 'val' / 'images',
                self.yolo_dir / 'val' / 'labels',
                self.yolo_dir / 'test' / 'images',
                self.yolo_dir / 'test' / 'labels',
            ]
            
            for d in required_dirs:
                if not d.exists() or not any(d.iterdir()):
                    print(f"Missing or empty directory: {d}")
                    return False
            
            # Check dataset info
            self.get_dataset_info()
            
            # Check train/val/test splits
            for split in ['train', 'val', 'test']:
                self.get_split_paths(split)
                
            return True
            
        except Exception as e:
            print(f"Dataset verification failed: {e}")
            return False

# Example usage
if __name__ == "__main__":
    loader = RoboflowDatasetLoader()
    
    # Download the dataset (only needs to be done once)
    if not loader.download_dataset():
        print("Failed to download dataset")
        exit(1)
    
    # Verify the dataset
    if not loader.verify_dataset():
        print("Dataset verification failed")
        exit(1)
    
    # Get dataset info
    try:
        info = loader.get_dataset_info()
        print(f"Dataset info: {info}")
        
        # Get paths for training data
        img_paths, label_paths = loader.get_split_paths('train')
        print(f"Found {len(img_paths)} training images")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
