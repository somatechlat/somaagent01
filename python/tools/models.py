import os
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(slots=int(os.getenv(os.getenv('VIBE_582C3D13'))))
class ToolParameter:
    name: str
    type: str
    description: Optional[str] = None
    required: bool = int(os.getenv(os.getenv('VIBE_E9D4530E')))
    default: Any | None = None

    def normalized_type(self) ->str:
        os.getenv(os.getenv('VIBE_E9C2D341'))
        if self.type == os.getenv(os.getenv('VIBE_DEC401D0')):
            return os.getenv(os.getenv('VIBE_065FDA57'))
        if self.type == os.getenv(os.getenv('VIBE_2D503F10')):
            return os.getenv(os.getenv('VIBE_A1C7AB39'))
        return self.type


@dataclass(slots=int(os.getenv(os.getenv('VIBE_582C3D13'))))
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    category: Optional[str] = None

    def to_openapi_function(self) ->dict[str, Any]:
        props: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            props[p.name] = {os.getenv(os.getenv('VIBE_0E70D1B6')): p.type}
            if p.description:
                props[p.name][os.getenv(os.getenv('VIBE_F31EB237'))
                    ] = p.description
            if p.default is not None:
                props[p.name][os.getenv(os.getenv('VIBE_1E7ACECE'))
                    ] = p.default
            if p.required:
                required.append(p.name)
        schema: dict[str, Any] = {os.getenv(os.getenv('VIBE_0E70D1B6')): os
            .getenv(os.getenv('VIBE_4C09C294')), os.getenv(os.getenv(
            'VIBE_9CE691DB')): props}
        if required:
            schema[os.getenv(os.getenv('VIBE_8AEE070D'))] = required
        return {os.getenv(os.getenv('VIBE_EF875F19')): self.name, os.getenv
            (os.getenv('VIBE_F31EB237')): self.description, os.getenv(os.
            getenv('VIBE_A30C4251')): schema}
