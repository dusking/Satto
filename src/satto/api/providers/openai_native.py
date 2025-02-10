import re
import ast
import json
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
            api_key=self.options.api_key,
        )

    def extract_error(self, exception_message: Exception) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", str(exception_message))
        if match:
            error_json_str = match.group(0)
            
            try:
                # Use ast.literal_eval to safely convert the string to a Python dictionary
                error_dict = ast.literal_eval(error_json_str)
                return DotDict(error_dict)
            except (ValueError, SyntaxError) as e:
                print("Failed to parse JSON:", e)

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:
        model_id = self.get_model()["id"]
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": "system", "content": system_prompt},
            *convert_to_openai_messages(messages),
        ]
        
        # o1 models don't support streaming
        if model_id in ["o1", "o1-preview", "o1-mini"]:
            try:
                response = await self.client.chat.completions.create(
                    model=model_id,
                    messages=openai_messages,
                )
            except Exception as ex:
                error = self.extract_error(ex)
                return error
            
            return DotDict({
                "text": response.choices[0].message.content if response.choices else "",
                "usage": DotDict({
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0,
                }) if response.usage else None
            })
        
        # For other models, use streaming
        try:
            stream = await self.client.chat.completions.create(
                model=model_id,
                messages=openai_messages,
                temperature=0.5,
                stream=True,
                stream_options={"include_usage": True},
            )
        except Exception as ex:
            error = self.extract_error(ex)
            print(f"Error: {error.error}")
            return error

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
