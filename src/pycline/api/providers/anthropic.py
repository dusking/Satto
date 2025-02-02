import asyncio
from anthropic import Anthropic
from typing import AsyncGenerator, Dict, Any, List
from ...shared.dicts import DotDict
from ...shared.api import anthropic_models, anthropic_default_model_id


class AnthropicHandler:
    def __init__(self, options: Dict[str, Any]):
        self.options = options
        self.client = Anthropic(
            api_key=self.options["api_key"],
            base_url=self.options.get("anthropic_base_url")
        )
    
    async def create_message(self, system_prompt: str, messages: list) -> AsyncGenerator[Dict[str, Any], None]:
        model = self.get_model()
        model_id = model["id"]

        message = await asyncio.to_thread(
            self.client.messages.create,
            model=model_id,
            max_tokens=model["info"].get("max_tokens", 8192),
            temperature=0,
            system=system_prompt,
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
        )
        for content in message.content:
            if content.type == "text":
                yield DotDict({"type": "text", "text": content.text})
    
    def get_model(self):
        model_id = self.options.get("api_model_id")
        if model_id and model_id in anthropic_models:
            return DotDict({"id": model_id, "info": anthropic_models[model_id]})
        return DotDict({"id": anthropic_default_model_id, "info": anthropic_models[anthropic_default_model_id]})
