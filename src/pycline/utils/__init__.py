"""Utility functions for PyCline."""

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
    'ensure_history_dir_exists',
    'ensure_task_dir_exists',
    'save_api_conversation_history',
    'load_api_conversation_history', 
    'save_cline_messages',
    'load_cline_messages',
    'get_task_history',
    'get_latest_task'
]
