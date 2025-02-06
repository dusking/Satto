from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Union
from enum import Enum


# Define the available tool and parameter names
class ToolName(str, Enum):
    EXECUTE_COMMAND = "execute_command"
    READ_FILE = "read_file"
    WRITE_TO_FILE = "write_to_file"
    REPLACE_IN_FILE = "replace_in_file"
    SEARCH_FILES = "search_files"
    LIST_FILES = "list_files"
    LIST_CODE_DEFINITION_NAMES = "list_code_definition_names"
    BROWSER_ACTION = "browser_action"
    USE_MCP_TOOL = "use_mcp_tool"
    ACCESS_MCP_RESOURCE = "access_mcp_resource"
    ASK_FOLLOWUP_QUESTION = "ask_followup_question"
    PLAN_MODE_RESPONSE = "plan_mode_response"
    ATTEMPT_COMPLETION = "attempt_completion"


class ParamName(str, Enum):
    COMMAND = "command"
    REQUIRES_APPROVAL = "requires_approval"
    PATH = "path"
    CONTENT = "content"
    DIFF = "diff"
    REGEX = "regex"
    FILE_PATTERN = "file_pattern"
    RECURSIVE = "recursive"
    ACTION = "action"
    URL = "url"
    COORDINATE = "coordinate"
    TEXT = "text"
    SERVER_NAME = "server_name"
    TOOL_NAME = "tool_name"
    ARGUMENTS = "arguments"
    URI = "uri"
    QUESTION = "question"
    RESPONSE = "response"
    RESULT = "result"


@dataclass
class TextContent:
    type: Literal["text"]
    content: str
    block_type: Optional[str] = None  # For special blocks like "thinking"


@dataclass
class ToolUse:
    type: Literal["tool_use"]
    name: ToolName
    params: Dict[ParamName, str]


AssistantMessageContent = Union[TextContent, ToolUse]


def parse_assistant_message(message: str) -> List[AssistantMessageContent]:
    """
    Parse an assistant message into a list of content blocks (text and tool uses).

    Args:
        message: The complete message from the assistant

    Returns:
        List of TextContent and ToolUse blocks
    """
    blocks: List[AssistantMessageContent] = []
    current_text = ""

    # Helper function to add accumulated text as a block
    def add_text_block():
        nonlocal current_text
        if current_text.strip():
            # Check if this is a thinking block
            text = current_text.strip()
            if "<thinking>" in text and "</thinking>" in text:
                # Extract all thinking blocks from the text
                while "<thinking>" in text and "</thinking>" in text:
                    start = text.find("<thinking>") + len("<thinking>")
                    end = text.find("</thinking>")
                    if start > 0 and end > start:
                        # Get the content between thinking tags
                        thinking_content = text[start:end].strip()
                        blocks.append(TextContent(
                            type="text",
                            content=thinking_content,
                            block_type="thinking"
                        ))
                        # Remove the processed thinking block
                        text = text[end + len("</thinking>"):].strip()
                
                # Add any remaining non-thinking text
                if text:
                    blocks.append(TextContent(
                        type="text",
                        content=text
                    ))
            else:
                blocks.append(TextContent(
                    type="text",
                    content=text
                ))
        current_text = ""

    # Find all tool use blocks
    while message:
        # Look for the next tool opening tag
        tool_start = -1
        tool_name = None

        for name in ToolName:
            name = name.name.lower()
            tag = f"<{name}>"
            pos = message.find(tag)
            if pos != -1 and (tool_start == -1 or pos < tool_start):
                tool_start = pos
                tool_name = name
                break

        if tool_start == -1:
            # No more tools found, add remaining text
            current_text += message
            message = ""
            continue

        # Add text before the tool block
        current_text += message[:tool_start]
        add_text_block()

        # Find the end of the tool block
        tool_end = message.find(f"</{tool_name}>", tool_start)
        if tool_end == -1:
            # Incomplete tool block, treat as text
            current_text += message[tool_start:]
            message = ""
            continue

        tool_content = message[tool_start:tool_end + len(f"</{tool_name}>")]
        message = message[tool_end + len(f"</{tool_name}>"):]

        # Parse the tool block
        tool_use = parse_tool_block(tool_content)
        if tool_use:
            blocks.append(tool_use)

    # Add any remaining text
    add_text_block()

    return blocks


def parse_tool_block(block: str) -> Optional[ToolUse]:
    """
    Parse a tool use block into a ToolUse object.

    Args:
        block: The complete tool block including opening and closing tags

    Returns:
        ToolUse object if valid, None if invalid
    """
    # Find the tool name
    tool_name = None
    for name in ToolName:
        name = name.name.lower()
        if block.startswith(f"<{name}>"):
            tool_name = name
            break

    if not tool_name:
        return None

    # Extract the tool content (everything between the opening and closing tags)
    content_start = block.find(">") + 1
    content_end = block.rfind(f"</{tool_name}>")
    if content_end == -1:
        return None

    content = block[content_start:content_end]

    # Parse parameters
    params: Dict[ParamName, str] = {}
    for param in ParamName:
        param = param.name.lower()
        param_start = content.find(f"<{param}>")
        if param_start != -1:
            param_end = content.find(f"</{param}>", param_start)
            if param_end != -1:
                param_value = content[param_start + len(f"<{param}>"):param_end].strip()
                params[param] = param_value

    return ToolUse(
        type="tool_use",
        name=tool_name,
        params=params
    )


# # Example usage:
# if __name__ == "__main__":
#     # Example assistant message with multiple tools
#     message = """Here's what I found:
#
# <read_file>
# <path>example.txt</path>
# </read_file>
#
# Now I'll make some changes:
#
# <write_to_file>
# <path>example.txt</path>
# <content>Hello World!</content>
# </write_to_file>
#
# The changes have been made."""
#
#     blocks = parse_assistant_message(message)
#
#     # Print the parsed blocks
#     for block in blocks:
#         if block.type == "text":
#             print(f"Text block: {block.content}")
#         else:  # tool_use
#             print(f"Tool use: {block.name}")
#             print("Parameters:")
#             for param, value in block.params.items():
#                 print(f"  {param}: {value}")
#         print()
