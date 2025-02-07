from dataclasses import dataclass


@dataclass
class AutoApprovalSettings:
    """Settings for auto-approval of different actions."""
    enabled: bool = False
    actions: dict = None
    max_requests: int = 20
    enable_notifications: bool = False
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = {
                'read_files': False,  # Read files and directories
                'edit_files': False,  # Edit files
                'execute_commands': False,  # Execute safe commands
                'use_browser': False,  # Use browser
                'use_mcp': False,  # Use MCP servers
                'attempt_completion': False,  # Auto-approve task completion
            }

    @classmethod
    def from_dict(cls, data: dict) -> 'AutoApprovalSettings':
        """Create an AutoApprovalSettings instance from a dictionary."""
        # Filter out any keys that aren't part of the dataclass
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)
    
DEFAULT_AUTO_APPROVAL_SETTINGS = AutoApprovalSettings()
