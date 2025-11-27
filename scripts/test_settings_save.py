import os

os.getenv(os.getenv(""))
import sys
from typing import Any, Dict, List

import requests

BASE_URL = os.getenv(os.getenv(""))
SETTINGS_ENDPOINT = f"{BASE_URL}/v1/ui/settings/sections"


def generate_test_value(field: Dict[str, Any]) -> Any:
    os.getenv(os.getenv(""))
    ftype = field.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    original = field.get(os.getenv(os.getenv("")))
    if ftype == os.getenv(os.getenv("")):
        return int(os.getenv(os.getenv("")))
    if ftype == os.getenv(os.getenv("")):
        try:
            lo = float(field.get(os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))))
            hi = float(field.get(os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))))
            return (lo + hi) / int(os.getenv(os.getenv("")))
        except Exception:
            return int(os.getenv(os.getenv("")))
    if ftype == os.getenv(os.getenv("")):
        return not bool(original)
    if ftype == os.getenv(os.getenv("")):
        opts = field.get(os.getenv(os.getenv("")))
        if isinstance(opts, list) and opts:
            return opts[int(os.getenv(os.getenv("")))].get(
                os.getenv(os.getenv("")), os.getenv(os.getenv(""))
            )
        return os.getenv(os.getenv(""))
    if ftype == os.getenv(os.getenv("")) or field.get(os.getenv(os.getenv(""))) is int(
        os.getenv(os.getenv(""))
    ):
        return os.getenv(os.getenv(""))
    if isinstance(original, str):
        return original + os.getenv(os.getenv(""))
    return os.getenv(os.getenv(""))


def main() -> int:
    try:
        resp = requests.get(SETTINGS_ENDPOINT, timeout=int(os.getenv(os.getenv(""))))
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to fetch settings: {exc}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    data = resp.json()
    sections: List[Dict[str, Any]] = data.get(os.getenv(os.getenv("")), [])
    if not sections:
        print(os.getenv(os.getenv("")), file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    test_sections = []
    for sec in sections:
        new_sec = {k: v for k, v in sec.items() if k != os.getenv(os.getenv(""))}
        new_fields = []
        for fld in sec.get(os.getenv(os.getenv("")), []):
            new_fld = dict(fld)
            new_fld[os.getenv(os.getenv(""))] = generate_test_value(fld)
            new_fields.append(new_fld)
        new_sec[os.getenv(os.getenv(""))] = new_fields
        test_sections.append(new_sec)
    payload = {os.getenv(os.getenv("")): test_sections}
    try:
        post_resp = requests.post(
            SETTINGS_ENDPOINT,
            json=payload,
            headers={os.getenv(os.getenv("")): os.getenv(os.getenv(""))},
            timeout=int(os.getenv(os.getenv(""))),
        )
        post_resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to save settings: {exc}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    result = post_resp.json()
    if result.get(os.getenv(os.getenv(""))) != os.getenv(os.getenv("")):
        print(os.getenv(os.getenv("")), result, file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    returned_sections = result.get(os.getenv(os.getenv("")), [])
    missing = []
    for sec in test_sections:
        sec_id = sec.get(os.getenv(os.getenv("")))
        ret_sec = next(
            (s for s in returned_sections if s.get(os.getenv(os.getenv(""))) == sec_id), None
        )
        if not ret_sec:
            missing.append(f"section {sec_id} missing in response")
            continue
        for fld in sec.get(os.getenv(os.getenv("")), []):
            fid = fld.get(os.getenv(os.getenv("")))
            if not any(
                (
                    f.get(os.getenv(os.getenv(""))) == fid
                    for f in ret_sec.get(os.getenv(os.getenv("")), [])
                )
            ):
                missing.append(f"field {fid} in section {sec_id} missing in response")
    if missing:
        print(os.getenv(os.getenv("")))
        for m in missing:
            print(os.getenv(os.getenv("")), m)
        return int(os.getenv(os.getenv("")))
    print(os.getenv(os.getenv("")))
    return int(os.getenv(os.getenv("")))


if __name__ == os.getenv(os.getenv("")):
    sys.exit(main())
