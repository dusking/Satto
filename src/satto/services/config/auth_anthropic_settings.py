from dataclasses import dataclass


@dataclass
class AuthAnthropicSettings:
    """Settings for Anthropic authentication and model configuration."""
    api_key: str
    api_provider: str = "anthropic"
    model_id: str = "claude-3-5-sonnet-20241022"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AuthAnthropicSettings':
        """Create an AuthAnthropicSettings instance from a dictionary."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)