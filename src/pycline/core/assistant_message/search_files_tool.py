"""
This module implements the search_files tool for regex-based file searching using ripgrep.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from ...services.ripgrep import regex_search_files
from .tool import Tool


@dataclass
class SearchFilesParams:
    """Parameters for the search_files tool."""
    path: str
    regex: str
    file_pattern: Optional[str] = None


class SearchFilesTool(Tool[SearchFilesParams]):
    """Tool for performing regex-based file searches using ripgrep."""

    name = "search_files"
    description = "Request to perform a regex search across files in a specified directory, providing context-rich results."
    param_class = SearchFilesParams

    async def execute(self, params: SearchFilesParams, cwd: str) -> str:
        """Execute the search_files tool with the given parameters."""
        try:
            return await regex_search_files(
                cwd=cwd,
                directory_path=params.path,
                regex=params.regex,
                file_pattern=params.file_pattern
            )
        except Exception as e:
            return f"Error performing file search: {str(e)}"
