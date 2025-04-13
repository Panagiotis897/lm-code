"""
OpenRouter model integration for the CLI tool.
"""

import requests
import json
import logging
import time
from typing import Optional, Dict, List, Any, Union
from rich.console import Console
from rich.panel import Panel
import questionary

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

class OpenRouterTool:
    def __init__(self, function_declarations):
        self.function_declarations = function_declarations

def list_available_models(api_key):
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
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


class OpenRouterModel:
    """Interface for OpenRouter models with function calling support."""

    def __init__(self, api_key: str, console: Console, model_name: str ="qwen/qwen-2.5-coder-32b-instruct:free"):
        """Initialize the OpenRouter model interface."""
        self.api_key = api_key
        self.initial_model_name = model_name
        self.current_model_name = model_name
        self.console = console
        self.base_url = "https://openrouter.ai/api/v1"
        
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
        return list_available_models(self.api_key)

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

    # --- Native Function Calling Agent Loop ---
    def generate(self, prompt: str) -> str | None:
        logging.info(f"Agent Loop - Processing prompt: '{prompt[:100]}...' using model '{self.current_model_name}'")
        original_user_prompt = prompt
        if prompt.startswith('/'):
            command = prompt.split()[0].lower()
            # Handle commands like /compact here eventually
            if command in ['/exit', '/help']:
                logging.info(f"Handled command: {command}")
                return None  # Or return specific help text

        # === Step 1: Mandatory Orientation ===
        orientation_context = ""
        ls_result = None  # Initialize to None
        try:
            logging.info("Performing mandatory orientation (ls).")
            ls_tool = get_tool("ls")
            if ls_tool:
                # Clear args just in case, assuming ls takes none for basic root listing
                ls_result = ls_tool.execute()
                # === START DEBUG LOGGING ===
                log.debug(f"LsTool raw result:\n---\n{ls_result}\n---")
                # === END DEBUG LOGGING ===
                log.info(f"Orientation ls result length: {len(ls_result) if ls_result else 0}")
                self.console.print(f"[dim]Directory context acquired via 'ls'.[/dim]")
                orientation_context = f"Current directory contents (from initial `ls`):\n```\n{ls_result}\n```\n"
            else:
                log.error("CRITICAL: Could not find 'ls' tool for mandatory orientation.")
                # Stop execution if ls tool is missing - fundamental context is unavailable
                return "Error: The essential 'ls' tool is missing. Cannot proceed."

        except Exception as orient_error:
            log.error(f"Error during mandatory orientation (ls): {orient_error}", exc_info=True)
            error_message = f"Error during initial directory scan: {orient_error}"
            orientation_context = f"{error_message}\n"
            self.console.print(f"[bold red]Error getting initial directory listing: {orient_error}[/bold red]")
            # Stop execution if initial ls fails - context is unreliable
            return f"Error: Failed to get initial directory listing. Cannot reliably proceed. Details: {orient_error}"

        # === Step 2: Prepare Initial User Turn ===
        # Combine orientation with the actual user request
        turn_input_prompt = f"{orientation_context}\nUser request: {original_user_prompt}"
        
        # Add this combined input to the PERSISTENT history
        self.chat_history.append({'role': 'user', 'content': turn_input_prompt})
        # === START DEBUG LOGGING ===
        log.debug(f"Prepared turn_input_prompt (sent to LLM):\n---\n{turn_input_prompt}\n---")
        # === END DEBUG LOGGING ===
        self._manage_context_window()  # Truncate *before* sending the first request

        iteration_count = 0
        task_completed = False
        final_summary = None
        last_text_response = "No response generated."  # Fallback text

        try:
            while iteration_count < MAX_AGENT_ITERATIONS:
                iteration_count += 1
                logging.info(f"Agent Loop Iteration {iteration_count}/{MAX_AGENT_ITERATIONS}")
                
                # === Call LLM with History and Tools ===
                llm_response = None
                try:
                    logging.info(f"Sending request to LLM ({self.current_model_name}). History length: {len(self.chat_history)} turns.")
                    # === ADD STATUS FOR LLM CALL ===
                    with self.console.status(f"[yellow]Assistant thinking ({self.current_model_name})...", spinner="dots"):
                        # Prepare the payload for the API request
                        payload = {
                            "model": self.current_model_name,
                            "messages": self.chat_history,
                            "temperature": 0.4,
                            "top_p": 0.95,
                            "max_tokens": 2000
                        }
                        
                        # Add tools if available
                        if self.openrouter_tools:
                            payload["tools"] = self.openrouter_tools
                        
                        # Send the API request
                        response = requests.post(
                            self.base_url,
                            headers=self.headers,
                            json=payload
                        )
                        
                        # Check for successful response
                        if response.status_code != 200:
                            log.error(f"API returned status code {response.status_code}: {response.text}")
                            raise Exception(f"API error: {response.status_code} - {response.text}")
                        
                        # Parse the response
                        llm_response = response.json()
                    # === END STATUS ===
                    
                    # === START DEBUG LOGGING ===
                    log.debug(f"RAW OpenRouter Response Object (Iter {iteration_count}): {llm_response}")
                    # === END DEBUG LOGGING ===
                    
                    # Extract the response
                    if not llm_response.get("choices"):
                        log.error(f"LLM response had no choices. Response: {llm_response}")
                        last_text_response = "(Agent received response with no choices)"
                        task_completed = True
                        final_summary = last_text_response
                        break
                    
                    response_message = llm_response["choices"][0]["message"]
                    
                    # Handle function call responses
                    if "tool_calls" in response_message and response_message["tool_calls"]:
                        # Process the function call
                        function_call = response_message["tool_calls"][0]["function"]
                        tool_name = function_call["name"]
                        tool_args = json.loads(function_call["arguments"])
                        log.info(f"LLM requested Function Call: {tool_name} with args: {tool_args}")
                        
                        # Add the function call to history
                        self.chat_history.append(response_message)
                        self._manage_context_window()
                        
                        # Execute the tool
                        tool_result = ""
                        tool_error = False
                        user_rejected = False  # Flag for user rejection
                        
                        # --- HUMAN IN THE LOOP CONFIRMATION ---
                        if tool_name in ["edit", "create_file"]:
                            file_path = tool_args.get("file_path", "(unknown file)")
                            content = tool_args.get("content")  # Get content, might be None
                            old_string = tool_args.get("old_string")  # Get old_string
                            new_string = tool_args.get("new_string")  # Get new_string
                            
                            panel_content = f"[bold yellow]Proposed change:[/bold yellow]\n[cyan]Tool:[/cyan] {tool_name}\n[cyan]File:[/cyan] {file_path}\n"
                            
                            if content is not None:  # Case 1: Full content provided
                                # Prepare content preview (limit length?)
                                preview_lines = content.splitlines()
                                max_preview_lines = 30  # Limit preview for long content
                                if len(preview_lines) > max_preview_lines:
                                    content_preview = "\n".join(preview_lines[:max_preview_lines]) + f"\n... ({len(preview_lines) - max_preview_lines} more lines)"
                                else:
                                    content_preview = content
                                panel_content += f"\n[bold]Content Preview:[/bold]\n---\n{content_preview}\n---"
                                
                            elif old_string is not None and new_string is not None:  # Case 2: Replacement
                                max_snippet = 50  # Max chars to show for old/new strings
                                old_snippet = old_string[:max_snippet] + ('...' if len(old_string) > max_snippet else '')
                                new_snippet = new_string[:max_snippet] + ('...' if len(new_string) > max_snippet else '')
                                panel_content += f"\n[bold]Action:[/bold] Replace occurrence of:\n---\n{old_snippet}\n---\n[bold]With:[/bold]\n---\n{new_snippet}\n---"
                            else:  # Case 3: Other/Unknown edit args
                                panel_content += "\n[italic](Preview not available for this edit type)"
                            
                            # Use Rich Panel for better presentation
                            self.console.print(Panel(
                                panel_content,  # Use the constructed content
                                title="Confirm File Modification",
                                border_style="red",
                                expand=False
                            ))
                            
                            # Use questionary for confirmation
                            confirmed = questionary.confirm(
                                "Apply this change?",
                                default=False,  # Default to No
                                auto_enter=False  # Require Enter key press
                            ).ask()
                            
                            # Handle case where user might Ctrl+C during prompt
                            if confirmed is None:
                                log.warning("User cancelled confirmation prompt.")
                                tool_result = f"User cancelled confirmation for {tool_name} on {file_path}."
                                user_rejected = True
                            elif not confirmed:  # User explicitly selected No
                                log.warning(f"User rejected proposed action: {tool_name} on {file_path}")
                                tool_result = f"User rejected the proposed {tool_name} operation on {file_path}."
                                user_rejected = True  # Set flag to skip execution
                            else:  # User selected Yes
                                log.info(f"User confirmed action: {tool_name} on {file_path}")
                        # --- END CONFIRMATION ---
                        
                        # Only execute if not rejected by user
                        if not user_rejected:
                            status_msg = f"Executing {tool_name}"
                            if tool_args:
                                status_msg += f" ({', '.join([f'{k}={str(v)[:30]}...' if len(str(v))>30 else f'{k}={v}' for k,v in tool_args.items()])})"
                            
                            with self.console.status(f"[yellow]{status_msg}...", spinner="dots"):
                                try:
                                    tool_instance = get_tool(tool_name)
                                    if tool_instance:
                                        log.debug(f"Executing tool '{tool_name}' with arguments: {tool_args}")
                                        tool_result = tool_instance.execute(**tool_args)
                                        log.info(f"Tool '{tool_name}' executed. Result length: {len(str(tool_result)) if tool_result else 0}")
                                        log.debug(f"Tool '{tool_name}' result: {str(tool_result)[:500]}...")
                                    else:
                                        log.error(f"Tool '{tool_name}' not found.")
                                        tool_result = f"Error: Tool '{tool_name}' is not available."
                                        tool_error = True
                                except Exception as tool_exec_error:
                                    log.error(f"Error executing tool '{tool_name}' with args {tool_args}: {tool_exec_error}", exc_info=True)
                                    tool_result = f"Error executing tool {tool_name}: {str(tool_exec_error)}"
                                    tool_error = True
                                
                                # --- Print Executed/Error INSIDE the status block ---
                                if tool_error:
                                    self.console.print(f"[red] -> Error executing {tool_name}: {str(tool_result)[:100]}...[/red]")
                                else:
                                    self.console.print(f"[dim] -> Executed {tool_name}[/dim]")
                            # --- End Status Block ---
                        
                        # === Check for Task Completion Signal via Tool Call ===
                        if tool_name == "task_complete":
                            log.info("Task completion signaled by 'task_complete' function call.")
                            task_completed = True
                            final_summary = tool_result  # The result of task_complete IS the summary
                            # We break *after* adding the tool response below
                        
                        # Add tool response to history
                        tool_response = {
                            "role": "tool",
                            "tool_call_id": response_message["tool_calls"][0]["id"],
                            "name": tool_name,
                            "content": str(tool_result)
                        }
                        self.chat_history.append(tool_response)
                        self._manage_context_window()
                        
                        if task_completed:
                            break  # Exit loop after task_complete result is in history
                        else:
                            continue  # Continue loop to let LLM react to tool result
                    
                    # Handle text responses
                    elif "content" in response_message and response_message["content"]:
                        llm_text = response_message["content"]
                        log.info(f"LLM returned text (Iter {iteration_count}): {llm_text[:100]}...")
                        
                        # Add text response to history
                        self.chat_history.append(response_message)
                        self._manage_context_window()
                        
                        last_text_response = llm_text.strip()
                        task_completed = True  # Treat text response as completion
                        final_summary = last_text_response  # Use the text as the summary
                        break  # Exit the loop
                    
                    else:
                        # No actionable content
                        log.warning("LLM response contained no actionable content.")
                        last_text_response = "(Agent received response with no actionable content)"
                        task_completed = True  # Treat as completion to avoid loop errors
                        final_summary = last_text_response
                        break  # Exit loop
                
                except Exception as e:
                    # Handle other errors during the API call or response processing
                    log.error(f"Error during Agent Loop: {e}", exc_info=True)
                    # Clean history
                    if self.chat_history[-1]["role"] == "user":
                        self.chat_history.pop()
                    return f"Error during agent processing: {e}"
            
            # === End Agent Loop ===
            
            # === Handle Final Output ===
            if task_completed and final_summary:
                log.info("Agent loop finished. Returning final summary.")
                return final_summary.strip()  # Return the summary from task_complete or final text
            elif iteration_count >= MAX_AGENT_ITERATIONS:
                log.warning(f"Agent loop terminated after reaching max iterations ({MAX_AGENT_ITERATIONS}).")
                # Try to get the last text response
                last_model_response_text = self._find_last_model_text(self.chat_history)
                timeout_message = f"(Task exceeded max iterations ({MAX_AGENT_ITERATIONS}). Last text from model was: {last_model_response_text})"
                return timeout_message.strip()
            else:
                # This case should be less likely now
                log.error("Agent loop exited unexpectedly.")
                last_model_response_text = self._find_last_model_text(self.chat_history)
                return f"(Agent loop finished unexpectedly. Last model text: {last_model_response_text})"
        
        except Exception as e:
            log.error(f"Error during Agent Loop: {str(e)}", exc_info=True)
            return f"An unexpected error occurred during the agent process: {str(e)}"

    # --- Context Management ---
    def _manage_context_window(self):
        """Basic context window management."""
        # Basic management based on turn count
        MAX_HISTORY_TURNS = 20  # Keep ~N pairs of user/assistant turns + initial setup + tool calls/responses
        # OpenRouter format uses 'role' of system, user, assistant, tool
        if len(self.chat_history) > (MAX_HISTORY_TURNS * 2 + 1):  # +1 for system message
            log.warning(f"Chat history length ({len(self.chat_history)}) exceeded threshold. Truncating.")
            # Keep system message (idx 0)
            keep_count = MAX_HISTORY_TURNS * 2  # Keep N rounds (user+assistant or user+tool)
            keep_from_index = len(self.chat_history) - keep_count
            self.chat_history = [self.chat_history[0]] + self.chat_history[keep_from_index:]
            log.info(f"History truncated to {len(self.chat_history)} items.")

    # --- Tool Definition Helper ---
    def _create_tool_definitions(self) -> list[FunctionDeclaration] | None:
        """Dynamically create FunctionDeclarations from AVAILABLE_TOOLS."""
        declarations = []
        for tool_name, tool_instance in AVAILABLE_TOOLS.items():
            if hasattr(tool_instance, 'get_function_declaration'):
                declaration = tool_instance.get_function_declaration()
                if isinstance(declaration, dict):  # Handle unexpected dictionary type
                    if "name" in declaration and "description" in declaration:
                        schema = {
                            "type": "object",
                            "properties": declaration.get("parameters", {}).get("properties", {}),
                            "required": declaration.get("parameters", {}).get("required", [])
                        }
                        declarations.append(FunctionDeclaration(
                            name=declaration["name"],
                            description=declaration["description"],
                            parameters=schema
                        ))
                        log.debug(f"Generated FunctionDeclaration (dict) for tool: {tool_name}")
                    else:
                        log.warning(f"Unexpected dictionary format for tool declaration: {declaration}")
                elif declaration:  # Handle regular objects with attributes
                    schema = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                    # Convert declaration parameters to schema
                    if hasattr(declaration, 'parameters') and declaration.parameters:
                        if hasattr(declaration.parameters, 'properties'):
                            for prop_name, prop_details in declaration.parameters.properties.items():
                                schema["properties"][prop_name] = {
                                    "type": getattr(prop_details, 'type', "string"),
                                    "description": getattr(prop_details, 'description', "")
                                }
                        if hasattr(declaration.parameters, 'required') and declaration.parameters.required:
                            schema["required"] = declaration.parameters.required
    
                    declarations.append(FunctionDeclaration(
                        name=getattr(declaration, 'name', 'unknown'),
                        description=getattr(declaration, 'description', ''),
                        parameters=schema
                    ))
                    log.debug(f"Generated FunctionDeclaration (object) for tool: {tool_name}")
                else:
                    log.warning(f"Tool {tool_name} has 'get_function_declaration' but it returned None.")
            else:
                log.warning(f"Tool {tool_name} does not have a 'get_function_declaration' method. Skipping.")
    
        log.info(f"Created {len(declarations)} function declarations for native tool use.")
        return declarations if declarations else None
    # --- System Prompt Helper ---
    def _create_system_prompt(self) -> str:
        """Creates the system prompt, emphasizing native functions and planning."""
        # Use docstrings from tools if possible for descriptions
        tool_descriptions = []
        if self.function_declarations:
            for func_decl in self.function_declarations:
                # Format the parameters
                params_str = ""
                if hasattr(func_decl, 'parameters') and func_decl.parameters and 'properties' in func_decl.parameters:
                    params_list = []
                    required_args = func_decl.parameters.get('required', [])
                    
                    for prop, details in func_decl.parameters['properties'].items():
                        prop_type = details.get('type', 'UNKNOWN')
                        prop_desc = details.get('description', '')
                        
                        suffix = "" if prop in required_args else "?"  # Indicate optional args
                        
                        params_list.append(f"{prop}: {prop_type}{suffix} # {prop_desc}")
                    
                    params_str = ", ".join(params_list)
                
                desc = func_decl.description if hasattr(func_decl, 'description') else "(No description provided)"
                tool_descriptions.append(f"- `{func_decl.name}({params_str})`: {desc}")
        else:
            tool_descriptions.append(" - (No tools available with function declarations)")

        tool_list_str = "\n".join(tool_descriptions)

        # System prompt based on the original but with OpenRouter specifics
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
   * The `summary` argument MUST accurately reflect the final outcome (success, partial success, error, or what was done).
   * Format the summary using **Markdown** for readability (e.g., use backticks for filenames `like_this.py` or commands `like this`).
   * If code was generated or modified, the summary **MUST** contain the **actual, specific commands** needed to run or test the result (e.g., show `pip install Flask` and `python app.py`).

