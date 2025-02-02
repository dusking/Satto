from typing import Protocol, Dict, Any, Union
from .providers.anthropic import AnthropicHandler
# from .providers.openrouter import OpenRouterHandler
# from .providers.bedrock import AwsBedrockHandler
# from .providers.vertex import VertexHandler
# from .providers.openai import OpenAiHandler
# from .providers.ollama import OllamaHandler
# from .providers.lmstudio import LmStudioHandler
# from .providers.gemini import GeminiHandler
# from .providers.openai_native import OpenAiNativeHandler
# from .providers.deepseek import DeepSeekHandler
# from .providers.mistral import MistralHandler
# from .providers.vscode_lm import VsCodeLmHandler
from ..shared.api import ApiConfiguration, ModelInfo


class ApiHandler(Protocol):
    def create_message(self, system_prompt: str, messages: list) -> Any:
        pass

    def get_model(self) -> Dict[str, Union[str, ModelInfo]]:
        pass


class SingleCompletionHandler(Protocol):
    async def complete_prompt(self, prompt: str) -> str:
        pass


def build_api_handler(configuration: ApiConfiguration) -> ApiHandler:
    api_provider = configuration["api_provider"]
    # handlers = {
    #     "anthropic": AnthropicHandler,
    #     "openrouter": OpenRouterHandler,
    #     "bedrock": AwsBedrockHandler,
    #     "vertex": VertexHandler,
    #     "openai": OpenAiHandler,
    #     "ollama": OllamaHandler,
    #     "lmstudio": LmStudioHandler,
    #     "gemini": GeminiHandler,
    #     "openai-native": OpenAiNativeHandler,
    #     "deepseek": DeepSeekHandler,
    #     "mistral": MistralHandler,
    #     "vscode-lm": VsCodeLmHandler,
    # }
    handlers = {
        "anthropic": AnthropicHandler,        
    }

    handler_class = handlers.get(api_provider, AnthropicHandler)
    return handler_class(options=configuration)
