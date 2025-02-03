from typing import Dict, Optional, Union
from dataclasses import dataclass


@dataclass
class TextContent:
    content: str
    partial: bool
    type: str = "text"


TOOL_USE_NAMES = [
    "execute_command",
    "read_file",
    "write_to_file",
    "replace_in_file",
    "search_files",
    "list_files",
    "list_code_definition_names",
    "browser_action",
    "use_mcp_tool",
    "access_mcp_resource",
    "ask_followup_question",
    "plan_mode_response",
    "attempt_completion",
]

TOOL_PARAM_NAMES = [
    "command",
    "requires_approval",
    "path",
    "content",
    "diff",
    "regex",
    "file_pattern",
    "recursive",
    "action",
    "url",
    "coordinate",
    "text",
    "server_name",
    "tool_name",
    "arguments",
    "uri",
    "question",
    "response",
    "result",
]


@dataclass
class ToolUse:
    name: str
    params: Dict[str, Optional[str]]
    partial: bool
    type: str = "tool_use"


@dataclass
class ExecuteCommandToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "execute_command"


@dataclass
class ReadFileToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "read_file"


@dataclass
class WriteToFileToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "write_to_file"


@dataclass
class ReplaceInFileToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "replace_in_file"


@dataclass
class SearchFilesToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "search_files"


@dataclass
class ListFilesToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "list_files"


@dataclass
class ListCodeDefinitionNamesToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "list_code_definition_names"


@dataclass
class BrowserActionToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "browser_action"


@dataclass
class UseMcpToolToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "use_mcp_tool"


@dataclass
class AccessMcpResourceToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "access_mcp_resource"

@dataclass
class AskFollowupQuestionToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "ask_followup_question"


@dataclass
class AttemptCompletionToolUse(ToolUse):
    params: Dict[str, Optional[str]]
    name: str = "attempt_completion"


AssistantMessageContent = Union[TextContent, ToolUse]
