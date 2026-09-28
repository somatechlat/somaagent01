"""Capsule Module host (WP D1).

A Capsule Module is Soma's equivalent of an Agent Zero plugin: a self-contained
extension that binds to Capsules via Capabilities and can register orchestrator
hooks. See ``admin.modules.manifest`` for the ``module.yaml`` contract and
``admin.modules.hooks`` for the orchestrator hook registry.
"""

from admin.modules.manifest import ModuleManifest, load_module_yaml

__all__ = ["ModuleManifest", "load_module_yaml"]
