"""
Directory tools for interacting with the file system.
"""

import os
import platform
import subprocess
import logging

log = logging.getLogger(__name__)

class LsTool:
    """Tool for listing directory contents."""

    def execute(self, path: str = ".") -> str:
        """List the contents of a directory."""
        try:
            # Check the operating system and use the appropriate command
            if platform.system() == "Windows":
                # Use dir command on Windows
                result = subprocess.run(["cmd", "/c", "dir", path], capture_output=True, text=True, check=True)
            else:
                # Use ls command on Unix-based systems
                result = subprocess.run(["ls", path], capture_output=True, text=True, check=True)
            return result.stdout
        except FileNotFoundError:
            log.error("'ls' or 'dir' command not found. Ensure it is installed or in PATH.")
            raise
        except subprocess.CalledProcessError as e:
            log.error(f"Error executing directory listing: {e}")
            raise