Important Rules:
* **Use Native Functions:** ONLY interact with tools by making function calls as defined above. Do NOT output tool calls as text.
* **Sequential Calls:** Call functions one at a time. You will get the result back before deciding the next step. Do not try to chain calls in one turn.
* **Initial Context Handling:** When the user asks a general question about the codebase contents, your **first step** should be to use tools like `ls`, `tree` or `find` to gather this information.
* **Accurate Context Reporting:** When asked about directory contents, accurately list or summarize **all** relevant files and directories shown in the `ls` or `tree` output.
* **Handling Explanations:** If the user asks *how* to do something or requests instructions, provide the explanation directly in a text response without calling a function.
* **Proactive Assistance:** When providing instructions that culminate in a specific execution command, offer to run it for the user.
* **Planning First:** For tasks requiring multiple steps, explain your plan briefly in text *before* the first function call.
* **Precise Edits:** When editing files, prefer viewing the relevant section first, then use exact `old_string`/`new_string` arguments if possible.
* **Task Completion Signal:** ALWAYS finish action-oriented tasks by calling `task_complete(summary=...)`.

The user's first message will contain initial directory context and their request."""

    # --- Find Last Text Helper ---
    def _find_last_model_text(self, history: list) -> str:
        """Finds the last text content sent by the assistant in the history."""
        for i in range(len(history) - 1, -1, -1):
            if history[i]['role'] == 'assistant' and 'content' in history[i] and history[i]['content']:
                return history[i]['content'].strip()
        return "(No previous text response found)"
