from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    message: str
    content: Optional[str] = None


class AskFollowupQuestionTool:
    def __init__(self, working_directory: str):
        """
        Initialize the ask_followup_question tool.

        Args:
            working_directory: The base directory for all operations
        """
        self.working_directory = Path(working_directory)

    def _validate_params(self, params: Dict[str, str]) -> None:
        """
        Validate the question parameter.

        Args:
            params: Dictionary containing 'question' parameter

        Raises:
            ValueError: If parameters are invalid
        """
        if 'question' not in params:
            raise ValueError("Missing required parameter: 'question'")
        
        if not isinstance(params['question'], str) or not params['question'].strip():
            raise ValueError("Question must be a non-empty string")

    def execute(self, params: Dict[str, str]) -> ToolResult:
        """
        Execute the ask_followup_question tool.

        Args:
            params: Dictionary containing:
                - question: The question to ask the user

        Returns:
            ToolResult with success status and message
        """
        try:
            # Validate parameters
            self._validate_params(params)

            question = params['question']

            return ToolResult(
                success=True,
                message=f"Question for user: {question}",
                content=None
            )

        except ValueError as e:
            return ToolResult(
                success=False,
                message=f"Invalid parameters: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error asking question: {str(e)}"
            )
