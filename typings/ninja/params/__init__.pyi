"""Type stubs for django-ninja params to fix Pyright compatibility.

Django Ninja uses a TYPE_CHECKING trick where Query/Path/etc are
Annotated[T, ...] at type-check time but callable ParamShortcut at runtime.
Pyright reads the TYPE_CHECKING block, causing "Annotated is not callable".
These stubs override the type-checking view to match the runtime behavior.
"""

from typing import Any, Callable, TypeVar

T = TypeVar("T")

class ParamShortcut:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    def __getitem__(self, args: Any) -> Any: ...

Body: ParamShortcut
Cookie: ParamShortcut
File: ParamShortcut
Form: ParamShortcut
Header: ParamShortcut
Path: ParamShortcut
Query: ParamShortcut
BodyEx: ParamShortcut
CookieEx: ParamShortcut
FileEx: ParamShortcut
FormEx: ParamShortcut
HeaderEx: ParamShortcut
PathEx: ParamShortcut
QueryEx: ParamShortcut

def P(
    *,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    regex: str | None = None,
    example: Any = None,
    examples: dict[str, Any] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    **extra: Any,
) -> dict[str, Any]: ...
