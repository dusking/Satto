import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    content: Optional[str] = None


class ListFilesTool:
    def __init__(self, working_directory: str):
        """
        Initialize the list_files tool.

        Args:
            working_directory: The base directory for all file operations
        """
        self.working_directory = Path(working_directory)
        self.MAX_FILES = 200  # Maximum number of files to list

    def _validate_path(self, dir_path: str) -> Path:
        """
        Validate and resolve the directory path.

        Args:
            dir_path: Relative or absolute path to the directory

        Returns:
            Resolved path

        Raises:
            ValueError: If path is invalid or outside working directory
        """
        # Resolve the full path
        full_path = (self.working_directory / dir_path).resolve()

        # Check if path is within working directory
        try:
            full_path.relative_to(self.working_directory)
        except ValueError:
            raise ValueError(f"Path '{dir_path}' is outside working directory")

        # Check if directory exists
        if not full_path.exists():
            raise ValueError(f"Directory does not exist: {dir_path}")

        # Check if path is a directory
        if not full_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        return full_path

    def _list_files(self, directory: Path, recursive: bool) -> Tuple[List[str], bool]:
        """
        List files in the directory.

        Args:
            directory: Path to the directory
            recursive: Whether to list files recursively

        Returns:
            Tuple of (list of file paths, whether limit was hit)
        """
        files = []
        did_hit_limit = False

        try:
            if recursive:
                for root, _, filenames in os.walk(directory):
                    root_path = Path(root)
                    for filename in filenames:
                        if len(files) >= self.MAX_FILES:
                            did_hit_limit = True
                            break
                        file_path = root_path / filename
                        files.append(str(file_path.relative_to(directory)))
                    if did_hit_limit:
                        break
            else:
                for entry in directory.iterdir():
                    if len(files) >= self.MAX_FILES:
                        did_hit_limit = True
                        break
                    files.append(entry.name)

        except Exception as e:
            raise RuntimeError(f"Error listing files: {str(e)}")

        return files, did_hit_limit

    def _format_file_list(self, directory: Path, files: List[str], did_hit_limit: bool) -> str:
        """Format the file list into a readable string."""
        rel_path = directory.relative_to(self.working_directory)
        header = f"Contents of {rel_path}/:\n"
        
        if not files:
            return header + "(empty directory)"

        file_list = "\n".join(f"  {f}" for f in sorted(files))
        footer = f"\n[Results limited to {self.MAX_FILES} files]" if did_hit_limit else ""
        
        return f"{header}{file_list}{footer}"

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the list_files tool.

        Args:
            params: Dictionary containing 'path' and optional 'recursive' parameters

        Returns:
            ToolResult with success status, message, and file listing
        """
        # Validate parameters
        if 'path' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'path'"
            )

        recursive = params.get('recursive', '').lower() == 'true'

        try:
            # Validate and resolve path
            dir_path = self._validate_path(params['path'])

            # List files
            files, did_hit_limit = self._list_files(dir_path, recursive)

            # Format result
            content = self._format_file_list(dir_path, files, did_hit_limit)

            # Create result message
            rel_path = dir_path.relative_to(self.working_directory)
            mode = "recursively " if recursive else ""
            return ToolResult(
                success=True,
                message=f"Successfully {mode}listed files in: {rel_path}",
                content=content
            )

        except ValueError as e:
            return ToolResult(
                success=False,
                message=f"Invalid path: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error listing files: {str(e)}"
            )
