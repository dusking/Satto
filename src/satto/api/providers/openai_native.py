import re
import ast
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
        super().__init__()

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
        model_id = self.options.model

        # Convert messages to OpenAI format
        openai_messages = [
            {"role": "system", "content": system_prompt},
            *convert_to_openai_messages(messages),
        ]
        
        message_payload = self.get_filtered_args(self.client.chat.completions.create, **self.options)        
        message_payload["messages"] = openai_messages

        # o1 models don't support streaming
        if model_id in ["o1", "o1-preview", "o1-mini"] and message_payload.stream:
            raise Exception(f"Streaming is not supported for this model: {model_id}.")
        
        # Handle non-streaming models
        if not message_payload.stream:
            try:
                response = await self.client.chat.completions.create(**message_payload)
            except Exception as ex:
                error = self.extract_error(ex)
                print(f"Error: {error.error}")
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
            stream = await self.client.chat.completions.create(**message_payload)
        except Exception as ex:
            error = self.extract_error(ex)
            print(f"Error: {error.error}")
            return error
        
        self.init_progerss()
        full_text = ""
        usage = None

        async for chunk in stream:
            self.print_progress()
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_text += delta.content
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage
        self.after_progerss()

        return DotDict({
            "text": full_text,
            "usage": DotDict({
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            }) if usage else None
        })

    def get_model(self) -> Dict[str, Any]:
        model_id = self.options.get("model")
        if model_id and model_id in openai_native_models:
            return DotDict({
                "id": model_id,
                "info": openai_native_models[model_id]
            })
        return DotDict({
            "id": openai_native_default_model_id,
            "info": openai_native_models[openai_native_default_model_id]
        })
