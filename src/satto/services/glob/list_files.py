"""File listing functionality with smart directory traversal and filtering."""
import os
import asyncio
from pathlib import Path
from typing import List, Tuple, Set
import glob
import fnmatch
from ...utils.path import are_paths_equal, to_posix_path
from ...services.config.list_files_settings import ListFilesSettings

async def list_files(dir_path: str, recursive: bool, limit: int, settings: ListFilesSettings = None) -> Tuple[List[str], bool]:
    """List files in a directory with smart filtering and traversal.
    
    Args:
        dir_path: Directory path to list files from
        recursive: Whether to recursively list files in subdirectories
        limit: Maximum number of files to return
        settings: Optional settings for file listing behavior
        
    Returns:
        Tuple of (list of file paths, whether limit was hit)
    """
    
    print(f">>> {settings.dirs_to_ignore}")
    
    absolute_path = os.path.abspath(dir_path)
    
    # Do not allow listing files in root or home directory
    root = "/" if os.name != "nt" else os.path.splitdrive(absolute_path)[0] + "\\"
    if are_paths_equal(absolute_path, root):
        return [root], False
        
    home_dir = os.path.expanduser("~")
    if are_paths_equal(absolute_path, home_dir):
        return [home_dir], False

    if recursive:
        files, hit_limit = await globby_level_by_level(absolute_path, limit, settings)
    else:
        # For non-recursive, just get immediate files/dirs
        pattern = os.path.join(absolute_path, "*")
        files = []
        for path in glob.glob(pattern):
            if len(files) >= limit:
                return files, True
            # Add trailing slash for directories
            if os.path.isdir(path):
                path = f"{path}/"
            files.append(path)
        hit_limit = len(files) >= limit
        
    return files, hit_limit

async def globby_level_by_level(dir_path: str, limit: int, settings: ListFilesSettings = None) -> Tuple[List[str], bool]:
    """Breadth-first traversal of directory structure level by level up to a limit.
    
    Args:
        dir_path: Root directory to start traversal from
        limit: Maximum number of files to return
        settings: Optional settings for file listing behavior
        
    Returns:
        Tuple of (list of file paths, whether limit was hit)
    """
    results: Set[str] = set()
    queue: List[str] = [os.path.join(dir_path, "*")]
    
    if settings is None:
        settings = ListFilesSettings()
        
    async def globbing_process() -> List[str]:
        while queue and len(results) < limit:
            pattern = queue.pop(0)
            
            # Check if pattern should be ignored based on gitignore-style rules
            should_ignore = False
            for ignore_pattern in settings.dirs_to_ignore:
                if fnmatch.fnmatch(pattern, f"**/{ignore_pattern}/**"):
                    should_ignore = True
                    break
            if should_ignore:
                continue
                
            # Get files at this level
            for path in glob.glob(pattern):
                if len(results) >= limit:
                    break
                    
                # Add trailing slash for directories
                if os.path.isdir(path):
                    path = f"{path}/"
                    # Add subdirectory pattern to queue for BFS
                    queue.append(os.path.join(path, "*"))
                    
                results.add(path)
                
        return sorted(list(results)[:limit])
    
    try:
        # Run globbing process with timeout
        globbing_task = asyncio.create_task(globbing_process())
        files = await asyncio.wait_for(globbing_task, timeout=10.0)
        return files, len(files) >= limit
        
    except asyncio.TimeoutError:
        print("Globbing timed out, returning partial results")
        files = sorted(list(results)[:limit])
        return files, len(files) >= limit
