"""Site customisation for the Agent‑Zero repository.

Python automatically imports a module named ``sitecustomize`` (if it can be
found on ``sys.path``) after the standard ``site`` module is initialised.  By
adding this file at the repository root we guarantee that it is discovered when
the test runner starts, before any test modules are imported.

The purpose is to make the top‑level ``python`` package (which contains all
helpers, models, and SDK code) reliably importable, even in environments where
another distribution provides a top‑level module named ``python`` that could mask
our local package.  We prepend the repository root to ``sys.path`` so that the
local ``python`` package takes precedence.
"""

import os
import sys
import warnings

# Silence upstream DeprecationWarnings from native bindings (e.g., SWIG/faiss) in test runs.
warnings.simplefilter("ignore", DeprecationWarning)

# Compatibility shim for tests that reference ``pytest.Request`` (which does not
# exist in the public pytest API). The test suite only uses the type for type
# hints, so we alias it to ``pytest.FixtureRequest`` which provides the same
# runtime behaviour.
# Ensure ``pytest.Request`` exists for type‑checking in the test suite.
# Importing pytest here forces its module to load before any test files are
# evaluated, allowing us to safely add the missing attribute.
import pytest

# Provide a minimal ``Request`` type for the test suite. If the internal
# ``FixtureRequest`` class is importable we use it; otherwise we fall back to a
# simple placeholder.
try:
    from _pytest.fixtures import FixtureRequest  # type: ignore

    _req_type = FixtureRequest
except Exception:

    class _PlaceholderRequest:  # pragma: no cover
        pass

    _req_type = _PlaceholderRequest

if not hasattr(pytest, "Request"):
    pytest.Request = _req_type  # type: ignore[attr-defined]

# Resolve the absolute path of the repository root (the directory containing this file).
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))

# Ensure the repo root is the first entry on ``sys.path`` – this gives our local
# ``python`` package priority over any similarly‑named installed package.
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Additionally, make the ``python`` directory itself importable as a top‑level
# package.  This is a safeguard for environments that manipulate ``PYTHONPATH``
# before the interpreter starts.
PYTHON_PKG = os.path.join(REPO_ROOT, "python")
if PYTHON_PKG not in sys.path:
    sys.path.append(PYTHON_PKG)
