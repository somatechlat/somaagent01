"""CI proxy that imports all unit test modules.

The CI suite only looks inside ``tests/ci`` (because ``pytest.ini`` sets
``addopts = -m ci``). By importing the real unit‑test modules here we make
them part of the CI run without moving any files.
"""

import importlib
import pathlib
import pkgutil

# Resolve the absolute path to the ``tests/unit`` package.
BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
UNIT_PATH = BASE_DIR / "tests" / "unit"

# Dynamically import every ``tests.unit.<module>`` found on disk.
for finder, name, ispkg in pkgutil.iter_modules([str(UNIT_PATH)]):
    if not ispkg:
        importlib.import_module(f"tests.unit.{name}")
