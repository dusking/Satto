from .providers.anthropic import AnthropicHandler
from .providers.openai import OpenAiHandler
from .providers.openai_native import OpenAiNativeHandler
from ..shared.api import ApiConfiguration
from .providers.api_handler_base import ApiHandlerBase


def build_api_handler(configuration: ApiConfiguration) -> ApiHandlerBase:
    api_provider = configuration["api_provider"]
    handlers = {
        "anthropic": AnthropicHandler,
        "openai": OpenAiHandler,
        "openai-native": OpenAiNativeHandler,
    }

    handler_class = handlers.get(api_provider, AnthropicHandler)
    return handler_class(options=configuration)
