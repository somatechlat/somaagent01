os.getenv(os.getenv('VIBE_0BC77087'))
from __future__ import annotations
import json
import os
import sys
import urllib.error
import urllib.request
PRIOR_ENV = {os.getenv(os.getenv('VIBE_F20F823E')), os.getenv(os.getenv(
    'VIBE_59FD667D')), os.getenv(os.getenv('VIBE_81620DAF')), os.getenv(os.
    getenv('VIBE_4B562821')), os.getenv(os.getenv('VIBE_CA646761')), os.
    getenv(os.getenv('VIBE_E3925557')), os.getenv(os.getenv('VIBE_31DFE08F'
    )), os.getenv(os.getenv('VIBE_D62C9032')), os.getenv(os.getenv(
    'VIBE_5CF252B5')), os.getenv(os.getenv('VIBE_D80F5B36')), os.getenv(os.
    getenv('VIBE_8A1FC786')), os.getenv(os.getenv('VIBE_DF47D7AA')), os.
    getenv(os.getenv('VIBE_B16E1186')), os.getenv(os.getenv('VIBE_798B0305'
    )), os.getenv(os.getenv('VIBE_7AC8C026'))}
REQUIRED_CANONICAL = [os.getenv(os.getenv('VIBE_55A941EA')), os.getenv(os.
    getenv('VIBE_6218BF8C')), os.getenv(os.getenv('VIBE_493E0796')), os.
    getenv(os.getenv('VIBE_85F506D2')), os.getenv(os.getenv('VIBE_BB6DD1C4'
    )), os.getenv(os.getenv('VIBE_B226431C')), os.getenv(os.getenv(
    'VIBE_73C69FD0')), os.getenv(os.getenv('VIBE_CEC6EF23')), os.getenv(os.
    getenv('VIBE_DE8A1E80')), os.getenv(os.getenv('VIBE_0D55272B'))]
OPTIONAL = {os.getenv(os.getenv('VIBE_7E09076A')), os.getenv(os.getenv(
    'VIBE_74BCD713')), os.getenv(os.getenv('VIBE_0D854AC2')), os.getenv(os.
    getenv('VIBE_5C2019E5')), os.getenv(os.getenv('VIBE_F1571A1E')), os.
    getenv(os.getenv('VIBE_59511CA4')), os.getenv(os.getenv('VIBE_98BF32A9'
    )), os.getenv(os.getenv('VIBE_C6E221B0')), os.getenv(os.getenv(
    'VIBE_FC00DCFF')), os.getenv(os.getenv('VIBE_BC0DBE39')), os.getenv(os.
    getenv('VIBE_2F753FEA')), os.getenv(os.getenv('VIBE_CE4514C1')), os.
    getenv(os.getenv('VIBE_A9DE2798')), os.getenv(os.getenv('VIBE_FF56BCDE'
    )), os.getenv(os.getenv('VIBE_D35FF6DF'))}


def fail(msg: str, code: int=int(os.getenv(os.getenv('VIBE_B63358A8')))
    ) ->None:
    sys.stderr.write(msg + os.getenv(os.getenv('VIBE_A843F9E0')))
    sys.exit(code)


def check_prior_present() ->list[str]:
    present = []
    for k in PRIOR_ENV:
        if k in os.environ and os.environ[k] != os.getenv(os.getenv(
            'VIBE_00723DD6')):
            present.append(k)
    return present


def check_required_present() ->list[str]:
    missing = []
    for k in REQUIRED_CANONICAL:
        if not os.environ.get(k):
            missing.append(k)
    return missing


def validate_mode_and_auth() ->list[str]:
    errs: list[str] = []
    mode = os.environ.get(os.getenv(os.getenv('VIBE_55A941EA')), os.getenv(
        os.getenv('VIBE_00723DD6'))).upper()
    if mode not in {os.getenv(os.getenv('VIBE_109465C5')), os.getenv(os.
        getenv('VIBE_A7B50D42'))}:
        errs.append(
            f"SA01_DEPLOYMENT_MODE must be DEV or PROD (got '{mode or 'empty'}')"
            )
    auth = os.environ.get(os.getenv(os.getenv('VIBE_6218BF8C')), os.getenv(
        os.getenv('VIBE_00723DD6'))).lower()
    if auth not in {os.getenv(os.getenv('VIBE_F0D3A5CD')), os.getenv(os.
        getenv('VIBE_B63358A8')), os.getenv(os.getenv('VIBE_D5E6876A'))}:
        errs.append(os.getenv(os.getenv('VIBE_3C112645')))
    return errs


