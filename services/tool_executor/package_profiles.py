"""Operator allowlist for package profiles — TOOLS-001 §5.4.

Versions are **not** model-guessed. Profiles list distribution names only;
pip resolves compatible pins inside the workroot venv under Temporal.
Unknown names fail closed. No free-form shell strings.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Tuple

# Curated profiles. Extend only with names an operator would bake into an image.
PACKAGE_PROFILES: Dict[str, Tuple[str, ...]] = {
    "scientific": (
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
        "sympy",
        "seaborn",
    ),
    "office": (
        "python-docx",
        "openpyxl",
        "python-pptx",
        "reportlab",
        "odfpy",
    ),
    "data": (
        "pandas",
        "pyarrow",
        "openpyxl",
    ),
    "vision": (
        "pillow",
    ),
}

# Flat allowlist = union of profile members (single source of truth).
PACKAGE_ALLOWLIST: FrozenSet[str] = frozenset(
    name for names in PACKAGE_PROFILES.values() for name in names
)

PROFILE_IDS: Tuple[str, ...] = tuple(sorted(PACKAGE_PROFILES))


def resolve_profile_packages(profile: str) -> List[str]:
    """Return the package list for a profile id or raise KeyError."""
    key = (profile or "").strip().lower()
    if key not in PACKAGE_PROFILES:
        raise KeyError(profile)
    return list(PACKAGE_PROFILES[key])


def filter_allowlisted(packages: List[str]) -> Tuple[List[str], List[str]]:
    """Split requested names into (allowed, denied)."""
    allowed: List[str] = []
    denied: List[str] = []
    for raw in packages or []:
        name = str(raw or "").strip()
        if not name:
            continue
        if name.lower() in {p.lower() for p in PACKAGE_ALLOWLIST}:
            # Canonical casing from allowlist
            for canon in PACKAGE_ALLOWLIST:
                if canon.lower() == name.lower():
                    allowed.append(canon)
                    break
        else:
            denied.append(name)
    # de-dupe preserving order
    seen = set()
    uniq = []
    for n in allowed:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq, denied


def all_profile_ids() -> List[str]:
    return list(PROFILE_IDS)
