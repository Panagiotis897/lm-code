"""
OpenRouter model integration for the CLI tool.
"""

import requests
import json
import logging
import time
from typing import Optional, Dict, List, Any
from rich.console import Console
from rich.panel import Panel

from ..utils import count_tokens
from ..tools import get_tool, AVAILABLE_TOOLS

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
log = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 10
FALLBACK_MODEL = "qwen/qwen-2.5-coder-32b-instruct:free"
CONTEXT_TRUNCATION_THRESHOLD_TOKENS = 12000  # Approximate token limit for Qwen model

# Function definitions for tools
class FunctionDeclaration:
    def __init__(self, name: str, description: str, parameters: Dict):
        self.name = name
        self.description = description
        self.parameters = parameters


class OpenRouterModel:
    """Interface for OpenRouter models with function calling support."""

    def __init__(self, api_key: str, console: Console, model_name: str = FALLBACK_MODEL):
        """Initialize the OpenRouter model interface."""
        self.api_key = api_key
        self.initial_model_name = model_name
        self.current_model_name = model_name
        self.console = console
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Panagiotis897/lm-code",  # Optional: site URL
            "X-Title": "LM Code"  # Optional: title of your application
        }

        # --- Tool Definition ---
        self.function_declarations = self._create_tool_definitions()
        self.openrouter_tools = self._convert_to_openrouter_tools() if self.function_declarations else None
        # ---

        # --- System Prompt (Native Functions & Planning) ---
        self.system_instruction = self._create_system_prompt()
        # ---

        # --- Initialize Persistent History ---
        self.chat_history = [
            {'role': 'system', 'content': self.system_instruction},
            {'role': 'assistant', 'content': "Okay, I'm ready. Provide the directory context and your request."}
        ]
        log.info("Initialized persistent chat history.")
        # ---

        try:
            # Test the connection to make sure the model is valid
            self._test_model_connection()
            log.info("OpenRouterModel initialized successfully (Native Function Calling Agent Loop).")
        except Exception as e:
            log.error(f"Fatal error initializing OpenRouter model '{self.current_model_name}': {str(e)}", exc_info=True)
            raise Exception(f"Could not initialize OpenRouter model: {e}") from e

    def _test_model_connection(self):
        """Test the connection to the model."""
        log.info(f"Testing connection to model: {self.current_model_name}")
        try:
            # Simple test message
            payload = {
                "model": self.current_model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Test connection"}
                ],
                "max_tokens": 10
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )

            if response.status_code != 200:
                log.error(f"API returned status code {response.status_code}: {response.text}")
                raise Exception(f"API error: {response.status_code} - {response.text}")

            log.info(f"Model connection test successful: {self.current_model_name}")
        except Exception as e:
            log.error(f"Connection test failed: {e}")
            raise e

    def get_available_models(self):
        """List available models for the API key."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
            response.raise_for_status()
            models_data = response.json()

            openrouter_models = []
            for model in models_data.get("data", []):
                model_info = {
                    "name": model.get("id", ""),
                    "display_name": model.get("name", ""),
                    "description": model.get("description", ""),
                    "context_length": model.get("context_length", 0)
                }
                openrouter_models.append(model_info)
            return openrouter_models
        except Exception as e:
            log.error(f"Error listing models: {str(e)}")
            return [{"error": str(e)}]

    def _convert_to_openrouter_tools(self):
        """Convert function declarations to OpenRouter tools format."""
        tools = []
        for func_decl in self.function_declarations:
            tools.append({
                "type": "function",
                "function": {
                    "name": func_decl.name,
                    "description": func_decl.description,
                    "parameters": func_decl.parameters
                }
            })
        return tools

    def _create_tool_definitions(self) -> list[FunctionDeclaration] | None:
        """
        Dynamically create FunctionDeclarations from AVAILABLE_TOOLS.
        """
        declarations = []
        for tool_name, tool_instance in AVAILABLE_TOOLS.items():
            if hasattr(tool_instance, 'get_function_declaration'):
                declaration_data = tool_instance.get_function_declaration()
                if declaration_data:
                    try:
                        openrouter_declaration = FunctionDeclaration(
                            name=declaration_data['name'],
                            description=declaration_data.get('description', ''),
                            parameters=declaration_data.get('parameters', {})
                        )
                        declarations.append(openrouter_declaration)
                        log.debug(f"Generated FunctionDeclaration for tool: {tool_name}")
                    except Exception as e:
                        log.error(f"Error processing tool {tool_name}: {e}", exc_info=True)
                else:
                    log.warning(f"Tool {tool_name} has 'get_function_declaration' but it returned None.")
            else:
                log.warning(f"Tool {tool_name} does not have a 'get_function_declaration' method. Skipping.")

        log.info(f"Created {len(declarations)} function declarations for native tool use.")
        return declarations if declarations else None

    def _create_system_prompt(self) -> str:
        """Creates the system prompt, emphasizing native functions and planning."""
        tool_descriptions = []
        if self.function_declarations:
            for func_decl in self.function_declarations:
                params_str = ", ".join(
                    f"{name}: {details.get('type', 'unknown')} # {details.get('description', '')}"
                    for name, details in func_decl.parameters.get('properties', {}).items()
                )
                description = func_decl.description or "(No description provided)"
                tool_descriptions.append(f"- `{func_decl.name}({params_str})`: {description}")
        else:
            tool_descriptions.append(" - (No tools available with function declarations)")

        tool_list_str = "\n".join(tool_descriptions)

        return f"""You are LM Code, an AI coding assistant running in a CLI environment.
Your goal is to help the user with their coding tasks by understanding their request, planning the necessary steps, and using the available tools via **native function calls**.

Available Tools (Use ONLY these via function calls):
{tool_list_str}

Workflow:
1. **Analyze & Plan:** Understand the user's request based on the provided directory context (`ls` output) and the request itself. For non-trivial tasks, **first outline a brief plan** of the steps needed.
2. **Execute:** If a plan is not needed or after outlining the plan, make the **first necessary function call** to execute the next step (e.g., `view` a file, `edit` a file, `grep` for text, `tree` for directory structure).
3. **Observe:** You will receive the result of the function call (or a message indicating user rejection). Use this result to inform your next step.
4. **Repeat:** Based on the result, make the next function call required to achieve the user's goal. Continue calling functions sequentially until the task is complete.
5. **Complete:** Once the *entire* task is finished, **you MUST call the `task_complete` function**, providing a concise summary of what was done in the `summary` argument. 

Important Rules:
* **Use Native Functions:** ONLY interact with tools by making function calls as defined above. Do NOT output tool calls as text.
* **Sequential Calls:** Call functions one at a time. You will get the result back before deciding the next step. Do not try to chain calls in one turn.
* **Initial Context Handling:** When the user asks a general question about the codebase contents, your **first step** should be to use tools like `ls`, `tree` or `find` to gather this information.
"""
