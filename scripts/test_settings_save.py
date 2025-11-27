import os
os.getenv(os.getenv('VIBE_236201ED'))
import sys
from typing import Any, Dict, List
import requests
BASE_URL = os.getenv(os.getenv('VIBE_4ED0E1A5'))
SETTINGS_ENDPOINT = f'{BASE_URL}/v1/ui/settings/sections'


def generate_test_value(field: Dict[str, Any]) ->Any:
    os.getenv(os.getenv('VIBE_BBFBBB00'))
    ftype = field.get(os.getenv(os.getenv('VIBE_9FECA844')), os.getenv(os.
        getenv('VIBE_5182143D')))
    original = field.get(os.getenv(os.getenv('VIBE_3D7141CC')))
    if ftype == os.getenv(os.getenv('VIBE_6BFBC969')):
        return int(os.getenv(os.getenv('VIBE_1580419D')))
    if ftype == os.getenv(os.getenv('VIBE_79592113')):
        try:
            lo = float(field.get(os.getenv(os.getenv('VIBE_6EBB5AA0')), int
                (os.getenv(os.getenv('VIBE_172D2EED')))))
            hi = float(field.get(os.getenv(os.getenv('VIBE_09DF9FE7')), int
                (os.getenv(os.getenv('VIBE_72FD47E9')))))
            return (lo + hi) / int(os.getenv(os.getenv('VIBE_B1701BB2')))
        except Exception:
            return int(os.getenv(os.getenv('VIBE_C72A6F6B')))
    if ftype == os.getenv(os.getenv('VIBE_68A000F8')):
        return not bool(original)
    if ftype == os.getenv(os.getenv('VIBE_42B17EEE')):
        opts = field.get(os.getenv(os.getenv('VIBE_DF200B5C')))
        if isinstance(opts, list) and opts:
            return opts[int(os.getenv(os.getenv('VIBE_172D2EED')))].get(os.
                getenv(os.getenv('VIBE_3D7141CC')), os.getenv(os.getenv(
                'VIBE_03246120')))
        return os.getenv(os.getenv('VIBE_03246120'))
    if ftype == os.getenv(os.getenv('VIBE_CC31FDA1')) or field.get(os.
        getenv(os.getenv('VIBE_4A0D6DE6'))) is int(os.getenv(os.getenv(
        'VIBE_BB71B7B2'))):
        return os.getenv(os.getenv('VIBE_7A76298C'))
    if isinstance(original, str):
        return original + os.getenv(os.getenv('VIBE_BA8347D2'))
    return os.getenv(os.getenv('VIBE_03246120'))


def main() ->int:
    try:
        resp = requests.get(SETTINGS_ENDPOINT, timeout=int(os.getenv(os.
            getenv('VIBE_72FD47E9'))))
        resp.raise_for_status()
    except Exception as exc:
        print(f'Failed to fetch settings: {exc}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1580419D')))
    data = resp.json()
    sections: List[Dict[str, Any]] = data.get(os.getenv(os.getenv(
        'VIBE_FCE0C623')), [])
    if not sections:
        print(os.getenv(os.getenv('VIBE_24154300')), file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1580419D')))
    test_sections = []
    for sec in sections:
        new_sec = {k: v for k, v in sec.items() if k != os.getenv(os.getenv
            ('VIBE_4BB431AE'))}
        new_fields = []
        for fld in sec.get(os.getenv(os.getenv('VIBE_4BB431AE')), []):
            new_fld = dict(fld)
            new_fld[os.getenv(os.getenv('VIBE_3D7141CC'))
                ] = generate_test_value(fld)
            new_fields.append(new_fld)
        new_sec[os.getenv(os.getenv('VIBE_4BB431AE'))] = new_fields
        test_sections.append(new_sec)
    payload = {os.getenv(os.getenv('VIBE_FCE0C623')): test_sections}
    try:
        post_resp = requests.post(SETTINGS_ENDPOINT, json=payload, headers=
            {os.getenv(os.getenv('VIBE_1335492C')): os.getenv(os.getenv(
            'VIBE_17BA2E69'))}, timeout=int(os.getenv(os.getenv(
            'VIBE_BD2FC7C8'))))
        post_resp.raise_for_status()
    except Exception as exc:
        print(f'Failed to save settings: {exc}', file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1580419D')))
    result = post_resp.json()
    if result.get(os.getenv(os.getenv('VIBE_96AF09BC'))) != os.getenv(os.
        getenv('VIBE_E7F9BCE2')):
        print(os.getenv(os.getenv('VIBE_745B970A')), result, file=sys.stderr)
        return int(os.getenv(os.getenv('VIBE_1580419D')))
    returned_sections = result.get(os.getenv(os.getenv('VIBE_FCE0C623')), [])
    missing = []
    for sec in test_sections:
        sec_id = sec.get(os.getenv(os.getenv('VIBE_13B67062')))
        ret_sec = next((s for s in returned_sections if s.get(os.getenv(os.
            getenv('VIBE_13B67062'))) == sec_id), None)
        if not ret_sec:
            missing.append(f'section {sec_id} missing in response')
            continue
        for fld in sec.get(os.getenv(os.getenv('VIBE_4BB431AE')), []):
            fid = fld.get(os.getenv(os.getenv('VIBE_13B67062')))
            if not any(f.get(os.getenv(os.getenv('VIBE_13B67062'))) == fid for
                f in ret_sec.get(os.getenv(os.getenv('VIBE_4BB431AE')), [])):
                missing.append(
                    f'field {fid} in section {sec_id} missing in response')
    if missing:
        print(os.getenv(os.getenv('VIBE_6A20F38B')))
        for m in missing:
            print(os.getenv(os.getenv('VIBE_35A96F04')), m)
        return int(os.getenv(os.getenv('VIBE_1580419D')))
    print(os.getenv(os.getenv('VIBE_D0FFF726')))
    return int(os.getenv(os.getenv('VIBE_172D2EED')))


if __name__ == os.getenv(os.getenv('VIBE_0F15D067')):
    sys.exit(main())
