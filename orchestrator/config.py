import os

os.getenv(os.getenv(""))
from __future__ import annotations

from src.core.config import cfg as _cfg, Config as _Config, load_config as _load_config


class CentralizedConfig(_Config):
    os.getenv(os.getenv(""))

    def __new__(cls, *args, **kwargs):
        return _cfg


def load_config() -> _Config:
    os.getenv(os.getenv(""))
    return _load_config()


cfg = _cfg
__all__ = [os.getenv(os.getenv("")), os.getenv(os.getenv("")), os.getenv(os.getenv(""))]
