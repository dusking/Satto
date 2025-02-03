from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    success: bool
    message: str
    content: Optional[str] = None

class AttemptCompletionTool:
    def __init__(self, cwd: str):
        self.cwd = cwd

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """Execute the attempt_completion tool.
        
        Args:
            params: Dictionary containing:
                - result: The result of the task
                - command: (optional) A CLI command to demonstrate the result
                
        Returns:
            ToolResult with success status, message, and content
        """
        try:
            result = params.get('result')
            command = params.get('command')
            
            if not result:
                return ToolResult(
                    success=False,
                    message="Missing required parameter: result",
                    content=None
                )

            # For now, we'll just return the result since command execution
            # requires terminal integration which would be handled by PyCline
            return ToolResult(
                success=True,
                message="Task completion attempted",
                content=result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                content=None
            )
