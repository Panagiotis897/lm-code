# LM Code

LM Code is a powerful AI coding assistant for your terminal supporting 17 free models via OpenRouter. Chat with AI models, automate file operations, and boost your workflow directly from the command line.

---

## Features

- **Interactive CLI with AI Assistance**:
  - Chat with AI models for coding advice, file management, and more.
  - Markdown rendering for improved readability.
- **17 Free Models via OpenRouter**:
  - NVIDIA Nemotron, Qwen, OpenAI, Meta Llama, Mistral, and more.
- **Automated Tool Usage**:
  - File operations: `view`, `edit`, `grep`, `glob`.
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
git clone https://github.com/Panagiotis897/lm-code.git
cd lm-code
pip install -e .
```

---

## Setup

Before using LM Code, set up your API key for OpenRouter.

```bash
lmcode setup YOUR_OPENROUTER_API_KEY
```

This saves your API key in `~/.config/lm-code/config.yaml`.

---

## Usage

### Start an Interactive Session

```bash
# Start with the default model (NVIDIA Nemotron 3 Super 120B)
lmcode

# Start with a specific model
lmcode --model qwen/qwen3-coder:free
```

### Manage Models

```bash
# Set a default model
lmcode set-default-model qwen/qwen3-coder:free

# List all available models
lmcode list-models
```

---

## Supported Models

| Model | ID | Context | Strength |
|---|---|---|---|
| NVIDIA Nemotron 3 Super 120B | `nvidia/nemotron-3-super-120b-a12b:free` | 262K | Default |
| Qwen3 Coder 480B | `qwen/qwen3-coder:free` | 262K | Best coding |
| OpenAI GPT-OSS 120B | `openai/gpt-oss-120b:free` | 131K | Open source |
| Llama 3.3 70B | `meta-llama/llama-3.3-70b-instruct:free` | 66K | General purpose |
| Mistral Small 3.1 24B | `mistralai/mistral-small-3.1-24b-instruct:free` | 128K | Vision + tools |
| Qwen3 Next 80B A3B | `qwen/qwen3-next-80b-a3b-instruct:free` | 262K | Tool calling |
| NVIDIA Nemotron Nano 9B v2 | `nvidia/nemotron-nano-9b-v2:free` | 128K | Fast |
| Trinity Large Preview | `arcee-ai/trinity-large-preview:free` | 131K | Reasoning |
| Trinity Mini | `arcee-ai/trinity-mini:free` | 131K | Fast & efficient |
| GLM 4.5 Air | `z-ai/glm-4.5-air:free` | 131K | Tool calling |
| Step 3.5 Flash | `stepfun/step-3.5-flash:free` | 256K | Tool calling |
| MiniMax M2.5 | `minimax/minimax-m2.5:free` | 197K | Tool calling |
| OpenAI GPT-OSS 20B | `openai/gpt-oss-20b:free` | 131K | Lightweight |
| Gemma 3 27B | `google/gemma-3-27b-it:free` | 131K | Vision |
| Qwen3 4B | `qwen/qwen3-4b:free` | 41K | Ultra lightweight |
| Hermes 3 Llama 3.1 405B | `nousresearch/hermes-3-llama-3.1-405b:free` | 131K | Large Llama |
| Llama 3.2 3B | `meta-llama/llama-3.2-3b-instruct:free` | 131K | Tiny & fast |

---

## Interactive Commands

During an interactive session:

- **`/exit`**: Exit the session.
- **`/help`**: Display help information.

---

## How It Works

LM Code uses native tools to enhance your coding experience:

1. You ask: "What files are in the current directory?"
2. LM Code uses the `ls` tool to fetch directory contents.
3. The assistant formats and presents the response.

---

## Development

LM Code is under active development. Contributions, feature requests, and feedback are welcome!

### Changelog

#### v0.3.0
- Updated default model to NVIDIA Nemotron 3 Super 120B.
- Added 17 free models from OpenRouter (previously 6).
- Fixed `ModuleNotFoundError: No module named 'gemini_cli'` from stale entry point after package rename.
- Fixed `UnicodeDecodeError` on Windows (cp1253) for all subprocess commands.
- Fixed API URL (`/chat/completions` was missing) causing HTML response errors.
- Improved API error handling for empty/invalid responses.
- Added API key validation on startup.
- Tool parameter descriptions now use `args_schema` when available.
- Removed conflicting `logging.basicConfig` from openrouter module.
- Added UTF-8 encoding with fallback to all subprocess calls.

#### v0.2.5
- Added more models to the model list.
- Fixed crucial bugs from previous versions.
- Removed legacy Gemini module.
- Updated models to latest versions.

#### v0.1.0
- Rebranded to LM Code.
- Integrated OpenRouter as the default provider.
- Added multi-model support.
- Overhauled CLI commands.

---

## Future Plans
- Non-free model support.
- MCP Server integration.
- Additional providers.

---

## Known Issues

- If you used earlier versions, you may need to delete your old configuration:
  ```bash
  rm -rf ~/.config/lm-code
  ```

---

## License

MIT License
