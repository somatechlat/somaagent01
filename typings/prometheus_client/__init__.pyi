"""Type stubs for prometheus_client to fix Pyright compatibility."""

from typing import Any, Callable, Optional, Sequence, TypeVar

T = TypeVar("T")

class _Timer:
    def __enter__(self) -> "_Timer": ...
    def __exit__(self, *args: Any) -> None: ...

class Collector:
    def labels(self, *args: Any, **kwargs: Any) -> "Collector": ...
    def inc(self, amount: float = 1) -> None: ...
    def dec(self, amount: float = 1) -> None: ...
    def set(self, value: float) -> None: ...
    def observe(self, amount: float) -> None: ...
    def time(self) -> "_Timer": ...
    def remove(self, *labelvalues: Any, **labelkwargs: Any) -> None: ...
    def clear(self) -> None: ...

class Counter(Collector):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Any = ...,
        _labelvalues: Any = None,
    ) -> None: ...

class Gauge(Collector):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Any = ...,
        _labelvalues: Any = None,
    ) -> None: ...

class Histogram(Collector):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        buckets: Sequence[float] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Any = ...,
        _labelvalues: Any = None,
    ) -> None: ...

class Summary(Collector):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Any = ...,
        _labelvalues: Any = None,
    ) -> None: ...

class Info(Collector):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Any = ...,
        _labelvalues: Any = None,
    ) -> None: ...
    def info(self, data: dict[str, str]) -> None: ...

class Enum(Collector):
    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
        states: Sequence[str] = (),
        namespace: str = "",
        subsystem: str = "",
        unit: str = "",
        registry: Any = ...,
        _labelvalues: Any = None,
    ) -> None: ...

class CollectorRegistry:
    def register(self, collector: Any) -> None: ...
    def unregister(self, collector: Any) -> None: ...
    def _names_to_collectors(self) -> dict[str, Any]: ...

REGISTRY: CollectorRegistry

def generate_latest(registry: Any = ...) -> bytes: ...
def start_http_server(port: int = 8000, addr: str = "") -> None: ...
def make_wsgi_app(registry: Any = ...) -> Callable[..., Any]: ...
