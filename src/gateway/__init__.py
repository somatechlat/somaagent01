"""Gateway package initialisation.

The package contains FastAPI router modules that are mounted by the orchestrator
gateway service.  It is intentionally lightweight – the presence of this file
simply makes ``src.gateway`` a proper Python package so that imports such as
``from src.gateway.routers import chat`` succeed.
"""
