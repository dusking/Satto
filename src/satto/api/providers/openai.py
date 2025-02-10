from typing import Any, AsyncGenerator, Dict, Optional
from openai import AsyncOpenAI, AsyncAzureOpenAI
from .api_handler_base import ApiHandlerBase
from ...shared.api import ApiConfiguration, ModelInfo, openai_model_info_sane_defaults, azure_openai_default_api_version
from ..transform.openai_format import convert_to_openai_messages


class OpenAiHandler(ApiHandlerBase):
    def __init__(self, options: ApiConfiguration):
        self.options = options
        # Azure API shape slightly differs from the core API shape
        if self.options.get("openai_base_url", "").lower().find("azure.com") != -1:
            self.client = AsyncAzureOpenAI(
                base_url=self.options.get("openai_base_url"),
                api_key=self.options.api_key,
                api_version=self.options.get("azure_api_version") or azure_openai_default_api_version,
            )
        else:
            self.client = AsyncOpenAI(
                base_url=self.options.get("openai_base_url"),
                api_key=self.options.api_key,
            )

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:
        openai_messages = [
            {"role": "system", "content": system_prompt},
            *convert_to_openai_messages(messages),
        ]
        
        stream = await self.client.chat.completions.create(
            model=self.options.get("model_id", ""),
            messages=openai_messages,
            temperature=0,
            stream=True,
            stream_options={"include_usage": True},
        )

        full_text = ""
        usage = None

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_text += delta.content
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage

        return {
            "text": full_text,
            "usage": {
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            } if usage else None
        }

    def get_model(self) -> Dict[str, Any]:
        return {
            "id": self.options.get("model", ""),
            "info": openai_model_info_sane_defaults,
        }
