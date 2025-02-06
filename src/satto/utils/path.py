"""Path utility functions for consistent path handling across platforms."""

import os
from pathlib import Path


def to_posix_path(path_str: str) -> str:
    """
    Convert a path string to use forward slashes, maintaining Windows extended-length path support.
    
    Args:
        path_str: The path string to convert
        
    Returns:
        Path string using forward slashes
    """
    # Extended-Length Paths in Windows start with "\\?\\"
    if path_str.startswith("\\\\?\\"):
        return path_str  # Preserve extended-length paths in Windows
    return path.replace(os.sep, "/")

def are_paths_equal(path1: str, path2: str) -> bool:
    """Check if two paths are equal, accounting for case sensitivity and normalization."""
    if os.path.abspath(path1) == os.path.abspath(path2):
        return True
    # os.path.normcase() Converts the path to lowercase on Windows (since Windows paths are case-insensitive).
    return os.path.normcase(os.path.normpath(path1)) == os.path.normcase(os.path.normpath(path2))


def get_readable_path(cwd: str, rel_path: str = "") -> str:
    """
    Get a user-friendly path string relative to the current working directory.
    
    Args:
        cwd: Current working directory
        rel_path: Relative or absolute path
        
    Returns:
        User-friendly path string
    """
    # Resolve the absolute path
    abs_path = os.path.abspath(os.path.join(cwd, rel_path))
    
    # If cwd is Desktop, show full path
    if are_paths_equal(cwd, os.path.join(os.path.expanduser("~"), "Desktop")):
        return to_posix_path(abs_path)
    
    # If path is the cwd, just show the base name
    if are_paths_equal(abs_path, cwd):
        return to_posix_path(os.path.basename(abs_path))
    
    # Show relative path if within cwd, otherwise show absolute path
    rel_to_cwd = os.path.relpath(abs_path, cwd)
    if abs_path.startswith(cwd):
        return to_posix_path(rel_to_cwd)
    return to_posix_path(abs_path)
