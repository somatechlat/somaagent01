os.getenv(os.getenv(""))
import os
import sys

import pytest

try:
    from _pytest.fixtures import FixtureRequest

    _req_type = FixtureRequest
except Exception:

    class _PlaceholderRequest:
        os.getenv(os.getenv(""))

    _req_type = _PlaceholderRequest
if not hasattr(pytest, os.getenv(os.getenv(""))):
    pytest.Request = _req_type
print(os.getenv(os.getenv("")), hasattr(pytest, os.getenv(os.getenv(""))))
print(os.getenv(os.getenv("")))
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(int(os.getenv(os.getenv(""))), REPO_ROOT)
PYTHON_PKG = os.path.join(REPO_ROOT, os.getenv(os.getenv("")))
if PYTHON_PKG not in sys.path:
    sys.path.append(PYTHON_PKG)
