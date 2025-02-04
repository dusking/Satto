import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union


def ensure_history_dir_exists() -> str:
    """Ensure the history directory exists and return its path.
    
    Returns:
        str: Path to the history directory
    """
    history_dir = os.path.expanduser("~/.config/pycline/history")
    os.makedirs(history_dir, exist_ok=True)
    return history_dir

def ensure_task_dir_exists(task_id: str) -> str:
    """Ensure the task directory exists and return its path.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        str: Path to the task directory
    """
    task_dir = os.path.join(ensure_history_dir_exists(), task_id)
    os.makedirs(task_dir, exist_ok=True)
    return task_dir

def save_api_conversation_history(task_id: str, history: List[Dict]) -> None:
    """Save the API conversation history to disk.
    
    Args:
        task_id: The unique identifier for the task
        history: List of conversation messages
    """
    task_dir = ensure_task_dir_exists(task_id)
    history_file = os.path.join(task_dir, "api_conversation_history.json")
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def load_api_conversation_history(task_id: str) -> List[Dict]:
    """Load the API conversation history from disk.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        List[Dict]: List of conversation messages
    """
    task_dir = ensure_task_dir_exists(task_id)
    history_file = os.path.join(task_dir, "api_conversation_history.json")
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_cline_messages(task_id: str, messages: List[Dict]) -> None:
    """Save the Cline UI messages to disk.
    
    Args:
        task_id: The unique identifier for the task
        messages: List of UI messages
    """
    task_dir = ensure_task_dir_exists(task_id)
    messages_file = os.path.join(task_dir, "ui_messages.json")
    with open(messages_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

def load_cline_messages(task_id: str) -> List[Dict]:
    """Load the Cline UI messages from disk.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        List[Dict]: List of UI messages
    """
    task_dir = ensure_task_dir_exists(task_id)
    messages_file = os.path.join(task_dir, "ui_messages.json")
    if os.path.exists(messages_file):
        with open(messages_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_task_history() -> List[Dict]:
    """Get a list of all tasks and their metadata.
    
    Returns:
        List[Dict]: List of task metadata
    """
    history_dir = ensure_history_dir_exists()
    tasks = []
    
    for task_id in os.listdir(history_dir):
        task_dir = os.path.join(history_dir, task_id)
        if not os.path.isdir(task_dir):
            continue
            
        try:
            messages = load_cline_messages(task_id)
            if not messages:
                continue
                
            # Get task metadata from first message
            task_message = messages[0]
            
            # Calculate task size
            task_size = 0
            for root, _, files in os.walk(task_dir):
                for file in files:
                    task_size += os.path.getsize(os.path.join(root, file))
            
            tasks.append({
                "id": task_id,
                "ts": task_message.get("ts", 0),
                "task": task_message.get("text", ""),
                "size": task_size
            })
        except Exception as e:
            print(f"Error loading task {task_id}: {e}")
            continue
            
    return sorted(tasks, key=lambda x: x["ts"], reverse=True)
