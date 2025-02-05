"""Utility functions for PyCline."""

from .string import fix_model_html_escaping, remove_invalid_chars
from .history import (
    ensure_history_dir_exists,
    ensure_task_dir_exists,
    save_api_conversation_history,
    load_api_conversation_history,
    save_cline_messages,
    load_cline_messages,
    get_task_history,
    get_latest_task
)

__all__ = [
    'fix_model_html_escaping',
    'remove_invalid_chars',
    'ensure_history_dir_exists',
    'ensure_task_dir_exists',
    'save_api_conversation_history',
    'load_api_conversation_history', 
    'save_cline_messages',
    'load_cline_messages',
    'get_task_history',
    'get_latest_task'
]
