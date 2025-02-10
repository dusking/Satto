# Satto

Satto is a powerful CLI tool that enables task execution using natural language commands. It leverages AI to understand user intent and perform actions such as modifying code, running commands, and managing files. Originally inspired by [Cline](https://github.com/saoudrizwan/cline), Satto brings a similar automation approach to the Python ecosystem.

## Requirements

### Python

- Python 3.8 or higher

### System Dependencies

- **ripgrep** (Required for code search functionality)
  - macOS: `brew install ripgrep`
  - Ubuntu/Debian: `apt install ripgrep`
  - Windows: `choco install ripgrep` or `scoop install ripgrep`
  - [Other installation options](https://github.com/BurntSushi/ripgrep#installation)

## Installation

Install Satto directly from GitHub:

```bash
pip install git+https://github.com/dusking/satto.git
```

## Configuration

Satto requires a configuration file located at `~/.config/satto/config.json`. Below is a sample configuration:

```json
{
    "selected_api_provider": "api_provider_anthropic",
    "max_consecutive_mistake_count": 3,
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
    "api_provider_anthropic": {
        "name": "anthropic",
        "api_key": "sk-ant-***",
        "model": "claude-3-5-sonnet-20241022"
    },
    "api_provider_openai_native": {
        "name": "openai-native",
        "api_key": "sk-***",
        "model": "gpt-4",
        "temperature": 0.8,
        "stream": true,
        "stream_options": {"include_usage": true}
    },
    "api_provider_openai_reasoning_effort": {
        "name": "openai-native",
        "api_key": "sk-***",
        "model": "o1",
        "reasoning_effort": "high"
    },
    "api_provider_azure": {
        "name": "openai-azure",
        "api_key": "",
        "model": "gpt-4",
        "base_url": "",
        "azure_api_version": ""
    },
    "api_provider_deepseek": {
        "name": "deepseek",
        "api_key": "",
        "model": "deepseek-chat"
    },
    "api_provider_together": {
        "name": "together",
        "api_key": "",
        "model": "deepseek-ai/DeepSeek-R1",
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["<｜end▁of▁sentence｜>"],
        "stream": true
    },
    "task_list_files": {
        "dirs_to_ignore": [
            "node_modules", "__pycache__", "env", "venv",
            "target/dependency", "build/dependencies", "dist",
            "out", "bundle", "vendor", "tmp", "temp",
            "deps", "pkg", "Pods", ".*"
        ]
    }
}
```

### Configuration Details

- **`selected_api_provider`**: Specifies the active API provider configuration (e.g., `api_provider_openai_native`, `api_provider_anthropic`).
- **`max_consecutive_mistake_count`**: Maximum allowed consecutive mistakes before termination.
- **`auto_approval`**: Controls automatic approval settings:
  - `enabled`: Enables or disables auto-approval.
  - `actions`: Defines which actions can be auto-approved.
  - `max_requests`: Limits auto-approved requests per session.
  - `enable_notifications`: Enables/disables notifications for auto-approved actions.

### API Providers

Satto supports multiple API providers, each with unique configurations. The active provider is determined by `selected_api_provider`.

#### Example Multiple Provider Configurations

```json
{
    "selected_api_provider": "api_provider_openai_prod",
    "api_provider_openai_prod": {
        "name": "openai-native",
        "api_key": "sk-prod-***",
        "model": "gpt-4"
    },
    "api_provider_openai_dev": {
        "name": "openai-native",
        "api_key": "sk-dev-***",
        "model": "gpt-3.5-turbo"
    }
}
```

#### Supported Providers

- **Anthropic Claude** (`name: "anthropic"`):

  - `api_key`: Your Anthropic API key
  - `model`: Model selection (e.g., "claude-3-5-sonnet-20241022")

- **OpenAI** (`name: "openai-native"`):

  - `api_key`: OpenAI API key
  - `model`: Model selection (e.g., "gpt-4")
  - `temperature`: Model temperature (0-1)
  - `stream`: Enables streaming responses
  - `stream_options`: Additional streaming settings

- **Azure OpenAI** (`name: "openai-azure"`):

  - `api_key`: Azure OpenAI API key
  - `model`: Model selection
  - `base_url`: Azure API endpoint
  - `azure_api_version`: API version

- **DeepSeek** (`name: "deepseek"`):

  - `api_key`: DeepSeek API key
  - `model`: Model selection (e.g., "deepseek-chat")

Each provider configuration must include a `name` field. The `selected_api_provider` determines which configuration is active.

## Features

- Execute tasks via natural language commands
- Fast code searching using ripgrep
- File operations and management
- Command execution
- Context-aware conversation history
- And more...

## Usage

### Start a Task

Run a task using natural language:

```bash
satto start "make the attempt_api_request docstring simpler"
```

### Continue a Task

Refine or continue a previous task:

```bash
satto cont "please refine the description, make it a bit longer"
```

Satto maintains context between commands for iterative task refinement.

