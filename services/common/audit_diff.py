"""Masked audit diff generator for settings changes"""
import json
import re
from typing import Any, Dict
from prometheus_client import Counter

audit_diff_total = Counter('audit_diff_total', 'Total masked audit diff events')
MASK_PATTERNS = [r"(?i)(password|secret|token|key)\b.*", r"(?i)api_key.*", r"(?i)private.*"]

def mask_value(value: str) -> str:
    """Replace secret values with placeholder."""
    return "***MASKED***"

def generate_diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Return masked diff {"old": ..., "new": ..., "changes": ...}"""
    diff = {"old": {}, "new": {}, "changes": []}
    for key, new_val in new.items():
        old_val = old.get(key)
        masked_old = mask_value(str(old_val)) if any(p in key.lower() for p in MASK_PATTERNS) else old_val
        masked_new = mask_value(str(new_val)) if any(p in key.lower() for p in MASK_PATTERNS) else new_val
        if str(masked_old) != str(masked_new):
            diff[