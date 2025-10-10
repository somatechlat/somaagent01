"""Provider SDK package.

This package provides a minimal SDK that can be extended by downstream
projects to discover and interact with external providers (LLM, vector
stores, etc.).  At the moment it only contains a small ``discover`` helper
function that reads a configuration file and returns a dictionary of
available providers.

The implementation is deliberately lightweight – it does not depend on any
external libraries so that it can be imported safely during early start‑up
of the Soma stack.
"""

from .discover import discover_providers

__all__ = ["discover_providers"]
