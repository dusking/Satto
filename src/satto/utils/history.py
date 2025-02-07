import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union


def ensure_history_dir_exists() -> str:
    """Ensure the history directory exists and return its path.
    
    Returns:
        str: Path to the history directory
    """
    history_dir = os.path.expanduser("~/.config/satto/history")
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

def save_satto_messages(task_id: str, messages: List[Dict]) -> None:
    """Save the Satto UI messages to disk.
    
    Args:
        task_id: The unique identifier for the task
        messages: List of UI messages
    """
    task_dir = ensure_task_dir_exists(task_id)
    messages_file = os.path.join(task_dir, "ui_messages.json")
    with open(messages_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

def load_satto_messages(task_id: str) -> List[Dict]:
    """Load the Satto UI messages from disk.
    
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
        List[Dict]: List of task metadata sorted by timestamp in descending order
    """
    history_dir = ensure_history_dir_exists()
    tasks = []
    
    for task_id in os.listdir(history_dir):
        task_dir = os.path.join(history_dir, task_id)
        if not os.path.isdir(task_dir):
            continue
            
        try:
            # Try to load API conversation history
            history = load_api_conversation_history(task_id)
            if not history:
                continue
                
            # Get task metadata from first message
            first_message = history[0]
            if not first_message or not first_message.get("content"):
                continue
                
            # Extract task from content
            task_content = first_message["content"][0]["text"] if isinstance(first_message["content"], list) else ""
            
            # Calculate task size
            task_size = 0
            for root, _, files in os.walk(task_dir):
                for file in files:
                    task_size += os.path.getsize(os.path.join(root, file))
            
            tasks.append({
                "id": task_id,
                "ts": int(task_id),  # Task ID is timestamp
                "task": task_content,
                "size": task_size
            })
        except Exception as e:
            print(f"Error loading task {task_id}: {e}")
            continue
            
    return sorted(tasks, key=lambda x: x["ts"], reverse=True)

def get_latest_task() -> Optional[Dict]:
    """Get the most recent task's metadata.
    
    Returns:
        Optional[Dict]: The latest task's metadata or None if no tasks exist
    """
    tasks = get_task_history()
    return tasks[0] if tasks else None

def get_latest_task_id() -> Optional[str]:
    """Get the ID of the most recent task.
    
    Returns:
        Optional[str]: The latest task ID or None if no tasks exist
    """
    latest_task = get_latest_task()
    return latest_task["id"] if latest_task else None

def get_next_llm_response_number(task_id: str) -> int:
    """Get the next available LLM response number for a task.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        int: The next available response number
    """
    task_dir = ensure_task_dir_exists(task_id)
    existing_responses = [f for f in os.listdir(task_dir) if f.startswith("LLM_response_")]
    if not existing_responses:
        return 1
    
    numbers = [int(f.split("_")[-1]) for f in existing_responses]
    return max(numbers) + 1

def save_llm_response(task_id: str, response: Union[str, Dict]) -> None:
    """Save an LLM response to disk with an incremental number.
    
    Args:
        task_id: The unique identifier for the task
        response: The LLM response to save (string or dict)
    """
    task_dir = ensure_task_dir_exists(task_id)
    response_number = get_next_llm_response_number(task_id)
    response_file = os.path.join(task_dir, f"LLM_response_{response_number}")
    
    with open(response_file, "w", encoding="utf-8") as f:
        if isinstance(response, dict):
            json.dump(response, f, indent=2)
        else:
            f.write(response)

def load_llm_responses(task_id: str) -> List[Union[str, Dict]]:
    """Load all LLM responses for a task from disk.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        List[Union[str, Dict]]: List of LLM responses
    """
    task_dir = ensure_task_dir_exists(task_id)
    responses = []
    
    for file in sorted(os.listdir(task_dir)):
        if not file.startswith("LLM_response_"):
            continue
            
        file_path = os.path.join(task_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                response = json.load(f)
            except json.JSONDecodeError:
                # If not JSON, read as plain text
                f.seek(0)
                response = f.read()
            responses.append(response)
            
    return responses
