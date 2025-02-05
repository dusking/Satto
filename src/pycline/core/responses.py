"""Response formatting utilities for PyCline."""
import os
from typing import List, Optional, Union, Dict, Any
import difflib
import base64
from urllib.parse import urlparse

def format_tool_denied() -> str:
    """Format response for when user denies a tool operation."""
    return "The user denied this operation."

def format_tool_denied_with_feedback(feedback: Optional[str] = None) -> str:
    """Format response for when user denies a tool operation with feedback."""
    return f"The user denied this operation and provided the following feedback:\n<feedback>\n{feedback}\n</feedback>"

def format_tool_error(error: Optional[str] = None) -> str:
    """Format response for tool execution errors."""
    return f"The tool execution failed with the following error:\n<error>\n{error}\n</error>"

def format_no_tools_used() -> str:
    """Format response for when no tools were used in the assistant's response."""
    return f"""[ERROR] You did not use a tool in your previous response! Please retry with a tool use.

{_TOOL_USE_INSTRUCTIONS_REMINDER}

# Next Steps

If you have completed the user's task, use the attempt_completion tool. 
If you require additional information from the user, use the ask_followup_question tool. 
Otherwise, if you have not completed the task and do not need additional information, then proceed with the next step of the task. 
(This is an automated message, so do not respond to it conversationally.)"""

def format_too_many_mistakes(feedback: Optional[str] = None) -> str:
    """Format response for when there are too many mistakes."""
    return f"You seem to be having trouble proceeding. The user has provided the following feedback to help guide you:\n<feedback>\n{feedback}\n</feedback>"

def format_missing_tool_parameter_error(param_name: str) -> str:
    """Format response for missing tool parameters."""
    return f"Missing value for required parameter '{param_name}'. Please retry with complete response.\n\n{_TOOL_USE_INSTRUCTIONS_REMINDER}"

def format_invalid_mcp_tool_argument_error(server_name: str, tool_name: str) -> str:
    """Format response for invalid MCP tool arguments."""
    return f"Invalid JSON argument used with {server_name} for {tool_name}. Please retry with a properly formatted JSON argument."

def format_tool_result(text: str, images: Optional[List[str]] = None) -> Union[str, List[Dict[str, Any]]]:
    """Format tool execution results, optionally including images."""
    if images and images:
        text_block = {"type": "text", "text": text}
        image_blocks = format_images_into_blocks(images)
        # Placing images after text leads to better results
        return [text_block, *image_blocks]
    return text

def format_images_into_blocks(images: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Format images into Anthropic-compatible image blocks."""
    if not images:
        return []
    
    blocks = []
    for data_url in images:
        # data:image/png;base64,base64string
        try:
            rest, base64_data = data_url.split(",", 1)
            mime_type = rest.split(":")[1].split(";")[0]
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64_data
                }
            })
        except (ValueError, IndexError):
            continue  # Skip malformed data URLs
    return blocks

def format_files_list(absolute_path: str, files: List[str], did_hit_limit: bool) -> str:
    """Format list of files with proper sorting and path handling."""
    def to_posix_path(path: str) -> str:
        """Convert path to POSIX format."""
        return path.replace(os.sep, '/')
    
    sorted_files = []
    for file in files:
        # Convert absolute path to relative path
        rel_path = os.path.relpath(file, absolute_path)
        rel_path = to_posix_path(rel_path)
        if os.path.isdir(file):
            rel_path += "/"
        sorted_files.append(rel_path)
    
    # Sort so files are listed under their respective directories
    sorted_files.sort(key=lambda x: [p.lower() for p in x.split('/')])
    
    if did_hit_limit:
        return f"{os.linesep.join(sorted_files)}\n\n(File list truncated. Use list_files on specific subdirectories if you need to explore further.)"
    elif not sorted_files or (len(sorted_files) == 1 and not sorted_files[0]):
        return "No files found."
    else:
        return os.linesep.join(sorted_files)

def create_pretty_patch(filename: str = "file", old_str: Optional[str] = None, new_str: Optional[str] = None) -> str:
    """Create a formatted diff patch between two strings."""
    old_str = old_str or ""
    new_str = new_str or ""
    
    # Create unified diff
    diff_lines = list(difflib.unified_diff(
        old_str.splitlines(keepends=True),
        new_str.splitlines(keepends=True),
        fromfile=filename,
        tofile=filename,
        lineterm=''
    ))
    
    # Skip the first 4 lines (header) as in the TypeScript version
    if len(diff_lines) > 4:
        return '\n'.join(diff_lines[4:])
    return '\n'.join(diff_lines)

_TOOL_USE_INSTRUCTIONS_REMINDER = """# Reminder: Instructions for Tool Use

Tool uses are formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. Here's the structure:

<tool_name>
<parameter1_name>value1</parameter1_name>
<parameter2_name>value2</parameter2_name>
...
</tool_name>

For example:

<attempt_completion>
<result>
I have completed the task...
</result>
</attempt_completion>

Always adhere to this format for all tool uses to ensure proper parsing and execution."""
