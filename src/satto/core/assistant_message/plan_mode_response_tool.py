from dataclasses import dataclass
from typing import Optional


@dataclass
class PlanModeResponseResult:
    success: bool
    message: Optional[str] = None
    content: Optional[str] = None


class PlanModeResponseTool:
    def __init__(self, cwd: str):
        self.cwd = cwd

    def execute(self, params: dict) -> PlanModeResponseResult:
        """Execute the plan mode response tool.
        
        Args:
            params: Dictionary containing:
                response: The response text to display
                
        Returns:
            PlanModeResponseResult with success status and message
        """
        if 'response' not in params:
            return PlanModeResponseResult(
                success=False,
                message="Missing required 'response' parameter"
            )
            
        response = params['response']
        return PlanModeResponseResult(
            success=True,
            message=response
        )
