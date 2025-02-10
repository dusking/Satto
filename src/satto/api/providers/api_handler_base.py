import sys
import time
import json
import inspect
from typing import Protocol, Dict, Any, Union

from ...shared.dicts import DotDict
from ...shared.api import ModelInfo


class ApiHandlerBase(Protocol):
    def __init__(self):
        self.start_time = None
        self.chunk_count = None
        super().__init__()

    async def create_message(self, system_prompt: str, messages: list) -> Any:
        pass

    def get_model(self) -> DotDict[str, Union[str, ModelInfo]]:
        pass

    def get_filtered_args(self, func, **kwargs):
        """Calls func with only the arguments it accepts."""
        # Get the function's signature
        sig = inspect.signature(func)
        
        # Filter out arguments that the function does not accept
        filtered_args = {k: v for k, v in kwargs.items() if k in sig.parameters}
        
        # Call the function with the filtered arguments
        return DotDict(filtered_args)
    
    def init_progerss(self):
        self.start_time = time.time()
        self.chunk_count = 0

    def after_progerss(self):
        # Print newline after progress
        print()   

    def print_progress(self):
        self.chunk_count += 1        
        elapsed = time.time() - self.start_time
        sys.stdout.write(f"\rReceived {self.chunk_count} chunks in {elapsed:.2f}s")
        sys.stdout.flush()


class SingleCompletionHandler(Protocol):
    async def complete_prompt(self, prompt: str) -> str:
        pass
