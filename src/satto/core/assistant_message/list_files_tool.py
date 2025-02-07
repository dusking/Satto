"""Tool for listing files in a directory."""
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

from ...services.glob.list_files import list_files
from ...services.config import Config

@dataclass
class ListFilesResult:
    """Result of list_files tool execution."""
    success: bool
    message: str
    content: Optional[str] = None

class ListFilesTool:
    """Tool for listing files in a directory."""
    
    def __init__(self, cwd: str):
        """Initialize the tool.
        
        Args:
            cwd: Current working directory
        """
        self.cwd = cwd
        self.list_files_config = Config().task_list_files
        
    async def execute(self, params: Dict[str, Any]) -> ListFilesResult:
        """Execute the list_files tool.
        
        Args:
            params: Tool parameters including:
                - path: Directory path to list files from
                - recursive: (optional) Whether to list files recursively
                
        Returns:
            ListFilesResult containing:
                - success: Whether the operation succeeded
                - message: Status or error message
                - content: List of files as newline-separated string
        """
        try:
            path = params.get('path')
            if not path:
                return ListFilesResult(
                    success=False,
                    message="Missing required parameter: path"
                )

            # Convert relative paths to absolute using cwd
            if not os.path.isabs(path):
                path = os.path.join(self.cwd, path)
                
            # Verify the directory exists
            if not os.path.exists(path):
                return ListFilesResult(
                    success=False,
                    message=f"Directory does not exist: {path}"
                )
                
            recursive = params.get('recursive', False)
            limit = 200  # Same limit as TypeScript version
            
            files, hit_limit = await list_files(path, recursive, limit, self.list_files_config)
            
            # Convert absolute paths to relative for display
            relative_files = []
            for file in files:
                try:
                    rel_path = os.path.relpath(file, path)
                    # Keep forward slashes for consistency
                    rel_path = rel_path.replace(os.sep, '/')
                    if file.endswith('/'):  # Preserve directory markers
                        rel_path += '/'
                    relative_files.append(rel_path)
                except ValueError:  # For paths on different drives
                    relative_files.append(file)
                    
            content = '\n'.join(relative_files)
            message = "Files listed successfully"
            if hit_limit:
                message += f"\nFile list truncated at {limit} entries"
                
            return ListFilesResult(
                success=True,
                message=message,
                content=content
            )
            
        except Exception as e:
            return ListFilesResult(
                success=False,
                message=f"Error listing files: {str(e)}"
            )
