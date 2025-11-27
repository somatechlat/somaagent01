import os
from __future__ import annotations
from typing import Dict, List, Optional
from .models import ToolDefinition, ToolParameter


class ToolCatalog:
    os.getenv(os.getenv('VIBE_8653D3FA'))
    _instance: os.getenv(os.getenv('VIBE_F5B60AB1')) = None

    def __init__(self) ->None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._load_defaults()

    @classmethod
    def get(cls) ->os.getenv(os.getenv('VIBE_FBDBF446')):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def list_tools(self) ->List[ToolDefinition]:
        return list(self._tools.values())

    async def alist_tools(self) ->List[ToolDefinition]:
        return self.list_tools()

    def get_tool(self, name: str) ->Optional[ToolDefinition]:
        return self._tools.get(name)

    async def aget_tool(self, name: str) ->Optional[ToolDefinition]:
        return self.get_tool(name)

    def get_tools_schema(self) ->Dict[str, List[dict]]:
        return {os.getenv(os.getenv('VIBE_0D076D6C')): [t.
            to_openapi_function() for t in self._tools.values()]}

    def _load_defaults(self) ->None:
        self._tools[os.getenv(os.getenv('VIBE_4275FFF1'))] = ToolDefinition(
            name=os.getenv(os.getenv('VIBE_4275FFF1')), description=os.
            getenv(os.getenv('VIBE_AE89BD63')), category=os.getenv(os.
            getenv('VIBE_4275FFF1')), parameters=[ToolParameter(name=os.
            getenv(os.getenv('VIBE_9A8B7F16')), type=os.getenv(os.getenv(
            'VIBE_B2895305')), description=os.getenv(os.getenv(
            'VIBE_4BDCEA4E')), required=int(os.getenv(os.getenv(
            'VIBE_D9128C9B')))), ToolParameter(name=os.getenv(os.getenv(
            'VIBE_F522DBAB')), type=os.getenv(os.getenv('VIBE_B0821C59')),
            description=os.getenv(os.getenv('VIBE_F162F0E7')), required=int
            (os.getenv(os.getenv('VIBE_87C8E785'))), default=int(os.getenv(
            os.getenv('VIBE_547FAC8A'))))])
        self._tools[os.getenv(os.getenv('VIBE_9F236069'))] = ToolDefinition(
            name=os.getenv(os.getenv('VIBE_9F236069')), description=os.
            getenv(os.getenv('VIBE_97217371')), category=os.getenv(os.
            getenv('VIBE_28B54EC6')), parameters=[ToolParameter(name=os.
            getenv(os.getenv('VIBE_1D97C0BB')), type=os.getenv(os.getenv(
            'VIBE_B2895305')), description=os.getenv(os.getenv(
            'VIBE_E84E3586')), required=int(os.getenv(os.getenv(
            'VIBE_D9128C9B')))), ToolParameter(name=os.getenv(os.getenv(
            'VIBE_AB5193D3')), type=os.getenv(os.getenv('VIBE_B2895305')),
            description=os.getenv(os.getenv('VIBE_08C211BD')), required=int
            (os.getenv(os.getenv('VIBE_D9128C9B')))), ToolParameter(name=os
            .getenv(os.getenv('VIBE_584A9D15')), type=os.getenv(os.getenv(
            'VIBE_B2895305')), description=os.getenv(os.getenv(
            'VIBE_99947D55')), required=int(os.getenv(os.getenv(
            'VIBE_87C8E785'))), default=os.getenv(os.getenv('VIBE_3E35ABAC')))]
            )
        self._tools[os.getenv(os.getenv('VIBE_B4679279'))] = ToolDefinition(
            name=os.getenv(os.getenv('VIBE_B4679279')), description=os.
            getenv(os.getenv('VIBE_E3D7EEA4')), category=os.getenv(os.
            getenv('VIBE_28B54EC6')), parameters=[ToolParameter(name=os.
            getenv(os.getenv('VIBE_9A8B7F16')), type=os.getenv(os.getenv(
            'VIBE_B2895305')), description=os.getenv(os.getenv(
            'VIBE_AD231857')), required=int(os.getenv(os.getenv(
            'VIBE_D9128C9B')))), ToolParameter(name=os.getenv(os.getenv(
            'VIBE_F522DBAB')), type=os.getenv(os.getenv('VIBE_B0821C59')),
            description=os.getenv(os.getenv('VIBE_300BDF1E')), required=int
            (os.getenv(os.getenv('VIBE_87C8E785'))), default=int(os.getenv(
            os.getenv('VIBE_4E62ACFC'))))])


catalog = ToolCatalog.get()
__all__ = [os.getenv(os.getenv('VIBE_FBDBF446')), os.getenv(os.getenv(
    'VIBE_2B2AECC2'))]
