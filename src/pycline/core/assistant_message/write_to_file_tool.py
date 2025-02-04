import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass
import difflib


@dataclass
class FileChange:
    """Represents changes made to a file"""
    path: str
    content: str
    is_new: bool
    original_content: Optional[str] = None


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    file_change: Optional[FileChange] = None


class WriteToFileTool:
    def __init__(self, working_directory: str):
        """
        Initialize the write_to_file tool.

        Args:
            working_directory: The base directory for all file operations
        """
        self.working_directory = Path(working_directory)

    def _validate_path(self, file_path: str) -> Tuple[Path, bool]:
        """
        Validate and resolve the file path.

        Args:
            file_path: Relative or absolute path to the file

        Returns:
            Tuple of (resolved path, exists flag)

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

        return full_path, full_path.exists()

    def _create_directories(self, file_path: Path) -> None:
        """Create parent directories if they don't exist"""
        file_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_diff(self, original: str, new: str, file_path: str) -> str:
        """Generate a unified diff between original and new content"""
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        )
        return ''.join(diff)

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the write_to_file tool.

        Args:
            params: Dictionary containing 'path' and 'content' parameters

        Returns:
            ToolResult with success status and message
        """
        # Validate parameters
        if 'path' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'path'"
            )
        if 'content' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'content'"
            )

        try:
            # Validate and resolve path
            file_path, exists = self._validate_path(params['path'])

            # Store original content if file exists
            original_content = None
            if exists:
                original_content = file_path.read_text(encoding='utf-8')

            # Create directories if needed
            self._create_directories(file_path)

            # Write content to file
            content = params['content'].rstrip() + '\n'  # Ensure single trailing newline
            file_path.write_text(content, encoding='utf-8')

            # Create result message
            rel_path = file_path.relative_to(self.working_directory)
            action = "modified" if exists else "created"

            # Create FileChange object
            file_change = FileChange(
                path=str(rel_path),
                content=content,
                is_new=not exists,
                original_content=original_content
            )

            # Generate diff if file was modified
            diff_text = ""
            if exists:
                diff = self._get_diff(original_content or '', content, str(rel_path)).strip()
                diff = diff or "[No Changes Found]"
                diff_text = f"\n\nChanges made:\n{diff}"

            return ToolResult(
                success=True,
                message=f"Successfully {action} file: {rel_path}{diff_text}",
                file_change=file_change
            )

        except ValueError as e:
            return ToolResult(
                success=False,
                message=f"Invalid path: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error writing file: {str(e)}"
            )


# Example usage:
if __name__ == "__main__":
    # Create tool instance
    tool = WriteToFileTool("/path/to/working/directory")

    # Example: Create a new file
    result = tool.execute({
        "path": "example.txt",
        "content": "Hello, World!"
    })
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")

    if result.file_change:
        print(f"File: {result.file_change.path}")
        print(f"Is new: {result.file_change.is_new}")
        if result.file_change.original_content:
            print("Original content:", result.file_change.original_content)
        print("New content:", result.file_change.content)
