import os
import ast
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    content: Optional[str] = None


class ListCodeDefinitionNamesTool:
    def __init__(self, working_directory: str):
        """
        Initialize the list_code_definition_names tool.

        Args:
            working_directory: The base directory for all file operations
        """
        self.working_directory = Path(working_directory)
        self.SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx'}

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

    def _parse_python_file(self, file_path: Path) -> List[str]:
        """Parse Python file for top-level definitions."""
        definitions = []
        try:
            with file_path.open('r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    definitions.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            definitions.append(target.id)

        except Exception as e:
            print(f"Error parsing Python file {file_path}: {str(e)}")

        return definitions

    def _parse_js_ts_file(self, file_path: Path) -> List[str]:
        """Parse JavaScript/TypeScript file for top-level definitions."""
        definitions = []
        try:
            with file_path.open('r', encoding='utf-8') as f:
                content = f.read()

            # Simple regex-based parsing for demonstration
            # In a real implementation, you would use a proper JS/TS parser
            import re
            
            # Match class, function, and const/let/var declarations
            patterns = [
                r'class\s+(\w+)',
                r'function\s+(\w+)',
                r'(const|let|var)\s+(\w+)\s*=',
                r'export\s+(const|let|var)\s+(\w+)\s*=',
                r'export\s+class\s+(\w+)',
                r'export\s+function\s+(\w+)',
                r'export\s+interface\s+(\w+)',
                r'export\s+type\s+(\w+)',
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Get the last group which contains the name
                    name = match.groups()[-1]
                    if name:
                        definitions.append(name)

        except Exception as e:
            print(f"Error parsing JS/TS file {file_path}: {str(e)}")

        return definitions

    def _get_file_definitions(self, file_path: Path) -> List[str]:
        """Get definitions from a file based on its extension."""
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            return self._parse_python_file(file_path)
        elif ext in {'.js', '.ts', '.jsx', '.tsx'}:
            return self._parse_js_ts_file(file_path)
        
        return []

    def _format_definitions(self, file_definitions: Dict[str, List[str]]) -> str:
        """Format the definitions into a readable string."""
        if not file_definitions:
            return "No definitions found."

        result = []
        for file_path, definitions in sorted(file_definitions.items()):
            if definitions:
                result.append(f"\nFile: {file_path}")
                for definition in sorted(definitions):
                    result.append(f"  {definition}")

        return "\n".join(result)

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the list_code_definition_names tool.

        Args:
            params: Dictionary containing 'path' parameter

        Returns:
            ToolResult with success status, message, and definitions list
        """
        # Validate parameters
        if 'path' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'path'"
            )

        try:
            # Validate and resolve path
            dir_path = self._validate_path(params['path'])

            # Find and parse source files
            file_definitions: Dict[str, List[str]] = {}

            # Only process files in the top level of the directory
            for entry in dir_path.iterdir():
                if entry.is_file() and entry.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    rel_path = entry.relative_to(self.working_directory)
                    definitions = self._get_file_definitions(entry)
                    if definitions:
                        file_definitions[str(rel_path)] = definitions

            # Format results
            content = self._format_definitions(file_definitions)

            # Create result message
            rel_path = dir_path.relative_to(self.working_directory)
            return ToolResult(
                success=True,
                message=f"Successfully listed code definitions in: {rel_path}",
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
                message=f"Error listing code definitions: {str(e)}"
            )
