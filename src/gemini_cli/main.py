"""
Main entry point for the LM Code application.
Targets OpenRouter and other supported models. Includes ASCII Art welcome.
"""

import os
import sys
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from pathlib import Path
import yaml
import logging
import time

from .models.openrouter import OpenRouterModel, list_available_models
from .config import Config
from .utils import count_tokens
from .tools import AVAILABLE_TOOLS

# Setup console and config
console = Console()  # Create console instance HERE
try:
    config = Config()
except Exception as e:
    console.print(f"[bold red]Error loading configuration:[/bold red] {e}")
    config = None

# Setup logging - MORE EXPLICIT CONFIGURATION
log_level = os.environ.get("LOG_LEVEL", "WARNING").upper()  # <-- Default back to WARNING
log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# Get root logger and set level
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Remove existing handlers to avoid duplicates if basicConfig was called elsewhere
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Add a stream handler to output to console
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level)
formatter = logging.Formatter(log_format)
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

log = logging.getLogger(__name__)  # Get logger for this module
log.info(f"Logging initialized with level: {log_level}")  # Confirm level

# --- Default Model ---
DEFAULT_MODEL = "qwen/qwen-2.5-coder-32b-instruct:free"
# --- ---

# --- Supported Models ---
SUPPORTED_MODELS = [
    {"id": "qwen/qwen-2.5-coder-32b-instruct:free", "description": "Qwen 2.5 Coder 32B"},
    {"id": "qwen/qwq-32b:free", "description": "Qwen QWQ 32B"},
    {"id": "deepseek/deepseek-r1-0528:free", "description": "DeepSeek R1"},
    {"id": "google/gemma-3-27b-it:free", "description": "Gemma 3 27B Italian"},
    {"id": "qwen/qwen3-coder:free", "description": "Qwen 3 Coder"},
    {"id": "deepseek/deepseek-chat-v3.1:free", "description": "DeepSeek V3.1"},
]
# --- ---

# --- ASCII Art Definition ---
LM_CODE_ART = r"""

[green]
  ██╗     ███╗   ███╗     ██████╗ ██████╗ ██████╗ ███████╗
  ██║     ████╗ ████║    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
  ██║     ██╔████╔██║    ██║     ██║   ██║██║  ██║█████╗  
  ██║     ██║╚██╔╝██║    ██║     ██║   ██║██║  ██║██╔══╝  
  ███████╗██║ ╚═╝ ██║    ╚██████╗╚██████╔╝██████╔╝███████╗
  ╚══════╝╚═╝     ╚═╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
[/green]
"""
# --- End ASCII Art ---


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.option(
    '--model', '-m',
    help=f'Model ID to use (e.g., qwen/qwen-2.5-coder-32b-instruct:free). Default: {DEFAULT_MODEL}',
    default=None
)
@click.pass_context
def cli(ctx, model):
    """Interactive CLI for LM models with coding assistance tools."""
    if not config:
        console.print("[bold red]Configuration could not be loaded. Cannot proceed.[/bold red]")
        sys.exit(1)

    if ctx.invoked_subcommand is None:
        model_name_to_use = model or config.get_default_model() or DEFAULT_MODEL
        log.info(f"Attempting to start interactive session with model: {model_name_to_use}")
        # Pass the console object to start_interactive_session
        start_interactive_session(model_name_to_use, console)

@cli.command(name="setup")
@click.argument('key', required=True)
def setup(key):
    if not config: console.print("[bold red]Config error.[/bold red]"); return
    try: config.set_api_key("openrouter", key); console.print("[green]✓[/green] OpenRouter API key saved.")
    except Exception as e: console.print(f"[bold red]Error saving API key:[/bold red] {e}")

@cli.command(name="set-default-model")
@click.argument('model_name', required=True)
def set_default_model(model_name):
    if not config: console.print("[bold red]Config error.[/bold red]"); return
    try: config.set_default_model(model_name); console.print(f"[green]✓[/green] Default model set to [bold]{model_name}[/bold].")
    except Exception as e: console.print(f"[bold red]Error setting default model:[/bold red] {e}")

