# Installing and Using LM Code

This guide explains how to install, configure, and use LM Code.

---

## Installation Options

### Option 1: Install from PyPI (Recommended)

```bash
pip install code-lm
```

### Option 2: Install from Source

```bash
git clone https://github.com/Panagiotis897/lm-code.git
cd lm-code
pip install -e .
```

---

## Setting Up Your API Key

Before using LM Code, you need to set up your OpenRouter API key:

```bash
lmcode setup YOUR_OPENROUTER_API_KEY
```

Your API key is stored securely in `~/.config/gemini-code/config.yaml`.

---

## Using LM Code

### Starting a Session

```bash
# Start with default model
lmcode

# Start with a specific model
lmcode --model qwen/qwen-2.5-coder-32b-instruct:free
```

### Available Commands

During an interactive session, you can use these commands:

- `/help` - Display help information
- `/exit` - Exit the chat session

---

## Configuration Options

Set your default model:

```bash
lmcode set-default-model deepseek/deepseek-r1:free
```

---

## Troubleshooting

If you encounter issues:

1. Verify your API key is correct: `cat ~/.config/gemini-code/config.yaml`
2. Ensure you have a working internet connection.
3. Check that you have Python 3.7+ installed: `python --version`.
4. Make sure the required packages are installed: `pip list | grep code-lm`.

For more help, visit: https://github.com/Panagiotis897/lm-code
