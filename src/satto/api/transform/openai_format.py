from typing import List, Dict, Any

def convert_to_openai_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert messages to OpenAI chat format.
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        List of messages formatted for OpenAI chat completions API
    """
    openai_messages = []
    
    for message in messages:
        if isinstance(message.get("content"), list):
            # Handle messages with multiple content parts
            content_parts = []
            for part in message["content"]:
                if part.get("type") == "text":
                    content_parts.append(part.get("text", ""))
            content = "\n".join(content_parts)
        else:
            content = message.get("content", "")
            
        openai_messages.append({
            "role": message.get("role", "user"),
            "content": content
        })
        
    return openai_messages
