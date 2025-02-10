import asyncio
import time
import sys
from anthropic import Anthropic
from typing import AsyncGenerator, Dict, Any, List, Optional
from .api_handler_base import ApiHandlerBase
from ...shared.dicts import DotDict
from ...shared.api import anthropic_models, anthropic_default_model_id


class AnthropicHandler(ApiHandlerBase):
    def __init__(self, options: Dict[str, Any]):
        self.options = options
        self.client = Anthropic(
            api_key=self.options["api_key"],
            base_url=self.options.get("anthropic_base_url")
        )
        self.usage = {
                    "input_tokens": 0,                    
                    "output_tokens": 0,
                    "cache_write_tokens": 0,
                    "cache_read_tokens": 0,
                }
        super().__init__()
        
    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:
        model = self.get_model()
        model_id = model["id"]

        # Create message parameters
        message_params = {
            "model": model_id,
            "max_tokens": model["info"].get("max_tokens", 8192),
            "temperature": 0,
            "system": [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            "messages": [{"role": msg["role"], "content": msg["content"]} for msg in messages],
            "stream": True
        }
     
        stream = await asyncio.to_thread(
            self.client.messages.create,
            **message_params,
            extra_headers={
                "anthropic-beta": "prompt-caching-2024-07-31",
            }
        )

        full_text = ""
      
        self.init_progerss()

        for chunk in stream:            
            if not hasattr(chunk, 'type'):
                continue
                
            self.print_progress()
            if chunk.type == 'message_start':       
                usage = chunk.message.usage         
                self.usage["input_tokens"] += getattr(usage, 'input_tokens', 0)
                self.usage["output_tokens"] += getattr(usage, 'output_tokens', 0)
                self.usage["cache_write_tokens"] += getattr(usage, 'cache_creation_input_tokens', 0)
                self.usage["cache_read_tokens"] += getattr(usage, 'cache_read_input_tokens', 0)            
            elif chunk.type == 'message_delta':                
                self.usage["output_tokens"] += chunk.usage.output_tokens                            
            elif chunk.type == 'message_stop':
                break
            elif chunk.type == 'content_block_start':                
                if chunk.index > 0:
                    full_text += "\n"
                full_text += chunk.content_block.text
            elif chunk.type == 'content_block_delta':
                full_text += chunk.delta.text                
            elif chunk.type == 'content_block_stop':
                break
        self.after_progerss()

        self.usage["output_tokens"] += len(full_text.split())        

        if not self.usage:
            # Fallback if we didn't get usage info from the stream
            self.usage = {
                "input_tokens": 0,
                "output_tokens": 0
            }
        
        response = DotDict({
            "type": "text",
            "text": full_text,
            "usage": DotDict(self.usage) if self.usage else None
        })    
        return response

    def get_model(self):
        model_id = self.options.get("model")
        if model_id and model_id in anthropic_models:
            return DotDict({"id": model_id, "info": anthropic_models[model_id]})
        return DotDict({"id": anthropic_default_model_id, "info": anthropic_models[anthropic_default_model_id]})
