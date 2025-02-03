import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from fnmatch import fnmatch


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    content: Optional[str] = None


@dataclass
class SearchMatch:
    """Represents a regex match in a file"""
    file_path: str
    line_number: int
    line: str
    context_before: List[str]
    context_after: List[str]


class SearchFilesTool:
    def __init__(self, working_directory: str):
        """
        Initialize the search_files tool.

        Args:
            working_directory: The base directory for all file operations
        """
        self.working_directory = Path(working_directory)
        self.CONTEXT_LINES = 3  # Number of lines to show before and after match
        self.MAX_MATCHES = 100  # Maximum number of matches to return

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

    def _validate_regex(self, pattern: str) -> re.Pattern:
        """
        Validate and compile the regex pattern.

        Args:
            pattern: Regex pattern string

        Returns:
            Compiled regex pattern

        Raises:
            ValueError: If pattern is invalid
        """
        try:
            return re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {str(e)}")

    def _search_file(self, file_path: Path, regex: re.Pattern) -> List[SearchMatch]:
        """
        Search for regex matches in a file.

        Args:
            file_path: Path to the file to search
            regex: Compiled regex pattern

        Returns:
            List of SearchMatch objects
        """
        matches = []
        try:
            # Read all lines from the file
            with file_path.open('r', encoding='utf-8') as f:
                lines = f.readlines()

            # Search for matches
            for i, line in enumerate(lines):
                if regex.search(line):
                    # Get context lines
                    start = max(0, i - self.CONTEXT_LINES)
                    end = min(len(lines), i + self.CONTEXT_LINES + 1)
                    
                    matches.append(SearchMatch(
                        file_path=str(file_path.relative_to(self.working_directory)),
                        line_number=i + 1,
                        line=line.rstrip('\n'),
                        context_before=[l.rstrip('\n') for l in lines[start:i]],
                        context_after=[l.rstrip('\n') for l in lines[i+1:end]]
                    ))

                    if len(matches) >= self.MAX_MATCHES:
                        break

        except Exception as e:
            print(f"Error searching file {file_path}: {str(e)}")

        return matches

    def _format_matches(self, matches: List[SearchMatch], did_hit_limit: bool) -> str:
        """Format search matches into a readable string."""
        if not matches:
            return "No matches found."

        result = []
        current_file = None

        for match in matches:
            # Add file header if this is a new file
            if current_file != match.file_path:
                current_file = match.file_path
                result.append(f"\nFile: {match.file_path}")

            # Add match with context
            result.append(f"\n  Line {match.line_number}:")
            
            # Add context before
            for line in match.context_before:
                result.append(f"    {line}")
            
            # Add matching line (highlighted)
            result.append(f">>> {match.line}")
            
            # Add context after
            for line in match.context_after:
                result.append(f"    {line}")

        if did_hit_limit:
            result.append(f"\n[Results limited to {self.MAX_MATCHES} matches]")

        return "\n".join(result)

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the search_files tool.

        Args:
            params: Dictionary containing 'path', 'regex', and optional 'file_pattern' parameters

        Returns:
            ToolResult with success status, message, and search results
        """
        # Validate required parameters
        if 'path' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'path'"
            )
        if 'regex' not in params:
            return ToolResult(
                success=False,
                message="Missing required parameter: 'regex'"
            )

        try:
            # Validate and resolve path
            dir_path = self._validate_path(params['path'])

            # Validate and compile regex
            regex = self._validate_regex(params['regex'])

            # Get file pattern
            file_pattern = params.get('file_pattern', '*')

            # Search files
            matches = []
            did_hit_limit = False

            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    if fnmatch(filename, file_pattern):
                        file_path = Path(root) / filename
                        file_matches = self._search_file(file_path, regex)
                        matches.extend(file_matches)

                        if len(matches) >= self.MAX_MATCHES:
                            did_hit_limit = True
                            break

                if did_hit_limit:
                    break

            # Format results
            content = self._format_matches(matches, did_hit_limit)

            # Create result message
            rel_path = dir_path.relative_to(self.working_directory)
            pattern_info = f" (pattern: {file_pattern})" if file_pattern != '*' else ''
            return ToolResult(
                success=True,
                message=f"Successfully searched files in {rel_path}/{pattern_info} for: {params['regex']}",
                content=content
            )

        except ValueError as e:
            return ToolResult(
                success=False,
                message=f"Invalid input: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error searching files: {str(e)}"
            )
