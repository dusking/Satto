"""Settings for list_files functionality."""
from dataclasses import dataclass
from typing import List

@dataclass
class ListFilesSettings:
    """Settings for list_files functionality."""
    dirs_to_ignore: List[str] = None

    def __post_init__(self):
        """Set default values if none provided."""
        if self.dirs_to_ignore is None:
            self.dirs_to_ignore = [
                "node_modules",
                "__pycache__",
                "env",
                "venv",
                "target/dependency",
                "build/dependencies",
                "dist",
                "out",
                "bundle",
                "vendor",
                "tmp",
                "temp",
                "deps",
                "pkg",
                "Pods",
                ".*",  # Hidden directories
            ]
            
    @classmethod
    def from_dict(cls, data: dict) -> 'ListFilesSettings':
        """Create a ListFilesSettings instance from a dictionary."""
        # Filter out any keys that aren't part of the dataclass
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)
