from typing import Protocol, Dict, Any, Union

from ...shared.dicts import DotDict
from ...shared.api import ModelInfo


class ApiHandlerBase(Protocol):
    async def create_message(self, system_prompt: str, messages: list) -> Any:
        pass

    def get_model(self) -> DotDict[str, Union[str, ModelInfo]]:
        pass


class SingleCompletionHandler(Protocol):
    async def complete_prompt(self, prompt: str) -> str:
        pass
