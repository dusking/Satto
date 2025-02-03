from typing import Optional

class McpHub:
    """Simple McpHub class to avoid circular imports."""
    def __init__(self):
        self.is_connecting: bool = False
        self.connections = []
