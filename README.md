# Satto

Satto is a powerful CLI tool that helps you accomplish tasks using natural language commands. It leverages AI to understand your intent and execute the appropriate actions, whether it's making code changes, running commands, or managing files. The project started as a Python implementation of [Cline](https://github.com/saoudrizwan/cline), bringing its innovative approach to task automation to the Python ecosystem.

## Requirements

### Python
- Python 3.8 or higher

### System Dependencies
- **ripgrep**: Required for code searching functionality
  - macOS: `brew install ripgrep`
  - Ubuntu/Debian: `apt install ripgrep`
  - Windows: `choco install ripgrep` or `scoop install ripgrep`
  - Other installation options: [ripgrep installation guide](https://github.com/BurntSushi/ripgrep#installation)

## Installation

```bash
pip install git+https://github.com/dusking/satto.git
```

## Configuration

Satto requires a configuration file located at `~/.config/satto/config.json`. Create this file with the following default values:

```json
{
    "auto_approval": {
        "enabled": true,
        "actions": {
            "read_files": true,
            "edit_files": true,
            "execute_commands": false,
            "use_browser": false,
            "use_mcp": false,
            "attempt_completion": true
        },
        "max_requests": 20,
        "enable_notifications": false
    },
    "auth_anthropic": {
        "api_key": "sk-ant-***",
        "api_provider": "anthropic",
        "model_id": "claude-3-5-sonnet-20241022"
    },
    "task_ist_files": {
        "dirs_to_ignore": [
            "node_modules",
            "__pycache__",
            "env",
            "venv",
            "target/dependency",
            "build/dependencies",
            "dist",
            "out",
            "bundle",
            "vendor",
            "tmp",
            "temp",
            "deps",
            "pkg",
            "Pods",
            ".*"
        ]
    }
}
```

The configuration includes:
- `auto_approval`: Settings for automatic approval of different actions
  - `enabled`: Enable/disable auto-approval globally
  - `actions`: Specific actions that can be auto-approved
  - `max_requests`: Maximum number of auto-approved requests per session
  - `enable_notifications`: Enable/disable notifications for auto-approved actions
- `auth_anthropic`: Authentication settings for Anthropic's API
  - `api_key`: Your Anthropic API key
  - `api_provider`: API provider (currently supports "anthropic")
  - `model_id`: The model ID to use

## Features

- Natural language task execution
- Fast code searching with ripgrep integration
- File operations and manipulation
- Command execution
- Conversation history and context awareness
- And more...

## Usage

Satto provides two main commands:

### `satto start`

Start a new task with a natural language description:

```bash
satto start "make the attempt_api_request docstring simpler"
```

### `satto cont`

Continue or refine the previous task:

```bash
satto cont "please refine the description, make it a bit longer"
```

This allows for iterative refinement of tasks, with Satto maintaining context between commands.
