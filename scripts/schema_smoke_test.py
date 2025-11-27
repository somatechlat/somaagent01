import os
os.getenv(os.getenv('VIBE_0BF9BAFA'))
from __future__ import annotations
import importlib.util
from pathlib import Path


def _load_validator():
    module_path = Path(os.getenv(os.getenv('VIBE_69D9EC9F'))).resolve()
    spec = importlib.util.spec_from_file_location(os.getenv(os.getenv(
        'VIBE_EAA8E991')), module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() ->None:
    validator = _load_validator()
    validator.validate_event({os.getenv(os.getenv('VIBE_87969F0C')): os.
        getenv(os.getenv('VIBE_3E0DF71A')), os.getenv(os.getenv(
        'VIBE_B7E2EC81')): os.getenv(os.getenv('VIBE_6D248286')), os.getenv
        (os.getenv('VIBE_4105CE84')): os.getenv(os.getenv('VIBE_EB71157D')),
        os.getenv(os.getenv('VIBE_0D72F018')): os.getenv(os.getenv(
        'VIBE_51029727')), os.getenv(os.getenv('VIBE_94C7A23C')): {os.
        getenv(os.getenv('VIBE_087AEF6D')): os.getenv(os.getenv(
        'VIBE_B484D605'))}}, os.getenv(os.getenv('VIBE_C95AA627')))
    validator.validate_event({os.getenv(os.getenv('VIBE_87969F0C')): os.
        getenv(os.getenv('VIBE_5163742C')), os.getenv(os.getenv(
        'VIBE_B7E2EC81')): os.getenv(os.getenv('VIBE_6D248286')), os.getenv
        (os.getenv('VIBE_D60BDE5D')): os.getenv(os.getenv('VIBE_AA5EF26A')),
        os.getenv(os.getenv('VIBE_C7ECF0C5')): os.getenv(os.getenv(
        'VIBE_098E072B')), os.getenv(os.getenv('VIBE_B941E116')): {os.
        getenv(os.getenv('VIBE_0D72F018')): os.getenv(os.getenv(
        'VIBE_6966EF92'))}, os.getenv(os.getenv('VIBE_94C7A23C')): {os.
        getenv(os.getenv('VIBE_087AEF6D')): os.getenv(os.getenv(
        'VIBE_B484D605'))}, os.getenv(os.getenv('VIBE_0AB8F67D')): float(os
        .getenv(os.getenv('VIBE_3907054B')))}, os.getenv(os.getenv(
        'VIBE_6A5B3712')))
    print(os.getenv(os.getenv('VIBE_2587C31C')))


if __name__ == os.getenv(os.getenv('VIBE_721F5F58')):
    main()
