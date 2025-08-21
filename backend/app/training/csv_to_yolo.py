"""
CSV to YOLO Format Converter

This module provides functionality to convert CSV annotations to YOLO format.
"""
import csv
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from tqdm import tqdm

class CSVToYOLOConverter:
    """Converts CSV annotations to YOLO format."""
    
    def __init__(
        self,
        csv_path: str,
        images_dir: str,
        output_dir: str,
        class_map: Dict[str, int],
        image_ext: str = '.jpg'
    ):
        """Initialize the converter.
        
        Args:
            csv_path: Path to the CSV file containing annotations
            images_dir: Directory containing the images
            output_dir: Directory to save YOLO format annotations
            class_map: Dictionary mapping class names to class IDs
            image_ext: Image file extension (default: '.jpg')
        """
        self.csv_path = Path(csv_path)
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.class_map = class_map
        self.image_ext = image_ext
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _convert_bbox(
        self,
        x_min: float,
        y_min: float,
        width: float,
        height: float,
        img_width: int,
        img_height: int
    ) -> Tuple[float, float, float, float]:
        """Convert bounding box coordinates to YOLO format.
        
        YOLO format: [x_center, y_center, width, height] (normalized)
        """
        # Calculate center coordinates
        x_center = (x_min + width / 2) / img_width
        y_center = (y_min + height / 2) / img_height
        
        # Normalize width and height
        w_norm = width / img_width
        h_norm = height / img_height
        
        return x_center, y_center, w_norm, h_norm
    
    def convert(self, split_ratio: Tuple[float, float, float] = (0.7, 0.2, 0.1)):
        """Convert CSV annotations to YOLO format.
        
        Args:
            split_ratio: Tuple of (train, val, test) ratios
        """
        # Validate split ratios
        if abs(sum(split_ratio) - 1.0) > 1e-6:
            raise ValueError("Split ratios must sum to 1.0")
            
        # Read CSV file
        df = pd.read_csv(self.csv_path)
        
        # Group by image filename
        grouped = df.groupby('filename')
        
        # Shuffle and split the data
        image_files = list(grouped.groups.keys())
        n_total = len(image_files)
        n_train = int(n_total * split_ratio[0])
        n_val = int(n_total * split_ratio[1])
        
        # Split into train/val/test
        train_files = image_files[:n_train]
        val_files = image_files[n_train:n_train + n_val]
        test_files = image_files[n_train + n_val:]
        
        print(f"Splitting data: {len(train_files)} train, {len(val_files)} val, {len(test_files)} test")
        
        # Process each split
        self._process_split('train', train_files, grouped)
        self._process_split('val', val_files, grouped)
        self._process_split('test', test_files, grouped)
        
    def _process_split(self, split_name: str, filenames: List[str], grouped_df):
        """Process a single split (train/val/test)."""
        print(f"Processing {split_name} split...")
        
        # Create output directories
        split_dir = self.output_dir / split_name
        img_dir = split_dir / 'images'
        label_dir = split_dir / 'labels'
        
        img_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each image
        for filename in tqdm(filenames, desc=f"Processing {split_name}"):
            # Get image path and load image to get dimensions
            img_path = self.images_dir / filename
            if not img_path.exists():
                print(f"Warning: Image not found: {img_path}")
                continue
                
            # Get image dimensions (assuming all images have the same dimensions)
            # In a real implementation, you would read the image to get its dimensions
            # For now, we'll use placeholders - you'll need to update this
            img_width, img_height = 1280, 720  # Update with actual image dimensions
            
            # Copy image to output directory
            output_img_path = img_dir / filename
            shutil.copy2(img_path, output_img_path)
            
            # Create YOLO annotation file
            label_path = label_dir / f"{img_path.stem}.txt"
            with open(label_path, 'w') as f:
                # Get all annotations for this image
                annotations = grouped_df.get_group(filename)
                
                for _, row in annotations.iterrows():
                    # Get class ID
                    class_name = row['class']
                    if class_name not in self.class_map:
                        print(f"Warning: Unknown class '{class_name}'. Skipping...")
                        continue
                        
                    class_id = self.class_map[class_name]
                    
                    # Convert bbox to YOLO format
                    x_center, y_center, width, height = self._convert_bbox(
                        x_min=row['xmin'],
                        y_min=row['ymin'],
                        width=row['width'],
                        height=row['height'],
                        img_width=img_width,
                        img_height=img_height
                    )
                    
                    # Write to label file
                    f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
        
        print(f"Processed {len(filenames)} images for {split_name} split")

def create_yaml_config(output_dir: str, class_map: Dict[str, int]):
    """Create a YAML configuration file for the dataset.
    
    Args:
        output_dir: Directory to save the YAML file
        class_map: Dictionary mapping class names to class IDs
    """
    # Invert the class map to get class names by ID
    id_to_class = {v: k for k, v in class_map.items()}
    class_names = [id_to_class[i] for i in range(len(class_map))]
    
    # Create YAML content
    yaml_content = {
        'path': str(output_dir),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': len(class_map),
        'names': class_names
    }
    
    # Write to file
    yaml_path = output_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    
    print(f"Created YAML configuration at {yaml_path}")
    return yaml_path

# Example usage
if __name__ == "__main__":
    # Example class mapping
    CLASS_MAP = {
        'player': 0,
        'referee': 1,
        'ball': 2
    }
    
    # Example usage
    converter = CSVToYOLOConverter(
        csv_path='path/to/annotations.csv',
        images_dir='path/to/images',
        output_dir='data/yolo_format',
        class_map=CLASS_MAP
    )
    
    # Convert and split the data
    converter.convert(split_ratio=(0.7, 0.2, 0.1))
    
    # Create YAML configuration
    create_yaml_config(Path('data/yolo_format'), CLASS_MAP)
