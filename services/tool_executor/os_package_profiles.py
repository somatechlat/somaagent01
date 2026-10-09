"""Operator allowlist for container OS packages — TOOLS-001 §5.4.1.

Structured package **names only** (Debian distribution names). No shell
strings, no apt mirrors/URLs, no version pins from the model — apt resolves
those inside the agent container. Unknown names fail closed.

The allowlist is deliberately small. The operator extends it here (or bakes
the agent image) — never the model, never a chat-turn argument.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Tuple

# Curated OS profiles. Names are Debian package names the operator would
# allow inside the agent container image.
OS_PACKAGE_PROFILES: Dict[str, Tuple[str, ...]] = {
    "media": (
        "ffmpeg",
        "imagemagick",
    ),
    "docs": (
        "poppler-utils",
        "unzip",
    ),
}

# Flat allowlist = union of profile members (single source of truth).
OS_PACKAGE_ALLOWLIST: FrozenSet[str] = frozenset(
    name for names in OS_PACKAGE_PROFILES.values() for name in names
)

OS_PROFILE_IDS: Tuple[str, ...] = tuple(sorted(OS_PACKAGE_PROFILES))

# Package → binary verified with `which <bin>` after install. Only the
# curated set has an entry; an unknown mapping fails closed in the workflow.
OS_PACKAGE_BINARIES: Dict[str, str] = {
    "ffmpeg": "ffmpeg",
    "imagemagick": "convert",
    "poppler-utils": "pdftotext",
    "unzip": "unzip",
}


def resolve_os_profile(profile: str) -> List[str]:
    """Return the package list for an OS profile id or raise KeyError."""
    key = (profile or "").strip().lower()
    if key not in OS_PACKAGE_PROFILES:
        raise KeyError(profile)
    return list(OS_PACKAGE_PROFILES[key])


def filter_os_allowlisted(packages: List[str]) -> Tuple[List[str], List[str]]:
    """Split requested names into (allowed, denied)."""
    allowed: List[str] = []
    denied: List[str] = []
    canonical = {p.lower(): p for p in OS_PACKAGE_ALLOWLIST}
    for raw in packages or []:
        name = str(raw or "").strip()
        if not name:
            continue
        hit = canonical.get(name.lower())
        if hit is not None:
            allowed.append(hit)
        else:
            denied.append(name)
    # de-dupe preserving order
    seen = set()
    uniq: List[str] = []
    for n in allowed:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq, denied


def os_binary_for(package: str) -> str:
    """Binary to `which` for a curated package, or '' when unmapped."""
    return OS_PACKAGE_BINARIES.get(str(package or "").strip().lower(), "")


def all_os_profile_ids() -> List[str]:
    return list(OS_PROFILE_IDS)
