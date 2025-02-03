import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    content: Optional[str] = None


class ReadFileTool:
    def __init__(self, working_directory: str):
        """
        Initialize the read_file tool.

        Args:
            working_directory: The base directory for all file operations
        """
        self.working_directory = Path(working_directory)

    def _validate_path(self, file_path: str) -> Path:
        """
        Validate and resolve the file path.

        Args:
            file_path: Relative or absolute path to the file

        Returns:
            Resolved path

        Raises:
            ValueError: If path is invalid or outside working directory
        """
        # Resolve the full path
        full_path = (self.working_directory / file_path).resolve()

        # Check if path is within working directory
        try:
            full_path.relative_to(self.working_directory)
        except ValueError:
            raise ValueError(f"Path '{file_path}' is outside working directory")

        # Check if file exists
        if not full_path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        # Check if path is a file
        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        return full_path

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the read_file tool.

        Args:
            params: Dictionary containing 'path' parameter

        Returns:
            ToolResult with success status, message, and file content
        """
        # Validate parameters
        if 'path' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'path'"
            )

        try:
            # Validate and resolve path
            file_path = self._validate_path(params['path'])

            # Read file content
            content = file_path.read_text(encoding='utf-8')

            # Create result message
            rel_path = file_path.relative_to(self.working_directory)
            return ToolResult(
                success=True,
                message=f"Successfully read file: {rel_path}",
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
                message=f"Error reading file: {str(e)}"
            )
