from typing import Any, Dict
from openai import AsyncOpenAI
from .api_handler_base import ApiHandlerBase
from ...shared.api import ApiConfiguration, ModelInfo, deepseek_models, deepseek_default_model_id
from ..transform.openai_format import convert_to_openai_messages
from ..transform.r1_format import convert_to_r1_format


class DeepSeekHandler(ApiHandlerBase):
    def __init__(self, options: ApiConfiguration):
        self.options = options
        self.client = AsyncOpenAI(
            base_url="https://api.deepseek.com/v1",
            api_key=self.options.api_key,
        )

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:
        model = self.get_model()
        is_deepseek_reasoner = "deepseek-reasoner" in model["id"]

        if is_deepseek_reasoner:
            openai_messages = convert_to_r1_format([
                {"role": "user", "content": system_prompt},
                *messages
            ])
        else:
            openai_messages = [
                {"role": "system", "content": system_prompt},
                *convert_to_openai_messages(messages),
            ]

        stream = await self.client.chat.completions.create(
            model=model["id"],
            max_completion_tokens=model["info"].max_tokens,
            messages=openai_messages,
            temperature=0 if model["id"] != "deepseek-reasoner" else None,
            stream=True,
            stream_options={"include_usage": True},
        )

        full_text = ""
        full_reasoning = ""
        usage = None

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta:
                if delta.content:
                    full_text += delta.content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    full_reasoning += delta.reasoning_content
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage

        result = {
            "text": full_text,
            "usage": {
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "cache_read_tokens": getattr(usage, "prompt_cache_hit_tokens", 0) if usage else 0,
                "cache_write_tokens": getattr(usage, "prompt_cache_miss_tokens", 0) if usage else 0,
            } if usage else None
        }

        if full_reasoning:
            result["reasoning"] = full_reasoning

        return result

    def get_model(self) -> Dict[str, Any]:
        model_id = self.options.get("model")
        if model_id and model_id in deepseek_models:
            return {
                "id": model_id,
                "info": deepseek_models[model_id],
            }
        return {
            "id": deepseek_default_model_id,
            "info": deepseek_models[deepseek_default_model_id],
        }
