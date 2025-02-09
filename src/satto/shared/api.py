from typing import Dict, Optional, TypedDict, Literal, Union, Any

# Define API Provider Type
ApiProvider = Literal[
    "anthropic",
    "openrouter",
    "bedrock",
    "vertex",
    "openai",
    "ollama",
    "lmstudio",
    "gemini",
    "openai-native",
    "deepseek",
    "mistral",
    "vscode-lm"
]

# Define Model Information
class ModelInfo(TypedDict, total=False):
    max_tokens: int
    context_window: int
    supports_images: bool
    supports_computer_use: bool
    supports_prompt_cache: bool
    input_price: float
    output_price: float
    cache_writes_price: float
    cache_reads_price: float
    description: str

# Define API Handler Options
class ApiHandlerOptions(TypedDict, total=False):
    api_model_id: Optional[str]
    api_key: Optional[str]  # Anthropics
    anthropic_base_url: Optional[str]
    openrouter_api_key: Optional[str]
    openrouter_model_id: Optional[str]
    openrouter_model_info: Optional[ModelInfo]
    aws_access_key: Optional[str]
    aws_secret_key: Optional[str]
    aws_session_token: Optional[str]
    aws_region: Optional[str]
    aws_use_cross_region_inference: Optional[bool]
    vertex_project_id: Optional[str]
    vertex_region: Optional[str]
    openai_base_url: Optional[str]
    openai_api_key: Optional[str]
    openai_model_id: Optional[str]
    ollama_model_id: Optional[str]
    ollama_base_url: Optional[str]
    lmstudio_model_id: Optional[str]
    lmstudio_base_url: Optional[str]
    gemini_api_key: Optional[str]
    openai_native_api_key: Optional[str]
    deepseek_api_key: Optional[str]
    mistral_api_key: Optional[str]
    azure_api_version: Optional[str]
    vscode_lm_model_selector: Optional[Any]

# Define API Configuration
class ApiConfiguration(ApiHandlerOptions, total=False):
    api_provider: Optional[ApiProvider]

# Define Anthropics Model Information
anthropic_models: Dict[str, ModelInfo] = {
    "claude-3-5-sonnet-20241022": {
        "max_tokens": 8192,
        "context_window": 200_000,
        "supports_images": True,
        "supports_computer_use": True,
        "supports_prompt_cache": True,
        "input_price": 3.0,
        "output_price": 15.0,
        "cache_writes_price": 3.75,
        "cache_reads_price": 0.3,
    },
    "claude-3-5-haiku-20241022": {
        "max_tokens": 8192,
        "context_window": 200_000,
        "supports_images": False,
        "supports_prompt_cache": True,
        "input_price": 0.8,
        "output_price": 4.0,
        "cache_writes_price": 1.0,
        "cache_reads_price": 0.08,
    },
    "claude-3-opus-20240229": {
        "max_tokens": 4096,
        "context_window": 200_000,
        "supports_images": True,
        "supports_prompt_cache": True,
        "input_price": 15.0,
        "output_price": 75.0,
        "cache_writes_price": 18.75,
        "cache_reads_price": 1.5,
    },
    "claude-3-haiku-20240307": {
        "max_tokens": 4096,
        "context_window": 200_000,
        "supports_images": True,
        "supports_prompt_cache": True,
        "input_price": 0.25,
        "output_price": 1.25,
        "cache_writes_price": 0.3,
        "cache_reads_price": 0.03,
    },
}

anthropic_default_model_id = "claude-3-5-sonnet-20241022"

# Define AWS Bedrock Models
bedrock_models: Dict[str, ModelInfo] = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "max_tokens": 8192,
        "context_window": 200_000,
        "supports_images": True,
        "supports_computer_use": True,
        "supports_prompt_cache": False,
        "input_price": 3.0,
        "output_price": 15.0,
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "max_tokens": 4096,
        "context_window": 200_000,
        "supports_images": True,
        "supports_prompt_cache": False,
        "input_price": 15.0,
        "output_price": 75.0,
    },
}

bedrock_default_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# Define Gemini Models
gemini_models: Dict[str, ModelInfo] = {
    "gemini-2.0-flash-thinking-exp-01-21": {
        "max_tokens": 65536,
        "context_window": 1_048_576,
        "supports_images": True,
        "supports_prompt_cache": False,
        "input_price": 0,
        "output_price": 0,
    },
    "gemini-1.5-flash-002": {
        "max_tokens": 8192,
        "context_window": 1_048_576,
        "supports_images": True,
        "supports_prompt_cache": False,
        "input_price": 0,
        "output_price": 0,
    },
}

gemini_default_model_id = "gemini-2.0-flash-thinking-exp-1219"

# Define OpenAI Native Models
openai_native_models: Dict[str, ModelInfo] = {
    "o1": {
        "max_tokens": 100_000,
        "context_window": 200_000,
        "supports_images": True,
        "supports_prompt_cache": False,
        "input_price": 15,
        "output_price": 60,
    },
    "o1-mini": {
        "max_tokens": 65_536,
        "context_window": 128_000,
        "supports_images": False,
        "supports_prompt_cache": False,
        "input_price": 3,
        "output_price": 12
    },
    "gpt-4o": {
        "max_tokens": 4_096,
        "context_window": 128_000,
        "supports_images": True,
        "supports_prompt_cache": False,
        "input_price": 5,
        "output_price": 15,
    },
    "o3-mini": {
        "max_tokens": 4_096,
        "context_window": 128_000,
        "supports_images": True,
        "supports_prompt_cache": False,
        "input_price": 0.5,
        "output_price": 1.5
    }
}

openai_native_default_model_id = "gpt-4o"

# Define DeepSeek Models
deepseek_models: Dict[str, ModelInfo] = {
    "deepseek-chat": {
        "max_tokens": 8_000,
        "context_window": 64_000,
        "supports_images": False,
        "supports_prompt_cache": True,
        "input_price": 0,
        "output_price": 0.28,
        "cache_writes_price": 0.14,
        "cache_reads_price": 0.014,
    },
}

deepseek_default_model_id = "deepseek-chat"

# Define Mistral Models
mistral_models: Dict[str, ModelInfo] = {
    "codestral-latest": {
        "max_tokens": 32_768,
        "context_window": 256_000,
        "supports_images": False,
        "supports_prompt_cache": False,
        "input_price": 0.3,
        "output_price": 0.9,
    },
}

mistral_default_model_id = "codestral-latest"

# Define sane defaults for OpenAI Model Info
openai_model_info_sane_defaults: ModelInfo = {
    "max_tokens": -1,
    "context_window": 128_000,
    "supports_images": True,
    "supports_prompt_cache": False,
    "input_price": 0,
    "output_price": 0,
}

# Define Azure OpenAI API Version
azure_openai_default_api_version = "2024-08-01-preview"
