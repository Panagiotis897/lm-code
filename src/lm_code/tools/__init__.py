"""
Tools module initialization. Registers all available tools.
"""

import logging
from .base import BaseTool
from .file_tools import ViewTool, EditTool, GrepTool, GlobTool
from .directory_tools import LsTool

log = logging.getLogger(__name__)

# --- Tool Imports ---
try:
    from .system_tools import BashTool

    bash_tool_available = True
except ImportError as e:
    log.warning(f"system_tools.BashTool not found. Disabled. Error: {e}")
    bash_tool_available = False

try:
    from .task_complete_tool import TaskCompleteTool

    task_complete_available = True
except ImportError as e:
    log.warning(f"task_complete_tool.TaskCompleteTool not found. Disabled. Error: {e}")
    task_complete_available = False

try:
    from .directory_tools import CreateDirectoryTool

    create_dir_available = True
except ImportError as e:
    log.warning(f"directory_tools.CreateDirectoryTool not found. Disabled. Error: {e}")
    create_dir_available = False

try:
    from .quality_tools import LinterCheckerTool, FormatterTool

    quality_tools_available = True
except ImportError as e:
    log.warning(f"quality_tools not found or missing classes. Disabled. Error: {e}")
    quality_tools_available = False

try:
    from .tree_tool import TreeTool

    tree_tool_available = True
except ImportError as e:
    log.warning(f"tree_tool.TreeTool not found. Disabled. Error: {e}")
    tree_tool_available = False

try:
    from .summarizer_tool import SummarizeCodeTool

    summarizer_tool_available = True
except ImportError as e:
    log.warning(f"summarizer_tool.SummarizeCodeTool not found. Disabled. Error: {e}")
    summarizer_tool_available = False

# End Tool Imports

# AVAILABLE_TOOLS maps tool names (strings) to the actual tool classes.
# Start with core, guaranteed tools
AVAILABLE_TOOLS = {
    "view": ViewTool,
    "edit": EditTool,
    "ls": LsTool,
    "grep": GrepTool,
    "glob": GlobTool,
}

# Conditionally add tools based on successful imports
if create_dir_available:
    AVAILABLE_TOOLS["create_directory"] = CreateDirectoryTool

if task_complete_available:
    AVAILABLE_TOOLS["task_complete"] = TaskCompleteTool

if tree_tool_available:
    AVAILABLE_TOOLS["tree"] = TreeTool

if bash_tool_available:
    AVAILABLE_TOOLS["bash"] = BashTool

if quality_tools_available:
    AVAILABLE_TOOLS["linter_checker"] = LinterCheckerTool
    AVAILABLE_TOOLS["formatter"] = FormatterTool

if summarizer_tool_available:
    AVAILABLE_TOOLS["summarize_code"] = SummarizeCodeTool


def get_tool(name: str) -> BaseTool | None:
    """
    Retrieves an *instance* of the tool class based on its name.
    """
    tool_class = AVAILABLE_TOOLS.get(name)
    if tool_class:
        try:
            return tool_class()
        except Exception as e:
            log.error(f"Error instantiating tool '{name}': {e}", exc_info=True)
            return None
    else:
        log.warning(f"Tool '{name}' not found in AVAILABLE_TOOLS.")
        return None


log.info(f"Tools initialized. Available: {list(AVAILABLE_TOOLS.keys())}")
