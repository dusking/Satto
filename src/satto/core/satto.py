import os
import asyncio
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, Union, List, cast
from weakref import WeakValueDictionary, ref
from typing_extensions import Protocol
from ..shared.auto_approval_settings import AutoApprovalSettings, DEFAULT_AUTO_APPROVAL_SETTINGS
from .prompts.responses import (
    format_tool_denied,
    format_tool_denied_with_feedback,
    format_tool_error,
    format_no_tools_used,
    format_too_many_mistakes,
    format_missing_tool_parameter_error,
    format_invalid_mcp_tool_argument_error,
    format_tool_result,
    format_files_list
)
from ..utils.history import (
    save_api_conversation_history,
    load_api_conversation_history,
    save_satto_messages,
    load_satto_messages,
    get_latest_task
)
from ..utils.string import fix_model_html_escaping, remove_invalid_chars
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


class Satto:
    def __init__(self, api_provider: str, api_key: str, model_id: Optional[str] = None, base_url: Optional[str] = None, task_id: Optional[str] = None, load_latest: bool = True, auto_approval_settings: Optional[AutoApprovalSettings] = None):
        """Initialize Satto instance.

        Args:
            api_provider: The API provider to use (e.g. "anthropic", "openai")
            api_key: API key for authentication
            model_id: Optional model identifier
            base_url: Optional base URL for the API
            task_id: Optional task ID for resuming an existing task. If not provided and load_latest is True, will attempt to load latest task ID.
            load_latest: Whether to load the latest task ID if no task_id is provided. Note that actual task history loading is handled by resume_task().
        """
        self.cwd = os.getcwd()
        self.auto_approval_settings = auto_approval_settings or DEFAULT_AUTO_APPROVAL_SETTINGS
        self.consecutive_auto_approved_requests_count = 0
        self.api_handler = None
        self.mcp_hub = None
        self.browser_settings = None
        self.chat_settings = None
        self.custom_instructions = None
        self.task = ""
        self.abort = False

        # If no task_id provided and load_latest is True, try to load latest task
        if not task_id and load_latest:
            latest_task = get_latest_task()
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
        self.execute_command_tool = ExecuteCommandTool(self.cwd, self)
        self.ask_followup_question_tool = AskFollowupQuestionTool(self.cwd)
        self.plan_mode_response_tool = PlanModeResponseTool(self.cwd)
        self.attempt_completion_tool.set_satto(self)
        
        self.consecutive_mistake_count = 0
        self.satto_messages = []
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

    async def save_satto_messages(self) -> None:
        """Save the current Satto UI messages to disk."""
        try:
            save_satto_messages(self.task_id, self.satto_messages)
        except Exception as e:
            print(f"Failed to save Satto messages: {e}")

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
        self.satto_messages = []
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
            self.satto_messages = []
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
            did_end_loop = await self.recursively_make_satto_requests(next_user_content,
                                                                      include_file_details,
                                                                      is_new_task)

            if did_end_loop:
                break

            next_user_content = [
                {
                    "type": "text",
                    "text": format_no_tools_used()
                }
            ]
            self.consecutive_mistake_count += 1

    def should_auto_approve_tool(self, tool_name: str) -> bool:
        """Check if a tool should be auto-approved based on settings.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            bool: Whether the tool should be auto-approved
        """
        if self.auto_approval_settings.enabled:
            if tool_name in ["read_file", "list_files", "list_code_definition_names", "search_files"]:
                return self.auto_approval_settings.actions['read_files']
            elif tool_name in ["write_to_file", "replace_in_file"]:
                return self.auto_approval_settings.actions['edit_files']
            elif tool_name == "execute_command":
                return self.auto_approval_settings.actions['execute_commands']
            elif tool_name == "browser_action":
                return self.auto_approval_settings.actions['use_browser']
            elif tool_name in ["access_mcp_resource", "use_mcp_tool"]:
                return self.auto_approval_settings.actions['use_mcp']
        return False

    def show_notification(self, subtitle: str, message: str) -> None:
        """Show a system notification if enabled in auto-approval settings.
        
        Args:
            subtitle: The notification subtitle
            message: The notification message
        """
            
        # if self.auto_approval_settings.enabled and self.auto_approval_settings.enable_notifications:
            # In a real implementation this would show a system notification
            # For now we just print to console
        print(f"{subtitle}: {message}")

    async def recursively_make_satto_requests(self, user_content, include_file_details, is_new_task):     
        if self.abort:
            raise Exception("Satto instance aborted")

        if self.consecutive_mistake_count >= 3:
            self.show_notification(
                "Error",
                "Satto is having trouble. Exiting task run."
            )
            next_user_content = [
                {
                    "type": "text",
                    "text": format_too_many_mistakes("You seem to be having trouble. Please review the previous messages and try again.")
                }
            ]
            return True

        if (self.auto_approval_settings.enabled and 
            self.consecutive_auto_approved_requests_count >= self.auto_approval_settings.max_requests):
            self.show_notification(
                "Max Requests Reached",
                f"Satto has auto-approved {self.auto_approval_settings.max_requests} API requests."
            )
            response = await self.ask(
                "auto_approval_max_req_reached",
                f"Satto has auto-approved {self.auto_approval_settings.max_requests} API requests. Would you like to reset the count and proceed with the task?"
            )
            # If we get past here, it means the user approved and did not start a new task
            self.consecutive_auto_approved_requests_count = 0

        await self.add_to_api_conversation_history({
            "role": "user",
            "content": user_content})

        await self.save_satto_messages()

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
                    
                    # Check for auto-approval before executing any tool
                    auto_approved = False
                    requires_approval = True  # Default to requiring approval
                    
                    if block.name == "execute_command":
                        requires_approval = block.params.get('requires_approval', 'true').lower() == 'true'
                        auto_approved = (not requires_approval and 
                                      self.should_auto_approve_tool(block.name) and
                                      self.consecutive_auto_approved_requests_count < self.auto_approval_settings.max_requests)
                    else:
                        auto_approved = (self.should_auto_approve_tool(block.name) and
                                       self.consecutive_auto_approved_requests_count < self.auto_approval_settings.max_requests)

                    if auto_approved:
                        self.consecutive_auto_approved_requests_count += 1
                    elif requires_approval:
                                                
                        # If auto-approval is enabled but this tool wasn't auto-approved, send notification
                        if block.name == "write_to_file":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to {'edit' if os.path.exists(os.path.join(self.cwd, block.params.get('path', ''))) else 'create'} {os.path.basename(block.params.get('path', ''))}"
                            )
                        elif block.name == "replace_in_file":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to edit {os.path.basename(block.params.get('path', ''))}"
                            )
                        elif block.name == "read_file":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to read {os.path.basename(block.params.get('path', ''))}"
                            )
                        elif block.name == "list_files":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to view directory {os.path.basename(block.params.get('path', ''))}/"
                            )
                        elif block.name == "search_files":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to search files in {os.path.basename(block.params.get('path', ''))}/"
                            )
                        elif block.name == "execute_command":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to execute a command: {block.params.get('command', '')}"
                            )
                        elif block.name == "browser_action" and block.params.get('action') == "launch":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to use a browser and launch {block.params.get('url', '')}"
                            )
                        elif block.name == "use_mcp_tool":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to use {block.params.get('tool_name', '')} on {block.params.get('server_name', '')}"
                            )
                        elif block.name == "access_mcp_resource":
                            self.show_notification(
                                "Approval Required",
                                f"Satto wants to access {block.params.get('uri', '')} on {block.params.get('server_name', '')}"
                            )

                        # Ask for approval                        
                        response = await self.ask("tool_approval", f"Approve {block.name}?")
                        if response.get("response") != "yesClicked":
                            # User denied the tool use
                            next_user_content.append({
                                "type": "text",
                                "text": format_tool_denied()
                            })
                            return False
                                                
                    # Clean up model outputs before passing to tools
                    if block.name == "write_to_file" and 'content' in block.params:
                        block.params['content'] = fix_model_html_escaping(block.params['content'])
                        block.params['content'] = remove_invalid_chars(block.params['content'])
                        result = self.write_to_file_tool.execute(block.params)
                    elif block.name == "replace_in_file" and 'diff' in block.params:
                        block.params['diff'] = fix_model_html_escaping(block.params['diff'])
                        block.params['diff'] = remove_invalid_chars(block.params['diff'])
                        result = self.replace_in_file_tool.execute(block.params)
                    elif block.name == "read_file":
                        result = self.read_file_tool.execute(block.params)
                    elif block.name == "list_files":
                        result = await self.list_files_tool.execute(block.params)
                    elif block.name == "search_files":
                        result = await self.search_files_tool.execute(block.params)
                    elif block.name == "list_code_definition_names":
                        result = self.list_code_definition_names_tool.execute(block.params)
                    elif block.name == "attempt_completion":
                        result = self.attempt_completion_tool.execute(block.params)
                    elif block.name == "execute_command":
                        # If command was auto-approved, set a timeout to notify user if it runs too long
                        if auto_approved:
                            async def check_command_timeout():
                                await asyncio.sleep(30)  # 30 second timeout
                                self.show_notification(
                                    "Command is still running",
                                    "An auto-approved command has been running for 30s, and may need your attention."
                                )
                            asyncio.create_task(check_command_timeout())
                            
                        result = await self.execute_command_tool.execute(block.params)
                    elif block.name == "ask_followup_question":
                        result = self.ask_followup_question_tool.execute(block.params)
                    elif block.name == "plan_mode_response":
                        result = self.plan_mode_response_tool.execute(block.params)
                    
                    if result:
                        if not result.success:
                            next_user_content.append({
                                "type": "text",
                                "text": format_tool_error(result.message)
                            })
                        else:
                            if block.name in ["write_to_file", "read_file", "list_files", "search_files", 
                                           "list_code_definition_names", "replace_in_file"]:
                                tool_description = f"[{block.name} for '{block.params.get('path', '')}']"
                            elif block.name == "search_files":
                                tool_description = f"[{block.name} for '{block.params.get('regex', '')}']"
                            elif block.name == "execute_command":
                                tool_description = f"[{block.name} for '{block.params.get('command', '')}']"
                            elif block.name == "ask_followup_question":
                                tool_description = f"[{block.name} for '{block.params.get('question', '')}']"
                            else:
                                tool_description = f"[{block.name}]"
                            
                            if hasattr(result, 'message'):
                                print(f"{block.name.replace('_', '').upper()} RESULT: \n{result.message}\n")
                                formatted_result = format_tool_result(f"{tool_description} Result: {result.message}")
                                if isinstance(formatted_result, list):
                                    next_user_content.extend(formatted_result)
                                else:
                                    next_user_content.append({
                                        "type": "text",
                                        "text": formatted_result
                                    })
                            
                            if hasattr(result, 'content') and result.content:
                                formatted_content = format_tool_result(result.content)
                                if isinstance(formatted_content, list):
                                    next_user_content.extend(formatted_content)
                                else:
                                    next_user_content.append({
                                        "type": "text",
                                        "text": formatted_content
                                    })
                            
                            if block.name in ["attempt_completion", "ask_followup_question", "execute_command"]:
                                return True
                        
                        if hasattr(result, 'success') and not result.success:
                            return False
                    else:
                        error_msg = format_tool_error(f"Unknown tool: {block.name}")
                        print(f"{error_msg}\n")
                        next_user_content.append({
                            "type": "text",
                            "text": error_msg
                        })
                else:
                    print(f"Unknown block type: {block.type}\n")
            
            # If we had tool uses, make another request with the results
            if has_tool_use:
                return await self.recursively_make_satto_requests(next_user_content, False, False)
            
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
            satto_rules_file_path = os.path.join(self.cwd, '.sattorules')
            satto_rules_file_instructions = None

            if os.path.exists(satto_rules_file_path):
                try:
                    with open(satto_rules_file_path, 'r', encoding='utf-8') as f:
                        rule_file_content = f.read().strip()
                    if rule_file_content:
                        satto_rules_file_instructions = f"# .sattorules\n\nThe following is provided by a root-level .sattorules file where the user has specified instructions for this working directory ({self.cwd})\n\n{rule_file_content}"
                except Exception:
                    print(f"Failed to read .sattorules file at {satto_rules_file_path}")

            if settings_custom_instructions or satto_rules_file_instructions:
                system_prompt += self.add_user_instructions(settings_custom_instructions, satto_rules_file_instructions)

            if previous_api_req_index >= 0:
                previous_request = self.satto_messages[previous_api_req_index] if previous_api_req_index < len(self.satto_messages) else None
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
                            await self.save_satto_messages()
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
            self.satto_messages = load_satto_messages(self.task_id)
            return len(self.api_conversation_history) > 0 or len(self.satto_messages) > 0
        except Exception as e:
            print(f"Failed to load history: {e}")
            return False

    async def ask(self, question_type: str, error_message: str) -> Dict[str, str]:
        """Ask the user a question and get their response.
        
        Args:
            question_type: Type of question being asked
            error_message: Message to display to user
            
        Returns:
            Dict with response key indicating user's choice
        """
        while True:
            response = input(f"{error_message} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return {"response": "yesClicked"}
            elif response in ['n', 'no']:
                return {"response": "noClicked"} 
            print("Please answer with 'y' or 'n'")


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
