from typing import Any, Dict, Optional
from openai import AsyncOpenAI
from .api_handler_base import ApiHandlerBase
from ..transform.openai_format import convert_to_openai_messages
from ...shared.api import openai_native_models, openai_native_default_model_id
from ...shared.dicts import DotDict


class OpenAiNativeHandler(ApiHandlerBase):
    def __init__(self, options: Dict[str, Any]):
        self.options = options
        self.client = AsyncOpenAI(
            api_key=self.options.get("openai_native_api_key"),
        )

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:
        model_id = self.get_model()["id"]
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": "system", "content": system_prompt},
            *convert_to_openai_messages(messages),
        ]
        
        # o1 models don't support streaming
        if model_id in ["o1", "o1-preview", "o1-mini"]:
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=openai_messages,
            )
            
            return DotDict({
                "text": response.choices[0].message.content if response.choices else "",
                "usage": DotDict({
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0,
                }) if response.usage else None
            })
        
        # For other models, use streaming
        stream = await self.client.chat.completions.create(
            model=model_id,
            messages=openai_messages,
            temperature=0.5,
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

        return DotDict({
            "text": full_text,
            "usage": DotDict({
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            }) if usage else None
        })

    def get_model(self) -> Dict[str, Any]:
        model_id = self.options.get("api_model_id")
        if model_id and model_id in openai_native_models:
            return DotDict({
                "id": model_id,
                "info": openai_native_models[model_id]
            })
        return DotDict({
            "id": openai_native_default_model_id,
            "info": openai_native_models[openai_native_default_model_id]
        })
