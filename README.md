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
