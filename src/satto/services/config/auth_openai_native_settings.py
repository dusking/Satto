from dataclasses import dataclass


@dataclass
class AuthOpenAINativeSettings:
    """Settings for OpenAI authentication and model configuration."""
    api_key: str
    api_provider: str = "openai-native"
    model_id: str = "gpt-4o"
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AuthOpenAINativeSettings':
        """Create an AuthOpenAINativeSettings instance from a dictionary."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)