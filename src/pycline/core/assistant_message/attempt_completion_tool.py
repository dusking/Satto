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
        self.pycline = None

    def set_pycline(self, pycline):
        """Store a reference to the PyCline instance.
        
        Args:
            pycline: The PyCline instance that created this tool
        """
        self.pycline = pycline

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

            message = "Task completion attempted"
            if command and self.pycline:
                # If a command was provided and we have a PyCline instance,
                # include the command in the message for execution
                message = f"Task completion attempted. Command to demonstrate: {command}"
            
            return ToolResult(
                success=True,
                message=message,
                content=result
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                content=None
            )
