"""Utility script to verify that every field in the UI settings can be saved.

The script performs the following steps:
1. GET the current settings from ``/v1/ui/settings/sections``.
2. For each field it generates a deterministic test value based on the field
   type (text → ``<original>_test``, number → ``1``, boolean → ``True``).
   Secret/password fields are also updated (the backend will encrypt them).
3. POST the modified ``sections`` payload back to the same endpoint.
4. Verify that the response status is 200 and that the returned payload
   contains the same section/field IDs.
5. Print a summary indicating success or any failures.

This script is useful for a quick sanity‑check that the UI‑save flow works for
all fields without manually opening the web UI.
"""

import sys
from typing import Any, Dict, List

import requests

BASE_URL = "http://localhost:21016"
SETTINGS_ENDPOINT = f"{BASE_URL}/v1/ui/settings/sections"


def generate_test_value(field: Dict[str, Any]) -> Any:
    """Return a test value appropriate for the field type.

    The function respects the ``type`` attribute used by the UI schema.
    """
    ftype = field.get("type", "text")
    original = field.get("value")
    if ftype == "number":
        return 1
    if ftype == "range":
        try:
            lo = float(field.get("min", 0))
            hi = float(field.get("max", 10))
            return (lo + hi) / 2
        except Exception:
            return 5
    if ftype == "switch":
        return not bool(original)
    if ftype == "select":
        opts = field.get("options")
        if isinstance(opts, list) and opts:
            return opts[0].get("value", "test")
        return "test"
    if ftype == "password" or field.get("secret") is True:
        return "test-secret-key"
    if isinstance(original, str):
        return original + "_test"
    return "test"


def main() -> int:
    # 1. Fetch current settings
    try:
        resp = requests.get(SETTINGS_ENDPOINT, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to fetch settings: {exc}", file=sys.stderr)
        return 1

    data = resp.json()
    sections: List[Dict[str, Any]] = data.get("sections", [])
    if not sections:
        print("No sections returned from the API.", file=sys.stderr)
        return 1

    # 2. Build a new payload with test values for every field
    test_sections = []
    for sec in sections:
        new_sec = {k: v for k, v in sec.items() if k != "fields"}
        new_fields = []
        for fld in sec.get("fields", []):
            new_fld = dict(fld)
            new_fld["value"] = generate_test_value(fld)
            new_fields.append(new_fld)
        new_sec["fields"] = new_fields
        test_sections.append(new_sec)

    payload = {"sections": test_sections}

    # 3. POST the modified settings back
    try:
        post_resp = requests.post(
            SETTINGS_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        post_resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to save settings: {exc}", file=sys.stderr)
        return 1

    result = post_resp.json()
    if result.get("status") != "saved":
        print("Unexpected response status", result, file=sys.stderr)
        return 1

    # 4. Verify that every field ID is present in the response
    returned_sections = result.get("sections", [])
    missing = []
    for sec in test_sections:
        sec_id = sec.get("id")
        ret_sec = next((s for s in returned_sections if s.get("id") == sec_id), None)
        if not ret_sec:
            missing.append(f"section {sec_id} missing in response")
            continue
        for fld in sec.get("fields", []):
            fid = fld.get("id")
            if not any(f.get("id") == fid for f in ret_sec.get("fields", [])):
                missing.append(f"field {fid} in section {sec_id} missing in response")

    if missing:
        print("Some fields were not echoed back correctly:")
        for m in missing:
            print(" -", m)
        return 1

    # 5. Success summary
    print("All settings fields saved successfully and echoed back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