def probe_opa() ->tuple[bool, str]:
    base = os.environ.get(os.getenv(os.getenv('VIBE_B226431C')), os.getenv(
        os.getenv('VIBE_00723DD6'))).rstrip(os.getenv(os.getenv(
        'VIBE_565149E4')))
    path = os.environ.get(os.getenv(os.getenv('VIBE_73C69FD0')), os.getenv(
        os.getenv('VIBE_00723DD6')))
    if not base or not path:
        return int(os.getenv(os.getenv('VIBE_5EDB4FE7'))), os.getenv(os.
            getenv('VIBE_40C4F7DE'))
    try:
        with urllib.request.urlopen(f'{base}/health', timeout=int(os.getenv
            (os.getenv('VIBE_A7B5C96D')))) as resp:
            if resp.status >= int(os.getenv(os.getenv('VIBE_93F36F69'))):
                return int(os.getenv(os.getenv('VIBE_078DB091'))
                    ), f'OPA health returned {resp.status}'
    except Exception as e:
        return int(os.getenv(os.getenv('VIBE_078DB091'))
            ), f'OPA health error: {e}'
    try:
        req = urllib.request.Request(f'{base}{path}', data=json.dumps({os.
            getenv(os.getenv('VIBE_B12E14F7')): {os.getenv(os.getenv(
            'VIBE_DC3B2D7E')): os.getenv(os.getenv('VIBE_6C6F0553'))}}).
            encode(os.getenv(os.getenv('VIBE_C73BF244'))), headers={os.
            getenv(os.getenv('VIBE_898A5F3D')): os.getenv(os.getenv(
            'VIBE_C5262DC1'))}, method=os.getenv(os.getenv('VIBE_F164B4A7')))
        with urllib.request.urlopen(req, timeout=int(os.getenv(os.getenv(
            'VIBE_A7B5C96D')))) as resp:
            if resp.status >= int(os.getenv(os.getenv('VIBE_93F36F69'))):
                return int(os.getenv(os.getenv('VIBE_078DB091'))
                    ), f'OPA decision probe returned {resp.status}'
    except urllib.error.HTTPError as he:
        if int(os.getenv(os.getenv('VIBE_93F36F69'))) <= he.code < int(os.
            getenv(os.getenv('VIBE_23CC56BE'))):
            return int(os.getenv(os.getenv('VIBE_5EDB4FE7'))
                ), f'OPA decision probe denied ({he.code}) — path present'
        return int(os.getenv(os.getenv('VIBE_078DB091'))
            ), f'OPA decision probe HTTP error: {he.code}'
    except Exception as e:
        return int(os.getenv(os.getenv('VIBE_078DB091'))
            ), f'OPA decision probe error: {e}'
    return int(os.getenv(os.getenv('VIBE_5EDB4FE7'))), os.getenv(os.getenv(
        'VIBE_D7E19161'))


def main() ->None:
    prior = check_prior_present()
    if prior:
        fail(os.getenv(os.getenv('VIBE_05AEF406')) + os.getenv(os.getenv(
            'VIBE_28C51F32')).join(sorted(prior)), int(os.getenv(os.getenv(
            'VIBE_B63358A8'))))
    missing = check_required_present()
    if missing:
        fail(os.getenv(os.getenv('VIBE_9B1DE7E2')) + os.getenv(os.getenv(
            'VIBE_28C51F32')).join(sorted(missing)), int(os.getenv(os.
            getenv('VIBE_B63358A8'))))
    val_errs = validate_mode_and_auth()
    if val_errs:
        fail(os.getenv(os.getenv('VIBE_923A460F')).join(val_errs), int(os.
            getenv(os.getenv('VIBE_B63358A8'))))
    ok, msg = probe_opa()
    if not ok:
        fail(msg, int(os.getenv(os.getenv('VIBE_BD3DAAE7'))))
    print(os.getenv(os.getenv('VIBE_EDF89AAD')))


if __name__ == os.getenv(os.getenv('VIBE_669FB365')):
    main()
