import re
from typing import Any, Dict

from together import Together
from openai import AsyncOpenAI


from .api_handler_base import ApiHandlerBase
from ...shared.api import ApiConfiguration, ModelInfo, openai_model_info_sane_defaults
from ..transform.openai_format import convert_to_openai_messages
from ...shared.dicts import DotDict


class TogetherOpennAIHandler(ApiHandlerBase):
    def __init__(self, options: ApiConfiguration):
        self.options = options
        self.client = AsyncOpenAI(
            api_key=self.options.api_key,
            base_url=self.options.base_url,
        )
        super().__init__()

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:

        message_payload = self.get_filtered_args(self.client.chat.completions.create, **self.options)  

        openai_messages = [
            {"role": "system", "content": system_prompt},
            *convert_to_openai_messages(messages),
        ]      
        message_payload["messages"] = openai_messages

        try:            
            response = await self.client.chat.completions.create(**message_payload)
        except Exception as ex:
            print(f"Error: {ex}")
            raise

        self.init_progerss()
        full_text = ""
        full_reasoning = ""
        usage = None
                
        async for chunk in response:            
            self.print_progress()
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                full_reasoning += delta.reasoning_content
            if hasattr(delta, "content") and delta.content:
                full_text += delta.content
            if hasattr(chunk, "usage") and chunk.usage:
                usage = {
                    "input_tokens": chunk.usage.prompt_tokens,
                    "output_tokens": chunk.usage.completion_tokens,
                    "cache_read_tokens": 0,
                    "cache_write_tokens": 0,
                }
        self.after_progerss()

        result = DotDict({
            "text": full_text,
            "usage": usage
        })

        if full_reasoning:
            result["reasoning"] = full_reasoning
            print("AAAAA ", result["reasoning"])
        
        # result["text"] = self.remove_think_tags(result["text"])
        return result

    def remove_think_tags(self, text: str) -> str:
        """Removes content between <think> and </think> tags, including the tags themselves."""
        return re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)

    def get_model(self) -> Dict[str, Any]:
        model_id = self.options.get("model")
        return DotDict({
            "id": model_id or "",
            "info": openai_model_info_sane_defaults,
        })
