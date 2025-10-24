"""Deprecated memory service package.

This package has been removed in favor of SomaBrain HTTP APIs.
Any import should fail fast to prevent accidental usage.
"""

raise ImportError(
	"services.memory_service is removed; use python.integrations.soma_client.SomaClient"
)
