import os
import json
import logging
from typing import Optional
from pathlib import Path
from dataclasses import asdict

from .auto_approval_settings import AutoApprovalSettings
from .auth_anthropic_settings import AuthAnthropicSettings
from .list_files_settings import ListFilesSettings


logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "~/.config/satto/config.json"


class Config:
    """Represents the configuration for the Satto CLI."""

    def __init__(self, path: Optional[Path] = None):
        """Initialize the Config object.

        Args:
            path (Path): The path to the configuration file.

        Note:
            If the configuration file exists, the class is initialized with its content.
            If not, the class creates the necessary directory structure for the configuration file.
        """
        self._path: Path = (Path(path or DEFAULT_CONFIG_PATH)).expanduser()
        self.max_consecutive_mistake_count: int = 3
        self.auto_approval: AutoApprovalSettings = AutoApprovalSettings()
        self.auth_anthropic: Optional[AuthAnthropicSettings] = None
        self.task_list_files: ListFilesSettings = ListFilesSettings()

        if self._path.exists():
            self.load_config()

    def load_config(self):
        """Load configuration from file and update instance attributes."""
        data = json.loads(self._path.read_text())
        
        # Handle auto_approval settings separately
        auto_approval_data = data.pop('auto_approval', {})
        if auto_approval_data:
            self.auto_approval = AutoApprovalSettings.from_dict(auto_approval_data)
        
        auth_anthropic_data = data.pop('auth_anthropic', None)
        if auth_anthropic_data:
            self.auth_anthropic = AuthAnthropicSettings.from_dict(auth_anthropic_data)
            
        task_list_files_data = data.pop('task_list_files', {})
        if task_list_files_data:
            self.list_files = ListFilesSettings.from_dict(task_list_files_data)
            
        # Update remaining attributes
        for key, value in data.items():
            if not key.startswith('_'):
                setattr(self, key, value)
                
    def verify_config_dir(self):
        """Verify the existence of the directory specified by self._path.

        If the directory does not exist, attempts to create it.

        Returns:
            bool: True if the directory exists or is successfully created, False otherwise.
        """
        if self._path.exists():
            return True
        path = self._path.parent
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError as e:
            if e.errno == 30:
                logger.error(f"Error: {e}. Check if the file system is read-only or permissions are insufficient.")
            else:
                logger.error(f"Error: {e}")
            return False

    def save(self):
        """Save the configuration to the specified file."""
        if not self.verify_config_dir():
            logger.error("Failed to save config.")
            return False

        # Create a dictionary of the config data
        data = {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_')}
        
        # Convert dataclass instances to dict
        data['auto_approval'] = asdict(self.auto_approval)
        if self.auth_anthropic:
            data['auth_anthropic'] = asdict(self.auth_anthropic)
        data['list_files'] = asdict(self.list_files)

        # Save to file
        self._path.write_text(json.dumps(data, indent=4))
        return True
