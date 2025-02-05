"""
This module provides functionality to perform regex searches on files using ripgrep.
"""

import asyncio
import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

MAX_RESULTS = 300

@dataclass
class SearchResult:
    """Represents a single search result from ripgrep."""
    file: str
    line: int
    column: int
    match: str
    before_context: List[str]
    after_context: List[str]

async def exec_ripgrep(bin_path: str, args: List[str]) -> str:
    """Execute ripgrep command and return its output."""
    process = await asyncio.create_subprocess_exec(
        bin_path,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    output = []
    line_count = 0
    max_lines = MAX_RESULTS * 5  # Limit output similar to TypeScript version

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        
        if line_count < max_lines:
            output.append(line.decode().rstrip())
            line_count += 1
        else:
            process.terminate()
            break

    error = await process.stderr.read()
    await process.wait()

    if error:
        error_msg = error.decode()
        raise RuntimeError(f"ripgrep process error: {error_msg}")

    return "\n".join(output)

def format_results(results: List[SearchResult], cwd: str) -> str:
    """Format search results into a readable string."""
    grouped_results = {}
    
    output = []
    if len(results) >= MAX_RESULTS:
        output.append(f"Showing first {MAX_RESULTS} of {MAX_RESULTS}+ results. Use a more specific search if necessary.\n")
    else:
        result_count = len(results)
        output.append(f"Found {result_count} result{'s' if result_count != 1 else ''}.\n")

    # Group results by file
    for result in results[:MAX_RESULTS]:
        rel_path = os.path.relpath(result.file, cwd).replace("\\", "/")
        if rel_path not in grouped_results:
            grouped_results[rel_path] = []
        grouped_results[rel_path].append(result)

    # Format each file's results
    for file_path, file_results in grouped_results.items():
        output.append(f"{file_path}\n│----")

        for idx, result in enumerate(file_results):
            all_lines = result.before_context + [result.match] + result.after_context
            for line in all_lines:
                output.append(f"│{line.rstrip()}")

            if idx < len(file_results) - 1:
                output.append("│----")

        output.append("│----\n")

    return "\n".join(output).rstrip()

async def regex_search_files(cwd: str, directory_path: str, regex: str, file_pattern: Optional[str] = None) -> str:
    """
    Search for a regex pattern in files using ripgrep.
    
    Args:
        cwd: Current working directory for relative path calculation
        directory_path: Directory to search in
        regex: Regular expression to search for (Rust regex syntax)
        file_pattern: Optional glob pattern to filter files (default: '*')
    
    Returns:
        Formatted string containing search results with context
    """
    # Find ripgrep in system PATH
    try:
        process = await asyncio.create_subprocess_exec(
            "where" if platform.system() == "Windows" else "which",
            "rg",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0:
            rg_path = stdout.decode().splitlines()[0] if platform.system() == "Windows" else stdout.decode().strip()
        else:
            raise RuntimeError(
                "Ripgrep (rg) not found. Please install ripgrep:\n"
                "- macOS: brew install ripgrep\n"
                "- Ubuntu/Debian: apt install ripgrep\n"
                "- Windows: choco install ripgrep or scoop install ripgrep\n"
                "For more installation options, visit: https://github.com/BurntSushi/ripgrep#installation"
            )
    except Exception as e:
        raise RuntimeError(
            f"Error finding ripgrep: {str(e)}\n"
            "Please ensure ripgrep (rg) is installed and available in your system PATH."
        )

    args = ["--json", "-e", regex, "--glob", file_pattern or "*", "--context", "1", directory_path]

    try:
        output = await exec_ripgrep(rg_path, args)
    except Exception as e:
        return f"Error: {str(e)}"

    if not output:
        return "No results found"

    results: List[SearchResult] = []
    current_result = None

    for line in output.split("\n"):
        if not line:
            continue

        try:
            parsed = json.loads(line)
            if parsed["type"] == "match":
                if current_result:
                    results.append(current_result)
                
                current_result = SearchResult(
                    file=parsed["data"]["path"]["text"],
                    line=parsed["data"]["line_number"],
                    column=parsed["data"]["submatches"][0]["start"],
                    match=parsed["data"]["lines"]["text"],
                    before_context=[],
                    after_context=[]
                )
            elif parsed["type"] == "context" and current_result:
                context_line = parsed["data"]["lines"]["text"]
                if parsed["data"]["line_number"] < current_result.line:
                    current_result.before_context.append(context_line)
                else:
                    current_result.after_context.append(context_line)
        except json.JSONDecodeError:
            print(f"Error parsing ripgrep output line: {line}", file=sys.stderr)
            continue
        except KeyError as e:
            print(f"Missing key in ripgrep output: {e}", file=sys.stderr)
            continue

    if current_result:
        results.append(current_result)

    return format_results(results, cwd)
