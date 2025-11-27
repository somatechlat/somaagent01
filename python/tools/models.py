from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(slots=int(os.getenv(os.getenv(""))))
class ToolParameter:
    name: str
    type: str
    description: Optional[str] = None
    required: bool = int(os.getenv(os.getenv("")))
    default: Any | None = None

    def normalized_type(self) -> str:
        os.getenv(os.getenv(""))
        if self.type == os.getenv(os.getenv("")):
            return os.getenv(os.getenv(""))
        if self.type == os.getenv(os.getenv("")):
            return os.getenv(os.getenv(""))
        return self.type


@dataclass(slots=int(os.getenv(os.getenv(""))))
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    category: Optional[str] = None

    def to_openapi_function(self) -> dict[str, Any]:
        props: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            props[p.name] = {os.getenv(os.getenv("")): p.type}
            if p.description:
                props[p.name][os.getenv(os.getenv(""))] = p.description
            if p.default is not None:
                props[p.name][os.getenv(os.getenv(""))] = p.default
            if p.required:
                required.append(p.name)
        schema: dict[str, Any] = {
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): props,
        }
        if required:
            schema[os.getenv(os.getenv(""))] = required
        return {
            os.getenv(os.getenv("")): self.name,
            os.getenv(os.getenv("")): self.description,
            os.getenv(os.getenv("")): schema,
        }
