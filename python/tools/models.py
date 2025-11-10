from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(slots=True)
class ToolParameter:
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any | None = None


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    category: Optional[str] = None

    def to_openapi_function(self) -> dict[str, Any]:
        props: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            props[p.name] = {"type": p.type}
            if p.description:
                props[p.name]["description"] = p.description
            if p.default is not None:
                props[p.name]["default"] = p.default
            if p.required:
                required.append(p.name)
        schema: dict[str, Any] = {
            "type": "object",
            "properties": props,
        }
        if required:
            schema["required"] = required
        return {
            "name": self.name,
            "description": self.description,
            "parameters": schema,
        }
