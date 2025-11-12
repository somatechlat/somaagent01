"""Gateway service package for SomaAgent 01.

The module re-exports the :pymod:`services.gateway.main` module as ``main`` so
that test code can import ``services.gateway`` and access ``gateway.main``
directly (e.g., ``from services import gateway as gw_pkg``). This mirrors the
prior import pattern used throughout the test suite.
"""

# Export the main FastAPI module under the name ``main`` for backward
# compatibility with existing tests that expect ``services.gateway.main`` to be
# an attribute of the package.
from . import main as main  # noqa: F401
