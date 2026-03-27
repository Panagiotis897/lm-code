"""
Tool for summarizing code files.
"""

import logging
import os
from .base import BaseTool

log = logging.getLogger(__name__)

# Define thresholds for summarization vs. full view
MAX_LINES_FOR_FULL_CONTENT = 1000  # View files smaller than this directly
MAX_CHARS_FOR_FULL_CONTENT = 50 * 1024  # 50 KB


class SummarizeCodeTool(BaseTool):
    """
    Tool to summarize a code file, especially useful for large files.
    Returns full content for small files.
    """

    name = "summarize_code"
    description = "Provides a summary of a code file's purpose, key functions/classes, and structure. Use for large files or when only an overview is needed."

    def execute(
        self,
        file_path: str | None = None,
        directory_path: str | None = None,
        query: str | None = None,
        glob_pattern: str | None = None,
    ) -> str:
        """
        Summarizes code based on path, directory, or query.

        Args:
            file_path: Path to the file to summarize.
            directory_path: Path to directory (not implemented).
            query: Query for search (not implemented).
            glob_pattern: Glob pattern (not implemented).

        Returns:
            File content for small files, or a basic summary for large files.
        """
        log.debug(f"[SummarizeCodeTool] Current working directory: {os.getcwd()}")
        log.info(
            f"SummarizeCodeTool called with file='{file_path}', dir='{directory_path}', query='{query}', glob='{glob_pattern}'"
        )

        if not file_path:
            return "Error: No file path provided to summarize."

        try:
            # Basic path safety
            if ".." in file_path.split(os.path.sep):
                log.warning(f"Attempted access to parent directory: {file_path}")
                return f"Error: Invalid file path '{file_path}'."

            target_path = os.path.abspath(os.path.expanduser(file_path))
            log.info(f"Summarize/View file: {target_path}")

            if not os.path.exists(target_path):
                return f"Error: File not found: {file_path}"
            if not os.path.isfile(target_path):
                return f"Error: Path is not a file: {file_path}"

            # Check file size/lines
            file_size = os.path.getsize(target_path)
            line_count = 0
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    for _ in f:
                        line_count += 1
            except Exception:
                pass  # Ignore line count errors, rely on size

            log.debug(f"File '{file_path}': Size={file_size} bytes, Lines={line_count}")

            # Return full content if file is small
            if (
                line_count < MAX_LINES_FOR_FULL_CONTENT
                and file_size < MAX_CHARS_FOR_FULL_CONTENT
            ):
                log.info(f"File '{file_path}' is small, returning full content.")
                try:
                    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    return f"--- Full Content of {file_path} ---\n{content}"
                except Exception as read_err:
                    log.error(
                        f"Error reading small file '{target_path}': {read_err}",
                        exc_info=True,
                    )
                    return f"Error reading file: {read_err}"

            # Generate basic summary for large files
            else:
                log.info(f"File '{file_path}' is large, generating basic summary...")
                try:
                    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                        content_to_summarize = f.read()

                    if not content_to_summarize.strip():
                        return f"--- Summary of {file_path} ---\n(File is empty)"

                    # Basic summary without LLM
                    summary = f"--- Summary of {file_path} ---\n"
                    summary += f"File size: {file_size} bytes, {line_count} lines\n"

                    # Extract imports
                    imports = []
                    for line in content_to_summarize.split("\n"):
                        line = line.strip()
                        if line.startswith("import ") or line.startswith("from "):
                            imports.append(line)

                    if imports:
                        summary += f"\nImports:\n"
                        for imp in imports[:20]:  # Limit to first 20 imports
                            summary += f"  - {imp}\n"
                        if len(imports) > 20:
                            summary += f"  ... and {len(imports) - 20} more imports\n"

                    # Extract class definitions
                    classes = []
                    for line in content_to_summarize.split("\n"):
                        line = line.strip()
                        if line.startswith("class "):
                            classes.append(line)

                    if classes:
                        summary += f"\nClasses:\n"
                        for cls in classes[:10]:
                            summary += f"  - {cls}\n"

                    # Extract function definitions
                    functions = []
                    for line in content_to_summarize.split("\n"):
                        line = line.strip()
                        if line.startswith("def "):
                            functions.append(line)

                    if functions:
                        summary += f"\nFunctions:\n"
                        for func in functions[:20]:
                            summary += f"  - {func}\n"
                        if len(functions) > 20:
                            summary += (
                                f"  ... and {len(functions) - 20} more functions\n"
                            )

                    return summary

                except Exception as summary_err:
                    log.error(
                        f"Error generating summary for '{target_path}': {summary_err}",
                        exc_info=True,
                    )
                    return f"Error generating summary: {summary_err}"

        except Exception as e:
            log.error(
                f"Error in SummarizeCodeTool for '{file_path}': {e}", exc_info=True
            )
            return f"Error processing file for summary/view: {str(e)}"
