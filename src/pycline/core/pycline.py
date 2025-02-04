import os
import asyncio
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, Union, List
from weakref import WeakValueDictionary, ref
from typing_extensions import Protocol
from ..api.api_handler import build_api_handler
from ..shared.api import ApiConfiguration
from .prompts.system import SYSTEM_PROMPT, add_user_instructions
# from .mcp import McpHub
from .assistant_message import parse_assistant_message
from .assistant_message.write_to_file_tool import WriteToFileTool
from .assistant_message.read_file_tool import ReadFileTool
from .assistant_message.list_files_tool import ListFilesTool
from .assistant_message.search_files_tool import SearchFilesTool
from .assistant_message.list_code_definition_names_tool import ListCodeDefinitionNamesTool
from .assistant_message.replace_in_file_tool import ReplaceInFileTool
from .assistant_message.attempt_completion_tool import AttemptCompletionTool


class ApiStream(Protocol):
    async def __aiter__(self):
        ...
    async def __anext__(self):
        ...

class PyCline:
    def __init__(self, api_provider: str, api_key: str, model_id: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize PyCline instance.

        Args:
            api_provider: The API provider to use (e.g. "anthropic", "openai")
            api_key: API key for authentication
            model_id: Optional model identifier
            base_url: Optional base URL for the API
        """
        self.cwd = os.getcwd()
        self.api_handler = None
        self.mcp_hub = None
        self.browser_settings = None
        self.chat_settings = None
        self.custom_instructions = None
        self.task = ""
        self.abort = False
        
        # Initialize tools
        self.write_to_file_tool = WriteToFileTool(self.cwd)
        self.read_file_tool = ReadFileTool(self.cwd)
        self.list_files_tool = ListFilesTool(self.cwd)
        self.search_files_tool = SearchFilesTool(self.cwd)
        self.list_code_definition_names_tool = ListCodeDefinitionNamesTool(self.cwd)
        self.replace_in_file_tool = ReplaceInFileTool(self.cwd)
        self.attempt_completion_tool = AttemptCompletionTool(self.cwd)
        
        self.consecutive_mistake_count = 0
        self.cline_messages = []
        self.api_conversation_history = []
        self.conversation_history_deleted_range = None
        self.is_waiting_for_first_chunk = False
        self.did_automatically_retry_failed_api_request = False
        config: ApiConfiguration = {
            "api_provider": api_provider,
            "api_key": api_key,
            "api_model_id": model_id,
            "anthropic_base_url": base_url
        }
        self.api_handler = build_api_handler(config)

    async def add_to_api_conversation_history(self, message):
        self.api_conversation_history.append(message)
        # await this.saveApiConversationHistory()

    async def save_api_conversation_history(self, message):
        """

        Args:
            message:

        Save content to local file like:
        ~/Library/ApplicationSupport/Code/User/globalStorage/saoudrizwan.claude-dev/tasks

        """
        pass

    async def get_response(self, prompt: str) -> str:
        """Get a response from the API for the given prompt.

        Args:
            prompt: The user's input prompt

        Returns:
            The concatenated response from the API
        """
        response = await self.attempt_api_request(-1)
        if isinstance(response, dict) and 'text' in response:
            return response.text
        return ""

    async def start_task(self, task):
        self.cline_messages = []
        self.api_conversation_history = []
        is_new_task = True
        return await self.initiate_task_loop([
            {
                "type": "text",
                "text": f"<task>\n{task}\n</task>"
            }
        ], is_new_task)

    async def initiate_task_loop(self, user_content, is_new_task):
        next_user_content = user_content
        include_file_details = True
        while not self.abort:
            did_end_loop = await self.recursively_make_cline_requests(next_user_content,
                                                                      include_file_details,
                                                                      is_new_task)

            if did_end_loop:
                break

            next_user_content = [
                {
                    "type": "text",
                    "text": "[ERROR] You did not use a tool in your previous response! Please retry with a tool use."
                }
            ]
            self.consecutive_mistake_count += 1

    async def recursively_make_cline_requests(self, user_content, include_file_details, is_new_task):     
        if self.abort:
            raise Exception("Cline instance aborted")

        if self.consecutive_mistake_count >= 3:
            pass

        # if self.auto_approval_settings.enabled and \
        #         self.consecutive_autoApproved_requests_count > self.autoApprovalSettings.max_requests:
        #     pass

        await self.add_to_api_conversation_history({
            "role": "user",
            "content": user_content})

        await self.save_cline_messages()

        previous_api_req_index = -1
        response = await self.attempt_api_request(previous_api_req_index)
        
        # Process the response blocks
        if isinstance(response, dict) and 'text' in response:
            blocks = parse_assistant_message(response.text)
            has_tool_use = any(block.type == "tool_use" for block in blocks)
            next_user_content = []
            
            # Print all text blocks and handle tool uses
            for block in blocks:
                if block.type == "text":
                    if hasattr(block, 'block_type') and block.block_type == "thinking":
                        print(f"THINKING: \n{block.content}\n")
                    else:
                        print(f"TEXT: \n{block.content}\n")
                    # Only add non-thinking blocks to the next user content
                    # if not (hasattr(block, 'block_type') and block.block_type == "thinking"):
                    next_user_content.append({
                        "type": "text",
                        "text": block.content
                    })
                elif block.type == "tool_use":
                    tool_description = f"[{block.name}]"
                    result = None
                    
                    if block.name == "write_to_file":
                        result = self.write_to_file_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('path', '')}']"
                    elif block.name == "read_file":
                        result = self.read_file_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('path', '')}']"
                    elif block.name == "list_files":
                        result = self.list_files_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('path', '')}']"
                    elif block.name == "search_files":
                        result = self.search_files_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('regex', '')}']"
                    elif block.name == "list_code_definition_names":
                        result = self.list_code_definition_names_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('path', '')}']"
                    elif block.name == "replace_in_file":
                        result = self.replace_in_file_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('path', '')}']"
                    elif block.name == "attempt_completion":
                        result = self.attempt_completion_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name}]"
                            # Return True to end the loop when attempt_completion is successful
                            return True
                    
                    if result:
                        if hasattr(result, 'message'):
                            print(f"{block.name.replace('_', '').upper()} RESULT: \n{result.message}\n")
                            next_user_content.append({
                                "type": "text",
                                "text": f"{tool_description} Result: {result.message}"
                            })
                        
                        if hasattr(result, 'content') and result.content:
                            # print(f"{block.name.upper()}_CONTENT:\n{result.content}")
                            next_user_content.append({
                                "type": "text",
                                "text": result.content
                            })
                        
                        if hasattr(result, 'success') and not result.success:
                            return False
                    else:
                        print(f"Unknown tool: {block.name}\n")
                        next_user_content.append({
                            "type": "text",
                            "text": f"Unknown tool: {block.name}"
                        })
                else:
                    print(f"Unknown block type: {block.type}\n")
            
            # If we had tool uses, make another request with the results
            if has_tool_use:
                return await self.recursively_make_cline_requests(next_user_content, False, False)
            
            return has_tool_use
        
        return False

    async def attempt_api_request(self, previous_api_req_index: int) -> Dict[str, Any]:
        """Attempts to make an API request and handles the response.

        This asynchronous function:
        1. Waits for MCP servers to connect.
        2. Generates a system prompt with custom instructions.
        3. Manages conversation history truncation based on token usage and context window limits.
        4. Handles API request retries and error scenarios.

        Args:
            previous_api_req_index (int): Index of the previous API request in the conversation history
                                          used to check token usage for context window management.

        Yields:
            str: Individual chunks of the API response stream.

        Raises:
            RuntimeError: If the MCP hub is not available.
            RuntimeError: If the API request fails after retry attempts.

        Notes:
        - Automatically truncates conversation history when approaching context window limits.
        - Supports different context window sizes for various models (e.g. deepseek, Claude).
        - Includes special handling for OpenRouter with one automatic retry.
        - Allows user-initiated retries if the first chunk fails.
        """
        system_prompt = await SYSTEM_PROMPT(
            self.cwd,
            self.api_handler.get_model().info.get('supports_computer_use', False),
            self.mcp_hub,
            self.browser_settings
        )

        if False:
            settings_custom_instructions = self.custom_instructions.strip() if self.custom_instructions else None
            cline_rules_file_path = os.path.join(self.cwd, '.clinerules')
            cline_rules_file_instructions = None

            if os.path.exists(cline_rules_file_path):
                try:
                    with open(cline_rules_file_path, 'r', encoding='utf-8') as f:
                        rule_file_content = f.read().strip()
                    if rule_file_content:
                        cline_rules_file_instructions = f"# .clinerules\n\nThe following is provided by a root-level .clinerules file where the user has specified instructions for this working directory ({self.cwd})\n\n{rule_file_content}"
                except Exception:
                    print(f"Failed to read .clinerules file at {cline_rules_file_path}")

            if settings_custom_instructions or cline_rules_file_instructions:
                system_prompt += self.add_user_instructions(settings_custom_instructions, cline_rules_file_instructions)

            if previous_api_req_index >= 0:
                previous_request = self.cline_messages[previous_api_req_index] if previous_api_req_index < len(self.cline_messages) else None
                if previous_request and previous_request.get('text'):
                    try:
                        info = json.loads(previous_request['text'])
                        total_tokens = (info.get('tokensIn', 0) + info.get('tokensOut', 0) +
                                    info.get('cacheWrites', 0) + info.get('cacheReads', 0))

                        context_window = self.api_handler.get_model().info.get('context_window', 128_000)

                        max_allowed_size = {
                            64_000: context_window - 27_000,  # deepseek models
                            128_000: context_window - 30_000,  # most models
                            200_000: context_window - 40_000,  # claude models
                        }.get(context_window, max(context_window - 40_000, int(context_window * 0.8)))

                        if total_tokens >= max_allowed_size:
                            keep = "quarter" if total_tokens / 2 > max_allowed_size else "half"
                            self.conversation_history_deleted_range = self.get_next_truncation_range(
                                self.api_conversation_history,
                                self.conversation_history_deleted_range,
                                keep
                            )
                            await self.save_cline_messages()
                    except Exception as e:
                        print(f"Error processing previous request: {e}")

        truncated_conversation_history = self.get_truncated_messages(
            self.api_conversation_history,
            self.conversation_history_deleted_range
        )

        response = await self.api_handler.create_message(system_prompt, truncated_conversation_history)


        return response

    def get_next_truncation_range(self, messages: List[Dict], current_range: Optional[Dict], keep: str) -> Dict:
        """Calculate the next range of messages to truncate."""
        start = 0
        end = len(messages)

        if current_range:
            start = current_range.get('end', 0)

        if keep == "half":
            end = start + (len(messages) - start) // 2
        elif keep == "quarter":
            end = start + (len(messages) - start) // 4

        return {'start': start, 'end': end}

    def get_truncated_messages(self, messages: List[Dict], truncation_range: Optional[Dict]) -> List[Dict]:
        """Get the truncated conversation history."""
        if not truncation_range:
            return messages

        start = truncation_range.get('start', 0)
        end = truncation_range.get('end', len(messages))
        return messages[end:]

    async def save_cline_messages(self):
        """Save the current state of cline messages."""
        # This would typically persist the messages to storage
        # For now we'll just pass as it's not critical for core functionality
        pass

    async def ask(self, question_type: str, error_message: str) -> Dict[str, str]:
        """Ask the user a question and get their response."""
        # In a real implementation this would show a UI prompt
        # For now we'll simulate always choosing to retry
        return {"response": "yesButtonClicked"}

    async def say(self, message_type: str):
        """Display a message to the user."""
        # In a real implementation this would show a UI message
        pass
