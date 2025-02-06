"""Tool for performing regex-based file searches using ripgrep."""
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional

from ...services.ripgrep import regex_search_files

@dataclass
class SearchFilesResult:
    """Result of search_files tool execution."""
    success: bool
    message: str
    content: Optional[str] = None

class SearchFilesTool:
    """Tool for performing regex-based file searches using ripgrep."""
    
    def __init__(self, cwd: str):
        """Initialize the tool.
        
        Args:
            cwd: Current working directory
        """
        self.cwd = cwd
        
    async def execute(self, params: Dict[str, Any]) -> SearchFilesResult:
        """Execute the search_files tool.
        
        Args:
            params: Tool parameters including:
                - path: Directory path to search in
                - regex: Regular expression pattern to search for
                - file_pattern: (optional) Glob pattern to filter files
                
        Returns:
            SearchFilesResult containing:
                - success: Whether the operation succeeded
                - message: Status or error message
                - content: Search results as formatted string
        """
        try:
            path = params.get('path')
            if not path:
                return SearchFilesResult(
                    success=False,
                    message="Missing required parameter: path"
                )

            regex = params.get('regex')
            if not regex:
                return SearchFilesResult(
                    success=False,
                    message="Missing required parameter: regex"
                )

            # Convert relative paths to absolute using cwd
            if not os.path.isabs(path):
                path = os.path.join(self.cwd, path)
                
            # Verify the directory exists
            if not os.path.exists(path):
                return SearchFilesResult(
                    success=False,
                    message=f"Directory does not exist: {path}"
                )

            file_pattern = params.get('file_pattern')
            
            content = await regex_search_files(
                cwd=self.cwd,
                directory_path=path,
                regex=regex,
                file_pattern=file_pattern
            )
            
            return SearchFilesResult(
                success=True,
                message="Search completed successfully",
                content=content
            )
            
        except Exception as e:
            return SearchFilesResult(
                success=False,
                message=f"Error performing file search: {str(e)}"
            )
