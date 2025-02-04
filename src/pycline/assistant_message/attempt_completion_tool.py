from dataclasses import dataclass
from typing import Dict, Any, Optional
from ...utils.cost import calculate_api_cost

@dataclass
class AttemptCompletionResult:
    success: bool
    message: Optional[str] = None
    content: Optional[str] = None

class AttemptCompletionTool:
    def __init__(self, cwd: str):
        self.cwd = cwd
        self.pycline = None  # Will be set by PyCline instance
    
    def set_pycline(self, pycline):
        """Set reference to PyCline instance for accessing token counts."""
        self.pycline = pycline

    def execute(self, params: Dict[str, Any]) -> AttemptCompletionResult:
        """Execute the attempt_completion tool.
        
        Args:
            params: Dictionary containing:
                - result: The completion result message
                - command: Optional command to execute
                
        Returns:
            AttemptCompletionResult with success status and messages
        """
        if not params.get('result'):
            return AttemptCompletionResult(
                success=False,
                message="Missing required parameter 'result'"
            )

        # Get total cost if we have access to PyCline instance
        cost_message = ""
        if self.pycline:
            total_cost = self.pycline.get_cost()
            cost_message = f"\n\nTotal API usage cost: ${total_cost:.4f}"

        result = params['result'] + cost_message
        command = params.get('command')

        if command:
            return AttemptCompletionResult(
                success=True,
                message=result,
                content=command
            )
        
        return AttemptCompletionResult(
            success=True,
            message=result
        )
