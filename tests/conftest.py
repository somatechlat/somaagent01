"""Test bootstrap hooks.

Stubs optional heavy dependencies to avoid noisy native warnings in fast checks.
"""

import sys
import types
import warnings

# FAISS REMOVED: Use SomaBrain for all memory operations.
# Legacy FAISS stub removed. If tests fail, they must be updated to use SomaBrain.

# Suppress upstream SWIG deprecation noise
warnings.filterwarnings("ignore", message="builtin type SwigPy.*", category=DeprecationWarning)
