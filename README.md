# LM Code

LM Code is a powerful AI coding assistant for your terminal supporting multiple LLM models like Qwen, DeepSeek, and Gemini. With LM Code, you can interactively work on coding tasks, automate file operations, and improve your workflow directly from the command line.

---

## Features

- **Interactive CLI with AI Assistance**:
  - Chat with AI models for coding advice, file management, and more.
  - Markdown rendering for improved readability.
- **Multi-Model Support**:
  - Qwen, DeepSeek, Gemini, and more.
- **Automated Tool Usage**:
  - File operations: `view`, `edit`, `list`, `grep`, `glob`.
  - Directory operations: `ls`, `tree`, `create_directory`.
  - System commands: `bash`.
  - Quality checks: linting, formatting.
  - Test running: `pytest` and similar tools.
- **Customizable Configurations**:
  - Easily set default models and API keys.

---

## Installation

### Method 1: Install from PyPI (Recommended)

```bash
pip install code-lm
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/Panagiotis897/lm-code.git
cd lm-code

# Install the package
pip install -e .
```

---

## Setup

Before using LM Code, you need to set up your API keys for OpenRouter.

### Configure API Key

```bash
lmcode setup YOUR_OPENROUTER_API_KEY
```

This saves your API key in the configuration file located at `~/.config/gemini-code/config.yaml`.

---

## Usage

### Start an Interactive Session

```bash
# Start with the default model
lmcode

# Start with a specific model
lmcode --model qwen/qwen-2.5-coder-32b-instruct:free
```

### Manage Models

```bash
# Set a default model
lmcode set-default-model deepseek/deepseek-r1:free

# List all available models
lmcode list-models
```

---

## Supported Models

- **Qwen 2.5 Coder 32B**: `qwen/qwen-2.5-coder-32b-instruct:free`
- **Qwen QWQ 32B**: `qwen/qwq-32b:free`
- **DeepSeek R1**: `deepseek/deepseek-r1:free`
- **Gemma 3 (27B Italian)**: `google/gemma-3-27b-it:free`
- **Gemini 2.5 Pro Experimental**: `google/gemini-2.5-pro-exp-03-25:free`

---

## Interactive Commands

During an interactive session, you can use these commands:

- **`/exit`**: Exit the session.
- **`/help`**: Display help information.

---

## How It Works

LM Code uses native tools to enhance your coding experience. For instance:

1. You ask: "What files are in the current directory?"
2. LM Code uses the `ls` tool to fetch directory contents.
3. The assistant formats and presents the response.

This seamless integration of tools and AI makes LM Code a powerful coding partner.

---

## Development

LM Code is under active development. Contributions, feature requests, and feedback are welcome!

### Recent Changes

#### v0.1.0
- Rebranded from Gemini to LM Code.
- Integrated OpenRouter's Qwen model as the default.
- Added multi-model support for Qwen, DeepSeek, and Gemini.
- Overhauled CLI commands (`gemini` → `lmcode`).

#### v0.2.5
- Added some more models to the model list.
- Fixed some crucial bugs over the previous versions.
- Removed Gemini models as of now.
- Updated some models to use their latest versions instead of the outdated ones.

---

## Feture Updates
- Pricing will be introduced along with apropriate rate limits.
- More models will be introduced along with non-free ones.
- MCP Server intergration will be added as well.
- More providers are coming soon.

## Known Issues

- If you used earlier versions, you might need to delete your old configuration:
  ```bash
  rm -rf ~/.config/gemini-code
  ```

---

## License

MIT License
