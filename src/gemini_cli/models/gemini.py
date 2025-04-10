"""
Gemini model integration for the CLI tool.
"""

import logging
import time
from rich.console import Console
from rich.panel import Panel
import questionary

from ..utils import count_tokens
from ..tools import get_tool, AVAILABLE_TOOLS

# Setup logging (basic config, consider moving to main.py)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
log = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 10
CONTEXT_TRUNCATION_THRESHOLD_TOKENS = 800000  # Example token limit


class GeminiModel:
    """Interface for Gemini models using native function calling agentic loop."""

    def __init__(self, console: Console):
        """Initialize the Gemini model interface."""
        self.console = console

        # --- Tool Definition ---
        self.function_declarations = None  # Tools have been removed
        # ---

        # --- System Prompt (Native Functions & Planning) ---
        self.system_instruction = "Initialize system prompt."
        # ---

        # --- Initialize Persistent History ---
        self.chat_history = [
            {'role': 'user', 'parts': [self.system_instruction]},
            {'role': 'model', 'parts': ["Okay, I'm ready. Provide the directory context and your request."]}
        ]
        log.info("Initialized persistent chat history.")
        # ---
