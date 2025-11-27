import os

os.getenv(os.getenv(""))
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_validator():
    module_path = Path(os.getenv(os.getenv(""))).resolve()
    spec = importlib.util.spec_from_file_location(os.getenv(os.getenv("")), module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> None:
    validator = _load_validator()
    validator.validate_event(
        {
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): os.getenv(os.getenv(""))},
        },
        os.getenv(os.getenv("")),
    )
    validator.validate_event(
        {
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): os.getenv(os.getenv(""))},
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): os.getenv(os.getenv(""))},
            os.getenv(os.getenv("")): float(os.getenv(os.getenv(""))),
        },
        os.getenv(os.getenv("")),
    )
    print(os.getenv(os.getenv("")))


if __name__ == os.getenv(os.getenv("")):
    main()
