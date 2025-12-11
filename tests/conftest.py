"""Test bootstrap hooks.

Stubs optional heavy dependencies to avoid noisy native warnings in fast checks.
"""

import sys
import types
import warnings


# Stub faiss to prevent SWIG deprecation warnings in environments without the
# native library; tests that need real FAISS should override this.
if "faiss" not in sys.modules:
    dummy = types.ModuleType("faiss")

    class _IndexFlatIP:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("faiss not available in test stub")

    dummy.IndexFlatIP = _IndexFlatIP
    sys.modules["faiss"] = dummy

# Suppress upstream SWIG deprecation noise from FAISS bindings
warnings.filterwarnings("ignore", message="builtin type SwigPy.*", category=DeprecationWarning)
