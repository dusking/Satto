import os
import asyncio
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, Union, List
from weakref import WeakValueDictionary, ref
from typing_extensions import Protocol
from ..utils.history import (
    save_api_conversation_history,
    load_api_conversation_history,
    save_cline_messages,
    load_cline_messages,
    get_task_history
)
from ..api.api_handler import build_api_handler
from ..shared.api import ApiConfiguration
from .prompts.system import SYSTEM_PROMPT, add_user_instructions
from ..utils.cost import calculate_api_cost
# from .mcp import McpHub
from .assistant_message import parse_assistant_message
from .assistant_message.write_to_file_tool import WriteToFileTool
from .assistant_message.read_file_tool import ReadFileTool
from .assistant_message.list_files_tool import ListFilesTool
from .assistant_message.search_files_tool import SearchFilesTool
from .assistant_message.list_code_definition_names_tool import ListCodeDefinitionNamesTool
from .assistant_message.replace_in_file_tool import ReplaceInFileTool
from .assistant_message.attempt_completion_tool import AttemptCompletionTool
from .assistant_message.execute_command_tool import ExecuteCommandTool
from .assistant_message.ask_followup_question_tool import AskFollowupQuestionTool
from .assistant_message.plan_mode_response_tool import PlanModeResponseTool


class ApiStream(Protocol):
    async def __aiter__(self):
        ...
    async def __anext__(self):
        ...


class PyCline:
    def __init__(self, api_provider: str, api_key: str, model_id: Optional[str] = None, base_url: Optional[str] = None, task_id: Optional[str] = None, load_latest: bool = True):
        """Initialize PyCline instance.

        Args:
            api_provider: The API provider to use (e.g. "anthropic", "openai")
            api_key: API key for authentication
            model_id: Optional model identifier
            base_url: Optional base URL for the API
            task_id: Optional task ID for resuming an existing task. If not provided and load_latest is True, will attempt to load latest task ID.
            load_latest: Whether to load the latest task ID if no task_id is provided. Note that actual task history loading is handled by resume_task().
        """
        self.cwd = os.getcwd()
        self.api_handler = None
        self.mcp_hub = None
        self.browser_settings = None
        self.chat_settings = None
        self.custom_instructions = None
        self.task = ""
        self.abort = False

        # If no task_id provided and load_latest is True, try to load latest task
        if not task_id and load_latest:
            latest_task = get_task_history()[-1] if get_task_history() else None
            if latest_task:
                self.task_id = latest_task["id"]
            else:
                self.task_id = str(int(time.time()))
        else:
            self.task_id = task_id or str(int(time.time()))
        
        # Track API total usage cost
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_writes = 0
        self.total_cache_reads = 0
        
        # Initialize tools
        self.write_to_file_tool = WriteToFileTool(self.cwd)
        self.read_file_tool = ReadFileTool(self.cwd)
        self.list_files_tool = ListFilesTool(self.cwd)
        self.search_files_tool = SearchFilesTool(self.cwd)
        self.list_code_definition_names_tool = ListCodeDefinitionNamesTool(self.cwd)
        self.replace_in_file_tool = ReplaceInFileTool(self.cwd)
        self.attempt_completion_tool = AttemptCompletionTool(self.cwd)
        self.execute_command_tool = ExecuteCommandTool(self.cwd)
        self.ask_followup_question_tool = AskFollowupQuestionTool(self.cwd)
        self.plan_mode_response_tool = PlanModeResponseTool(self.cwd)
        self.attempt_completion_tool.set_pycline(self)
        
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

    async def add_to_api_conversation_history(self, message: Dict) -> None:
        """Add a message to the API conversation history and save it.
        
        Args:
            message: The message to add
        """
        self.api_conversation_history.append(message)
        await self.save_api_conversation_history()

    async def save_api_conversation_history(self) -> None:
        """Save the current API conversation history to disk."""
        try:
            save_api_conversation_history(self.task_id, self.api_conversation_history)
        except Exception as e:
            print(f"Failed to save API conversation history: {e}")

    async def save_cline_messages(self) -> None:
        """Save the current Cline UI messages to disk."""
        try:
            save_cline_messages(self.task_id, self.cline_messages)
        except Exception as e:
            print(f"Failed to save Cline messages: {e}")

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

    async def start_task(self, task: str) -> None:
        """Start a new task.
        
        Args:
            task: The task description
        """
        # Always generate new task_id for new tasks
        self.task_id = str(int(time.time()))
        self.cline_messages = []
        self.api_conversation_history = []
        
        return await self.initiate_task_loop([
            {
                "type": "text",
                "text": f"<task>\n{task}\n</task>"
            }
        ], True)

    async def resume_task(self, task: str) -> None:
        """Resume a task with history.
        
        Args:
            task: The task description
        """
        # First set the task
        self.task = task
        
        # Then try to load history
        if not await self.load_history():
            # If no history found, start a new task instead
            self.task_id = str(int(time.time()))
            self.cline_messages = []
            self.api_conversation_history = []
            
        return await self.initiate_task_loop([
            {
                "type": "text",
                "text": f"<task>\n{task}\n</task>"
            }
        ], True)

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
        
        # Process the response blocks and track usage
        if isinstance(response, dict) and 'text' in response:
            if 'usage' in response:
                input_tokens = response['usage'].get('input_tokens', 0)
                output_tokens = response['usage'].get('output_tokens', 0)
                
                # Update cumulative total costs
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
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
                    elif block.name == "execute_command":
                        result = self.execute_command_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('command', '')}']"
                    elif block.name == "ask_followup_question":
                        result = self.ask_followup_question_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name} for '{block.params.get('question', '')}']"
                            # Return True to end the loop when ask_followup_question is successful
                            return True
                    elif block.name == "plan_mode_response":
                        result = self.plan_mode_response_tool.execute(block.params)
                        if result and result.success:
                            tool_description = f"[{block.name}]"
                    
                    if result:
                        if hasattr(result, 'message'):
                            print(f"{block.name.replace('_', '').upper()} RESULT: \n{result.message}\n")
                            next_user_content.append({
                                "type": "text",
                                "text": f"{tool_description} Result: {result.message}"
                            })
                        
                        if hasattr(result, 'content') and result.content:
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

    async def load_history(self) -> bool:
        """Load task history from disk.
        
        Returns:
            bool: True if history was loaded successfully
        """
        try:
            self.api_conversation_history = load_api_conversation_history(self.task_id)
            self.cline_messages = load_cline_messages(self.task_id)
            return len(self.api_conversation_history) > 0 or len(self.cline_messages) > 0
        except Exception as e:
            print(f"Failed to load history: {e}")
            return False

    async def ask(self, question_type: str, error_message: str) -> Dict[str, str]:
        """Ask the user a question and get their response."""
        # In a real implementation this would show a UI prompt
        # For now we'll simulate always choosing to retry
        return {"response": "yesButtonClicked"}

    async def say(self, message_type: str):
        """Display a message to the user."""
        # In a real implementation this would show a UI message
        pass

    def get_cost(self) -> float:
        """Get the API usage cost in USD.
        
        Returns:
            float: Cost of API usage in USD based on token counts and model pricing.
        """
        model_info = self.api_handler.get_model().info    
        return calculate_api_cost(
            model_info,
            self.total_input_tokens,
            self.total_output_tokens,
            self.total_cache_writes,
            self.total_cache_reads
        )
