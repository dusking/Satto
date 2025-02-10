from .providers.anthropic import AnthropicHandler
from .providers.openai import OpenAiHandler
from .providers.openai_native import OpenAiNativeHandler
from .providers.together import TogetherHandler
from ..shared.api import ApiConfiguration
from .providers.api_handler_base import ApiHandlerBase


def build_api_handler(api_provider: ApiConfiguration) -> ApiHandlerBase:
    handlers = {
        "anthropic": AnthropicHandler,
        "openai": OpenAiHandler,
        "openai-native": OpenAiNativeHandler,
        "together": TogetherHandler,
    }
    if api_provider.name not in handlers:
        raise ValueError(f"Unsupported API provider: {api_provider.name}")
    handler_class = handlers.get(api_provider.name)    
    return handler_class(options=api_provider)
