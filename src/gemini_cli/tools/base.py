"""
Base tool implementation and interfaces.
"""

import shlex
import inspect
from abc import ABC, abstractmethod
import logging

log = logging.getLogger(__name__)

class BaseTool(ABC):
    """Base class for all tools."""
    
    name = None
    description = "Base tool"
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the tool with the given arguments."""
        pass

    @classmethod
    def get_function_declaration(cls):
        """Generates a function declaration based on the execute method's signature."""
        if not cls.name or not cls.description:
            log.warning(f"Tool {cls.__name__} is missing name or description. Cannot generate declaration.")
            return None

        try:
            exec_sig = inspect.signature(cls.execute)
            parameters = {}
            required = []

            for param_name, param in exec_sig.parameters.items():
                if param_name == 'self':
                    continue 
                
                param_type = "string"
                if param.annotation == str: param_type = "string"
                elif param.annotation == int: param_type = "integer"
                elif param.annotation == float: param_type = "number"
                elif param.annotation == bool: param_type = "boolean"
                elif param.annotation == list: param_type = "array"
                elif param.annotation == dict: param_type = "object"

                param_description = f"Parameter {param_name}"

                parameters[param_name] = {
                    "type": param_type,
                    "description": param_description
                }

                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            if not parameters:
                schema = None
            else:
                schema = {
                    "type": "object",
                    "properties": parameters,
                    "required": required if required else None 
                }
                if schema["required"] is None:
                    del schema["required"]

            return {
                "name": cls.name,
                "description": cls.description,
                "parameters": schema
            }

        except Exception as e:
            log.error(f"Error generating function declaration for tool '{cls.name}': {e}", exc_info=True)
            return None
