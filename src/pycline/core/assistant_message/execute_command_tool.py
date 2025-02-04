import subprocess
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    content: Optional[str] = None


class ExecuteCommandTool:
    def __init__(self, working_directory: str):
        """
        Initialize the execute_command tool.

        Args:
            working_directory: The base directory for command execution
        """
        self.working_directory = Path(working_directory)

    def _validate_params(self, params: Dict[str, str]) -> None:
        """
        Validate the command parameters.

        Args:
            params: Dictionary containing 'command' and 'requires_approval' parameters

        Raises:
            ValueError: If parameters are invalid
        """
        if 'command' not in params:
            raise ValueError("Missing required parameter: 'command'")
        
        if 'requires_approval' not in params:
            raise ValueError("Missing required parameter: 'requires_approval'")
        
        if not isinstance(params['command'], str) or not params['command'].strip():
            raise ValueError("Command must be a non-empty string")
        
        requires_approval = str(params['requires_approval']).lower()
        if requires_approval not in ['true', 'false']:
            raise ValueError("requires_approval must be 'true' or 'false'")

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the command.

        Args:
            params: Dictionary containing:
                - command: The command to execute
                - requires_approval: Whether the command requires explicit approval

        Returns:
            ToolResult with success status, message, and command output
        """
        try:
            # Validate parameters
            self._validate_params(params)

            command = params['command']
            requires_approval = params['requires_approval'].lower() == 'true'

            try:
                # Execute the command and capture output
                result = subprocess.run(
                    command,
                    shell=True,  # Use shell to support command chaining and shell features
                    cwd=self.working_directory,
                    capture_output=True,
                    text=True,
                    check=True  # Raise CalledProcessError if command fails
                )

                return ToolResult(
                    success=True,
                    message=f"Command executed successfully: {command}",
                    content=result.stdout if result.stdout else None
                )

            except subprocess.CalledProcessError as e:
                # Command failed
                error_message = e.stderr if e.stderr else str(e)
                return ToolResult(
                    success=False,
                    message=f"Command failed with exit code {e.returncode}: {error_message}",
                    content=e.stdout if e.stdout else None
                )

        except ValueError as e:
            return ToolResult(
                success=False,
                message=f"Invalid parameters: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error executing command: {str(e)}"
            )
