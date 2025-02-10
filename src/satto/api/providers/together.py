from typing import Any, Dict

from together import Together


from .api_handler_base import ApiHandlerBase
from ...shared.api import ApiConfiguration, ModelInfo, openai_model_info_sane_defaults
from ..transform.openai_format import convert_to_openai_messages
from ...shared.dicts import DotDict


class TogetherHandler(ApiHandlerBase):
    def __init__(self, options: ApiConfiguration):
        self.options = options
        self.client = Together(api_key=self.options["api_key"])

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:

        message_payload = self.get_filtered_args(self.client.chat.completions.create, **self.options)        
        message_payload["messages"] = messages

        try:            
            response = self.client.chat.completions.create(**message_payload)
        except Exception as ex:
            print(f"Error: {ex}")
            raise

        self.init_progerss()
        full_text = ""
        full_reasoning = ""
        usage = None
                
        for chunk in response:            
            self.print_progress()
            delta = chunk.choices[0].delta.content
            full_text += delta
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

        return result

    def get_model(self) -> Dict[str, Any]:
        model_id = self.options.get("model")
        return DotDict({
            "id": model_id or "",
            "info": openai_model_info_sane_defaults,
        })
