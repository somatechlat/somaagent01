from __future__ import annotations

import threading
import time
from typing import Callable, Optional

_FLAG_CACHE: dict[tuple[str, str], tuple[bool, float]] = {}
_LOCK = threading.Lock()

class TenantFlagCache:
    def __init__(self, fetcher: Callable[[str, str], bool], ttl: float = 2.0) -> None:
        self.fetcher = fetcher
        self.ttl = max(0.1, ttl)

    def get(self, tenant: str, flag: str) -> Optional[bool]:
        key = (tenant or "default", flag)
        now = time.time()
        with _LOCK:
            entry = _FLAG_CACHE.get(key)
            if entry and entry[1] > now:
                return entry[0]
        try:
            value = bool(self.fetcher(tenant or "default", flag))
        except Exception:
            return None
        with _LOCK:
            _FLAG_CACHE[key] = (value, now + self.ttl)
        return value

_CACHE_INSTANCE: TenantFlagCache | None = None


def init_tenant_flag_cache(fetcher: Callable[[str, str], bool], ttl: float) -> TenantFlagCache:
    global _CACHE_INSTANCE
    _CACHE_INSTANCE = TenantFlagCache(fetcher=fetcher, ttl=ttl)
    return _CACHE_INSTANCE


def get_tenant_flag(tenant: str | None, flag: str) -> Optional[bool]:
    if _CACHE_INSTANCE is None:
        return None
    return _CACHE_INSTANCE.get(tenant or "default", flag)


def cache_instance() -> TenantFlagCache | None:
    return _CACHE_INSTANCE


def set_flag_fetcher(fetcher: Callable[[str, str], bool]) -> None:
    if _CACHE_INSTANCE is None:
        return
    _CACHE_INSTANCE.fetcher = fetcher
