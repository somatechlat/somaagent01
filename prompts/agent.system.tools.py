"""Module agent.system.tools."""

import os
from typing import Any

from admin.core.helpers import files
from admin.core.helpers.files import VariablesPlugin
from admin.core.helpers.print_style import PrintStyle


class CallSubordinate(VariablesPlugin):
    """Callsubordinate class implementation."""

    def get_variables(self, file: str, backup_dirs: list[str] | None = None) -> dict[str, Any]:

        # collect all prompt folders in order of their priority
        """Retrieve variables.

            Args:
                file: The file.
                backup_dirs: The backup_dirs.
            """

        folder = files.get_abs_path(os.path.dirname(file))
        folders = [folder]
        if backup_dirs:
            for backup_dir in backup_dirs:
                folders.append(files.get_abs_path(backup_dir))

        # collect all tool instruction files
        prompt_files = files.get_unique_filenames_in_dirs(folders, "agent.system.tool.*.md")

        # load tool instructions
        tools = []
        for prompt_file in prompt_files:
            try:
                tool = files.read_prompt_file(prompt_file)
                tools.append(tool)
            except Exception as e:
                PrintStyle().error(f"Error loading tool '{prompt_file}': {e}")

        return {"tools": "\n\n".join(tools)}