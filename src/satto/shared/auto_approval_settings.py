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
            }


DEFAULT_AUTO_APPROVAL_SETTINGS = AutoApprovalSettings()
