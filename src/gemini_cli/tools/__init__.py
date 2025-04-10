"""
Tools module initialization. Registers all available tools.
"""

import logging
from .base import BaseTool
from .file_tools import ViewTool, EditTool, GrepTool, GlobTool
from .directory_tools import LsTool

# --- Tool Imports ---
try:
    from .system_tools import BashTool
    bash_tool_available = True
except ImportError:
    logging.warning("system_tools.BashTool not found. Disabled.")
    bash_tool_available = False

try:
    from .task_complete_tool import TaskCompleteTool
    task_complete_available = True
except ImportError:
    logging.warning("task_complete_tool.TaskCompleteTool not found. Disabled.")
    task_complete_available = False

try:
    from .directory_tools import CreateDirectoryTool
    create_dir_available = True
except ImportError:
    logging.warning("directory_tools.CreateDirectoryTool not found. Disabled.")
    create_dir_available = False

try:
    from .quality_tools import LinterCheckerTool, FormatterTool
    quality_tools_available = True
except ImportError:
    logging.warning("quality_tools not found or missing classes. Disabled.")
    quality_tools_available = False

# End Tool Imports

from .tree_tool import TreeTool

# AVAILABLE_TOOLS maps tool names (strings) to the actual tool classes.
# Start with core, guaranteed tools
AVAILABLE_TOOLS = {
    "view": ViewTool,
    "edit": EditTool,
    "ls": LsTool,
    "grep": GrepTool,
    "glob": GlobTool,
    "create_directory": CreateDirectoryTool,
    "task_complete": TaskCompleteTool,
    "tree": TreeTool,
}

# Conditionally add tools based on successful imports
if bash_tool_available:
    AVAILABLE_TOOLS["bash"] = BashTool
if quality_tools_available:
    AVAILABLE_TOOLS["linter_checker"] = LinterCheckerTool
    AVAILABLE_TOOLS["formatter"] = FormatterTool


def get_tool(name: str) -> BaseTool | None:
    """
    Retrieves an *instance* of the tool class based on its name.
    """
    tool_class = AVAILABLE_TOOLS.get(name)
    if tool_class:
        try:
            return tool_class()
        except Exception as e:
            logging.error(f"Error instantiating tool '{name}': {e}", exc_info=True)
            return None
    else:
        logging.warning(f"Tool '{name}' not found in AVAILABLE_TOOLS.")
        return None


logging.info(f"Tools initialized. Available: {list(AVAILABLE_TOOLS.keys())}")
