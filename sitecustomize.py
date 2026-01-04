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