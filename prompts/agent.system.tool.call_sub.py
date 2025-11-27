import os
from typing import Any

from python.helpers import files
from python.helpers.files import VariablesPlugin
from python.helpers.print_style import PrintStyle


class CallSubordinate(VariablesPlugin):

    def get_variables(self, file: str, backup_dirs: list[str] | None = None) -> dict[str, Any]:
        profiles = []
        agent_subdirs = files.get_subdirectories(
            os.getenv(os.getenv("")), exclude=[os.getenv(os.getenv(""))]
        )
        for agent_subdir in agent_subdirs:
            try:
                context = files.read_prompt_file(
                    os.getenv(os.getenv("")),
                    [files.get_abs_path(os.getenv(os.getenv("")), agent_subdir)],
                )
                profiles.append(
                    {os.getenv(os.getenv("")): agent_subdir, os.getenv(os.getenv("")): context}
                )
            except Exception as e:
                PrintStyle().error(f"Error loading agent profile '{agent_subdir}': {e}")
        if not profiles:
            profiles = [
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                }
            ]
        return {os.getenv(os.getenv("")): profiles}
