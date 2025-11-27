import os
from typing import Any
from python.helpers import files
from python.helpers.files import VariablesPlugin
from python.helpers.print_style import PrintStyle


class CallSubordinate(VariablesPlugin):

    def get_variables(self, file: str, backup_dirs: (list[str] | None)=None
        ) ->dict[str, Any]:
        profiles = []
        agent_subdirs = files.get_subdirectories(os.getenv(os.getenv(
            'VIBE_F53E0449')), exclude=[os.getenv(os.getenv('VIBE_51EBB773'))])
        for agent_subdir in agent_subdirs:
            try:
                context = files.read_prompt_file(os.getenv(os.getenv(
                    'VIBE_7DA38233')), [files.get_abs_path(os.getenv(os.
                    getenv('VIBE_F53E0449')), agent_subdir)])
                profiles.append({os.getenv(os.getenv('VIBE_EFD8A5ED')):
                    agent_subdir, os.getenv(os.getenv('VIBE_29C49EC3')):
                    context})
            except Exception as e:
                PrintStyle().error(
                    f"Error loading agent profile '{agent_subdir}': {e}")
        if not profiles:
            profiles = [{os.getenv(os.getenv('VIBE_EFD8A5ED')): os.getenv(
                os.getenv('VIBE_B39E9467')), os.getenv(os.getenv(
                'VIBE_29C49EC3')): os.getenv(os.getenv('VIBE_C7DCD036'))}]
        return {os.getenv(os.getenv('VIBE_AFF92C1E')): profiles}