@cli.command(name="list-models")
def list_models():
    if not config: console.print("[bold red]Config error.[/bold red]"); return
    api_key = config.get_api_key("openrouter")
    if not api_key: console.print("[bold red]Error:[/bold red] API key not found. Run 'lmcode setup YOUR_OPENROUTER_API_KEY'."); return
    console.print("[yellow]Fetching models...[/yellow]")
    try:
        models_list = list_available_models(api_key)
        if not models_list:
            console.print("[red]No models found or fetch error.[/red]")
        else:
            console.print("\n[bold cyan]Supported Models:[/bold cyan]")
            for model in SUPPORTED_MODELS:
                console.print(f"- [bold green]{model['id']}[/bold green]: {model['description']}")
            console.print("\nUse 'lmcode --model MODEL' or 'lmcode set-default-model MODEL'.")
    except Exception as e:
        console.print(f"[bold red]Error listing models:[/bold red] {e}")
        log.error("List models failed", exc_info=True)


# --- Modified start_interactive_session to use OpenRouter ---
def start_interactive_session(model_name: str, console: Console):
    """Start an interactive chat session with the selected OpenRouter model."""
    if not config: console.print("[bold red]Config error.[/bold red]"); return

    # --- Display Welcome Art ---
    console.clear()
    console.print(LM_CODE_ART)
    console.print(Panel("[b]Welcome to LM Code AI Assistant![/b]", border_style="green", expand=False))
    time.sleep(0.1)
    # --- End Welcome Art ---

    api_key = config.get_api_key("openrouter")
    if not api_key:
        console.print("\n[bold red]Error:[/bold red] OpenRouter API key not found.")
        console.print("Please run [bold]'lmcode setup YOUR_OPENROUTER_API_KEY'[/bold] first.")
        return

    try:
        console.print(f"\nInitializing model [bold]{model_name}[/bold]...")
        # Pass the console object to OpenRouterModel constructor
        model = OpenRouterModel(api_key=api_key, console=console, model_name=model_name)
        console.print("[green]Model initialized successfully.[/green]\n")

    except Exception as e:
        console.print(f"\n[bold red]Error initializing model '{model_name}':[/bold red] {e}")
        log.error(f"Failed to initialize model {model_name}", exc_info=True)
        console.print("Please check model name, API key permissions, network. Use 'lmcode list-models'.")
        return

    # --- Session Start Message ---
    console.print("Type '/help' for commands, '/exit' or Ctrl+C to quit.")

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")

            if user_input.lower() == '/exit': break
            elif user_input.lower() == '/help': show_help(); continue

            # Display initial "thinking" status - generate handles intermediate ones
            response_text = model.generate(user_input)

            if response_text is None and user_input.startswith('/'): console.print(f"[yellow]Unknown command:[/yellow] {user_input}"); continue
            elif response_text is None: console.print("[red]Received an empty response from the model.[/red]"); log.warning("generate() returned None unexpectedly."); continue

            console.print("[bold green]Assistant:[/bold green]")
            console.print(Markdown(response_text), highlight=True)

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Exiting.[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]An error occurred during the session:[/bold red] {e}")
            log.error("Error during interactive loop", exc_info=True)


def show_help():
    """Show help information for interactive mode."""
    tool_list_formatted = ""
    if AVAILABLE_TOOLS:
        # Add indentation for the bullet points
        tool_list_formatted = "\n".join([f"  • [white]`{name}`[/white]" for name in sorted(AVAILABLE_TOOLS.keys())])
    else:
        tool_list_formatted = "  (No tools available)"
        
    # Use direct rich markup and ensure newlines are preserved
    help_text = f""" [bold]Help[/bold]

 [cyan]Interactive Commands:[/cyan]
  /exit
  /help

 [cyan]CLI Commands:[/cyan]
  lmcode setup KEY
  lmcode list-models
  lmcode set-default-model NAME
  lmcode --model NAME

 [cyan]Workflow Hint:[/cyan] Analyze -> Plan -> Execute -> Verify -> Summarize

 [cyan]Available Tools:[/cyan]
{tool_list_formatted}
"""
    # Print directly to Panel without Markdown wrapper
    console.print(Panel(help_text, title="Help", border_style="green", expand=False))


if __name__ == "__main__":
    cli()
