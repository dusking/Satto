import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    success: bool
    message: str
    content: Optional[str] = None

class ReplaceInFileTool:
    def __init__(self, cwd: str):
        self.cwd = cwd

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute the replace_in_file tool.
        
        Args:
            params: Dictionary containing:
                - path: Relative path to the file
                - diff: SEARCH/REPLACE blocks defining the changes
                
        Returns:
            ToolResult with success status, message, and content
        """
        try:
            rel_path = params.get('path')
            diff_content = params.get('diff')
            
            if not rel_path:
                return ToolResult(
                    success=False,
                    message="Missing required parameter: path",
                    content=None
                )
            
            if not diff_content:
                return ToolResult(
                    success=False,
                    message="Missing required parameter: diff",
                    content=None
                )

            abs_path = os.path.join(self.cwd, rel_path)
            
            # Read original file content
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except FileNotFoundError:
                return ToolResult(
                    success=False,
                    message=f"File not found: {rel_path}",
                    content=None
                )
            
            # Apply the diff
            try:
                new_content = self._construct_new_file_content(diff_content, original_content)
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Error applying diff: {str(e)}",
                    content=None
                )
            
            # Write the modified content back to the file
            try:
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                return ToolResult(
                    success=False,
                    message=f"Error writing file: {str(e)}",
                    content=None
                )
            
            return ToolResult(
                success=True,
                message=f"Successfully updated {rel_path}",
                content=f"Updated content:\n{new_content}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                content=None
            )

    def _construct_new_file_content(self, diff_content: str, original_content: str) -> str:
        """Reconstruct file content by applying SEARCH/REPLACE blocks.
        
        Args:
            diff_content: String containing SEARCH/REPLACE blocks
            original_content: Original file content
            
        Returns:
            New file content with replacements applied
        """
        result = ""
        last_processed_index = 0
        
        current_search_content = ""
        current_replace_content = ""
        in_search = False
        in_replace = False
        
        search_match_index = -1
        search_end_index = -1
        
        lines = diff_content.split('\n')
        
        # Handle partial markers at the end
        if lines and any(
            lines[-1].startswith(prefix) for prefix in ('<', '=', '>')
        ) and lines[-1] not in ('<<<<<<< SEARCH', '=======', '>>>>>>> REPLACE'):
            lines.pop()
            
        for line in lines:
            if line == '<<<<<<< SEARCH':
                in_search = True
                current_search_content = ""
                current_replace_content = ""
                continue
                
            if line == '=======':
                in_search = False
                in_replace = True
                
                if not current_search_content:
                    # Empty search block
                    if not original_content:
                        # New file
                        search_match_index = 0
                        search_end_index = 0
                    else:
                        # Complete file replacement
                        search_match_index = 0
                        search_end_index = len(original_content)
                else:
                    # Try exact match first
                    search_match_index = original_content.find(
                        current_search_content, 
                        last_processed_index
                    )
                    
                    if search_match_index == -1:
                        # Try line-trimmed match
                        match = self._line_trimmed_match(
                            original_content,
                            current_search_content,
                            last_processed_index
                        )
                        
                        if match:
                            search_match_index, search_end_index = match
                        else:
                            # Try block anchor match for 3+ lines
                            match = self._block_anchor_match(
                                original_content,
                                current_search_content,
                                last_processed_index
                            )
                            
                            if match:
                                search_match_index, search_end_index = match
                            else:
                                raise ValueError(
                                    f"The SEARCH block:\n{current_search_content.rstrip()}\n"
                                    "...does not match anything in the file."
                                )
                    else:
                        search_end_index = search_match_index + len(current_search_content)
                
                # Output everything up to match location
                result += original_content[last_processed_index:search_match_index]
                continue
                
            if line == '>>>>>>> REPLACE':
                # Advance last_processed_index past matched section
                last_processed_index = search_end_index
                
                # Reset for next block
                in_search = False
                in_replace = False
                current_search_content = ""
                current_replace_content = ""
                search_match_index = -1
                search_end_index = -1
                continue
                
            # Accumulate content
            if in_search:
                current_search_content += line + '\n'
            elif in_replace:
                current_replace_content += line + '\n'
                # Output replacement lines immediately if insertion point known
                if search_match_index != -1:
                    result += line + '\n'
                    
        # Append any remaining original content
        if last_processed_index < len(original_content):
            result += original_content[last_processed_index:]
            
        return result

    def _line_trimmed_match(
        self, 
        original_content: str,
        search_content: str, 
        start_index: int
    ) -> Optional[tuple[int, int]]:
        """Find match by comparing trimmed lines."""
        original_lines = original_content.split('\n')
        search_lines = search_content.split('\n')
        
        # Remove empty trailing line
        if search_lines[-1] == "":
            search_lines.pop()
            
        # Find starting line number
        start_line_num = 0
        current_index = 0
        while current_index < start_index and start_line_num < len(original_lines):
            current_index += len(original_lines[start_line_num]) + 1
            start_line_num += 1
            
        # Try to match at each position
        for i in range(start_line_num, len(original_lines) - len(search_lines) + 1):
            matches = True
            
            for j in range(len(search_lines)):
                if original_lines[i + j].strip() != search_lines[j].strip():
                    matches = False
                    break
                    
            if matches:
                # Calculate character positions
                match_start = 0
                for k in range(i):
                    match_start += len(original_lines[k]) + 1
                    
                match_end = match_start
                for k in range(len(search_lines)):
                    match_end += len(original_lines[i + k]) + 1
                    
                return (match_start, match_end)
                
        return None

    def _block_anchor_match(
        self,
        original_content: str,
        search_content: str,
        start_index: int
    ) -> Optional[tuple[int, int]]:
        """Find match using first/last lines as anchors."""
        original_lines = original_content.split('\n')
        search_lines = search_content.split('\n')
        
        # Only use for 3+ line blocks
        if len(search_lines) < 3:
            return None
            
        # Remove empty trailing line
        if search_lines[-1] == "":
            search_lines.pop()
            
        first_line_search = search_lines[0].strip()
        last_line_search = search_lines[-1].strip()
        search_block_size = len(search_lines)
        
        # Find starting line number
        start_line_num = 0
        current_index = 0
        while current_index < start_index and start_line_num < len(original_lines):
            current_index += len(original_lines[start_line_num]) + 1
            start_line_num += 1
            
        # Look for matching anchors
        for i in range(start_line_num, len(original_lines) - search_block_size + 1):
            if original_lines[i].strip() != first_line_search:
                continue
                
            if original_lines[i + search_block_size - 1].strip() != last_line_search:
                continue
                
            # Calculate character positions
            match_start = 0
            for k in range(i):
                match_start += len(original_lines[k]) + 1
                
            match_end = match_start
            for k in range(search_block_size):
                match_end += len(original_lines[i + k]) + 1
                
            return (match_start, match_end)
            
        return None
