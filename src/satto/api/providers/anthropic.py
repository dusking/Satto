import asyncio
import time
import sys
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

    async def create_message(self, system_prompt: str, messages: list) -> Dict[str, Any]:
        model = self.get_model()
        model_id = model["id"]

        stream = await asyncio.to_thread(
            self.client.messages.create,
            model=model_id,
            max_tokens=model["info"].get("max_tokens", 8192),
            temperature=0,
            system=system_prompt,
            messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
            stream=True
        )

        full_text = ""
        usage = None
        chunk_count = 0
        start_time = time.time()

        for chunk in stream:
            if hasattr(chunk, 'type'):
                if chunk.type == 'content_block_delta':
                    chunk_count += 1
                    full_text += chunk.delta.text
                    elapsed = time.time() - start_time
                    sys.stdout.write(f"\rReceived {chunk_count} chunks in {elapsed:.2f}s")
                    sys.stdout.flush()
                elif chunk.type == 'message_delta':
                    if hasattr(chunk.usage, 'input_tokens'):
                        usage = {
                            "input_tokens": chunk.usage.input_tokens,
                            "output_tokens": chunk.usage.output_tokens
                        }
                    elapsed = time.time() - start_time
                    sys.stdout.write(f"\rReceived {chunk_count} chunks in {elapsed:.2f}s")
                    sys.stdout.flush()

        # Print newline after progress
        print()

        if not usage:
            # Fallback if we didn't get usage info from the stream
            usage = {
                "input_tokens": 0,
                "output_tokens": 0
            }

        return DotDict({
            "type": "text",
            "text": full_text,
            "usage": usage
        })

    def get_model(self):
        model_id = self.options.get("api_model_id")
        if model_id and model_id in anthropic_models:
            return DotDict({"id": model_id, "info": anthropic_models[model_id]})
        return DotDict({"id": anthropic_default_model_id, "info": anthropic_models[anthropic_default_model_id]})
