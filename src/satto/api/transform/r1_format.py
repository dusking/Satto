from typing import Any, Dict, List, Union

def convert_to_r1_format(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts messages to OpenAI format while merging consecutive messages with the same role.
    This is required for DeepSeek Reasoner which does not support successive messages with the same role.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys

    Returns:
        List of OpenAI messages where consecutive messages with the same role are combined
    """
    merged: List[Dict[str, Any]] = []

    for message in messages:
        message_content = message["content"]
        
        # Handle content arrays (for image support)
        if isinstance(message_content, list):
            text_parts = []
            image_parts = []
            has_images = False

            for part in message_content:
                if part["type"] == "text":
                    text_parts.append(part["text"])
                elif part["type"] == "image":
                    has_images = True
                    image_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{part['source']['media_type']};base64,{part['source']['data']}"
                        }
                    })

            if has_images:
                parts = []
                if text_parts:
                    parts.append({"type": "text", "text": "\n".join(text_parts)})
                parts.extend(image_parts)
                message_content = parts
            else:
                message_content = "\n".join(text_parts)

        # If last message has same role, merge the content
        if merged and merged[-1]["role"] == message["role"]:
            last_message = merged[-1]
            
            # Both are strings
            if isinstance(last_message["content"], str) and isinstance(message_content, str):
                last_message["content"] += f"\n{message_content}"
            
            # Handle array content (for images)
            else:
                last_content = (
                    last_message["content"] 
                    if isinstance(last_message["content"], list)
                    else [{"type": "text", "text": last_message["content"] or ""}]
                )
                
                new_content = (
                    message_content
                    if isinstance(message_content, list)
                    else [{"type": "text", "text": message_content}]
                )
                
                merged_content = [*last_content, *new_content]
                last_message["content"] = merged_content

        # Add as new message
        else:
            merged.append({
                "role": message["role"],
                "content": message_content
            })

    return merged
