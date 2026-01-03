"""Masked audit diff generator for settings changes"""

import re
from typing import Any, Dict

from prometheus_client import Counter

audit_diff_total = Counter("audit_diff_total", "Total masked audit diff events")
MASK_PATTERNS = [r"(?i)(password|secret|token|key)\b.*", r"(?i)api_key.*", r"(?i)private.*"]


def mask_value(value: str) -> str:
    return "***MASKED***"


def generate_diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Return masked diff {"old": ..., "new": ..., "changes": ...}"""
    diff = {"old": {}, "new": {}, "changes": []}

    def _secret(k: str) -> bool:
        return any(re.search(pat, k) for pat in MASK_PATTERNS)

    all_keys = set(old.keys()) | set(new.keys())
    for key in sorted(all_keys):
        old_val = old.get(key)
        new_val = new.get(key)
        masked_old = mask_value(str(old_val)) if _secret(key) else old_val
        masked_new = mask_value(str(new_val)) if _secret(key) else new_val
        if str(masked_old) != str(masked_new):
            diff["old"][key] = masked_old
            diff["new"][key] = masked_new
            diff["changes"].append(key)
    return diff
