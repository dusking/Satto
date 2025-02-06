"""
Base class for all assistant message tools.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')

class Tool(Generic[T], ABC):
    """Abstract base class for all tools.
    
    Generic type T represents the parameters type for the tool.
    """
    
    name: str
    description: str
    param_class: type
    
    @abstractmethod
    async def execute(self, params: T, cwd: str) -> str:
        """Execute the tool with the given parameters.
        
        Args:
            params: Tool-specific parameters
            cwd: Current working directory
            
        Returns:
            Result of the tool execution as a string
        """
        pass
