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

    async def get_response(self, prompt: str) -> str:
        """Get a response from the API for the given prompt.
        
        Args:
            prompt: The user's input prompt
            
        Returns:
            The concatenated response from the API
        """
        messages = [{"role": "user", "content": prompt}]
        response_chunks = []
        
        async for chunk in self.attempt_api_request(-1):
            if chunk["type"] == "text" and isinstance(chunk["text"], str):
                response_chunks.append(chunk["text"])
            elif chunk["type"] == "text" and isinstance(chunk["text"], list):
                response_chunks.extend(str(item) for item in chunk["text"])
        
        return "".join(response_chunks)

    async def attempt_api_request(self, previous_api_req_index: int) -> AsyncGenerator[Dict[str, Any], None]:
        """Attempt to make an API request with context window management and error handling.
        
        Args:
            previous_api_req_index: Index of the previous API request in cline_messages
            
        Returns:
            An async generator yielding response chunks from the API
            
        Raises:
            Exception: If MCP hub is not available or API request fails
            
            
        ToDo: MSC Hub and servers
        - MCP servers are Small programs that act as intermediaries between LLMs (like Claude) and external tools/data sources
        - They expose specific functionalities (called "tools") that LLMs can use
        - Examples include servers that:
          * Monitor GitHub repositories
          * Fetch weather data
          * Automate browser tasks
          * Query databases
          * Manage project tasks
        """
        # Wait for MCP servers to be connected before generating system prompt
        # start_time = time.time()
        # try:
        #     provider = self.provider_ref.get(1)
        #     while provider and getattr(provider.mcp_hub, 'is_connecting', False):
        #         await asyncio.sleep(0.1)
        #         if (time.time() - start_time) > 10:
        #             print("MCP servers failed to connect in time")
        #             break
        # except Exception:
        #     print("MCP servers failed to connect in time")
        # 
        # provider = self.provider_ref.get(1)
        # mcp_hub = getattr(provider, 'mcp_hub', None) if provider else None
        # if not mcp_hub:
        #     raise Exception("MCP hub not available")

        system_prompt = await SYSTEM_PROMPT(
            self.cwd,
            self.api_handler.get_model().info.get('supports_computer_use', False),
            self.mcp_hub,
            self.browser_settings,
        )

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
            # altering the system prompt mid-task will break the prompt cache, but in the grand scheme this will not change often so it's better to not pollute user messages with it the way we have to with <potentially relevant details>
            system_prompt += self.add_user_instructions(settings_custom_instructions, cline_rules_file_instructions)

        # Handle context window management
        # If the previous API request's total token usage is close to the context window, truncate the conversation history to free up space for the new request
        if previous_api_req_index >= 0:
            previous_request = self.cline_messages[previous_api_req_index] if previous_api_req_index < len(self.cline_messages) else None
            if previous_request and previous_request.get('text'):
                try:
                    info = json.loads(previous_request['text'])
                    total_tokens = (info.get('tokensIn', 0) + info.get('tokensOut', 0) + 
                                info.get('cacheWrites', 0) + info.get('cacheReads', 0))
                    
                    context_window = self.api_handler.get_model().info.get('context_window', 128_000)
                    
                    # Handle deepseek models
                    # if isinstance(self.api_handler, OpenAiHandler) and 'deepseek' in self.api_handler.get_model().id.lower():
                    #     context_window = 64_000

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

        # conversation_history_deleted_range is updated only when we're close to hitting the context window, so we don't continuously break the prompt cache
        truncated_conversation_history = self.get_truncated_messages(
            self.api_conversation_history,
            self.conversation_history_deleted_range
        )

        # DUSKING
        stream = self.api_handler.create_message(system_prompt, truncated_conversation_history)
        iterator = stream.__aiter__()

        try:
            self.is_waiting_for_first_chunk = True
            first_chunk = await iterator.__anext__()
            yield first_chunk
            self.is_waiting_for_first_chunk = False
        except Exception as error:
            is_open_router = self.api_handler.__class__.__name__ == 'OpenRouterHandler'
            if is_open_router and not self.did_automatically_retry_failed_api_request:
                print("first chunk failed, waiting 1 second before retrying")
                await asyncio.sleep(1)
                self.did_automatically_retry_failed_api_request = True
            else:
                # request failed after retrying automatically once, ask user if they want to retry again
                # note that this api_req_failed ask is unique in that we only present this option if the api hasn't streamed any content yet (ie it fails on the first chunk due), as it would allow them to hit a retry button. However if the api failed mid-stream, it could be in any arbitrary state where some tools may have executed, so that error is handled differently and requires cancelling the task entirely.
                response = await self.ask(
                    "api_req_failed",
                    str(error)
                )
                if response.get('response') != "yesButtonClicked":
                    # this will never happen since if noButtonClicked, we will clear current task, aborting this instance
                    raise Exception("API request failed")
                await self.say("api_req_retried")

            # delegate generator output from the recursive call
            async for chunk in self.attempt_api_request(previous_api_req_index):
                yield chunk
            return

        # no error, so we can continue to yield all remaining chunks
		# (needs to be placed outside of try/catch since it we want caller to handle errors not with api_req_failed as that is reserved for first chunk failures only)
		# this delegates to another generator or iterable object. In this case, it's saying "yield all remaining values from this iterator". This effectively passes along all subsequent chunks from the original stream.
        async for chunk in iterator:
            yield chunk

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
        # For now, we'll just pass as it's not critical for core functionality
        pass

    async def ask(self, question_type: str, error_message: str) -> Dict[str, str]:
        """Ask the user a question and get their response."""
        # In a real implementation, this would show a UI prompt
        # For now, we'll simulate always choosing to retry
        return {"response": "yesButtonClicked"}

    async def say(self, message_type: str):
        """Display a message to the user."""
        # In a real implementation, this would show a UI message
        pass
