"""Model profile storage for SomaAgent 01."""

from __future__ import annotations

import logging

"""
Legacy model profile store removed – centralized settings will drive LLM config.
"""

# This module intentionally left minimal to satisfy imports; all functionality removed.
LOGGER = logging.getLogger(__name__)

class ModelProfile:
    pass

class ModelProfileStore:
    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError("Model profiles have been removed; use centralized settings instead.")
