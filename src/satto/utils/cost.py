from typing import Optional
from ..shared.api import ModelInfo


def calculate_api_cost(
    model_info: ModelInfo,
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: Optional[int] = None,
    cache_read_input_tokens: Optional[int] = None,
) -> float:
    """Calculate the total API cost based on token usage.

    Args:
        model_info: Information about the model including pricing
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        cache_creation_input_tokens: Optional number of tokens used for cache writes
        cache_read_input_tokens: Optional number of tokens used for cache reads

    Returns:
        float: Total cost in USD
    """
    model_cache_writes_price = model_info.get('cache_writes_price') or 0
    cache_writes_cost = 0
    if cache_creation_input_tokens and model_cache_writes_price:
        cache_writes_cost = (model_cache_writes_price / 1_000_000) * cache_creation_input_tokens

    model_cache_reads_price = model_info.get('cache_reads_price') or 0
    cache_reads_cost = 0
    if cache_read_input_tokens and model_cache_reads_price:
        cache_reads_cost = (model_cache_reads_price / 1_000_000) * cache_read_input_tokens

    base_input_cost = (((model_info.get('input_price') or 0) / 1_000_000)) * input_tokens
    output_cost = (((model_info.get('output_price') or 0) / 1_000_000)) * output_tokens
    total_cost = cache_writes_cost + cache_reads_cost + base_input_cost + output_cost

    return round(total_cost, 3)
