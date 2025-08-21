"""
Configuration for basketball analysis datasets.
"""
from pathlib import Path
from typing import Dict, Any, Optional

class DatasetConfig:
    """Configuration for a dataset source."""
    
    def __init__(
        self,
        name: str,
        source_url: str,
        local_dir: Path,
        classes: Dict[int, str],
        expected_files: list[str],
        download_required: bool = True
    ):
        self.name = name
        self.source_url = source_url
        self.local_dir = Path(local_dir)
        self.classes = classes
        self.expected_files = expected_files
        self.download_required = download_required
        
        # Create local directory if it doesn't exist
        self.local_dir.mkdir(parents=True, exist_ok=True)
    
    def get_class_names(self) -> list[str]:
        """Get list of class names."""
        return list(self.classes.values())
    
    def get_class_ids(self) -> list[int]:
        """Get list of class IDs."""
        return list(self.classes.keys())

# Roboflow Basketball Players Dataset
ROBOFLOW_BASKETBALL = DatasetConfig(
    name="roboflow_basketball",
    source_url="https://universe.roboflow.com/roboflow-universe-projects/basketball-players-fy4c2",
    local_dir=Path("data/roboflow_basketball"),
    classes={
        0: "player",
        1: "referee",
        2: "ball"
    },
    expected_files=["dataset.yaml", "train/images", "val/images", "test/images"],
    download_required=True
)

# TrackID3x3 Dataset (needs to be downloaded manually)
TRACK_ID_3X3 = DatasetConfig(
    name="trackid3x3",
    source_url="https://arxiv.org/abs/2503.18282",
    local_dir=Path("data/trackid3x3"),
    classes={
        0: "player",
        1: "ball",
        2: "hoop"
    },
    expected_files=["indoor", "outdoor", "drone"],
    download_required=False  # Manual download required
)

# Dataset registry
DATASETS = {
    "roboflow": ROBOFLOW_BASKETBALL,
    "trackid3x3": TRACK_ID_3X3
}

def get_dataset_config(name: str) -> Optional[DatasetConfig]:
    """Get dataset configuration by name."""
    return DATASETS.get(name.lower())

def list_available_datasets() -> list[str]:
    """List all available dataset names."""
    return list(DATASETS.keys())
