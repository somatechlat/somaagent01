import base64
import os
import re
from typing import Any

from dotenv import load_dotenv as _load_dotenv

from .files import get_abs_path

KEY_AUTH_LOGIN = "AUTH_LOGIN"
KEY_AUTH_PASSWORD = "AUTH_PASSWORD"
KEY_RFC_PASSWORD = "RFC_PASSWORD"
KEY_ROOT_PASSWORD = "ROOT_PASSWORD"


def load_dotenv():
    _load_dotenv(get_dotenv_file_path(), override=True)


def get_dotenv_file_path():
    return get_abs_path(".env")


def get_dotenv_value(key: str, default: Any = None):
    """Return an environment value with production-friendly fallbacks.

    Resolution order (first non-empty wins):
    1) KEY
    2) KEY_FILE -> read file contents, strip trailing newlines
    3) KEY_B64 -> base64-decode value
    4) KEY_B64_FILE -> read file and base64-decode contents

    If a file-based value is loaded, this function also sets os.environ[KEY]
    so downstream libraries that read only KEY continue to work.
    """
    # Direct value
    val = os.getenv(key)
    if val not in (None, ""):
        return val

    # File value
    file_path = os.getenv(f"{key}_FILE")
    if file_path:
        try:
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    content = f.read().decode("utf-8").strip()
                if content != "":
                    os.environ[key] = content
                    return content
        except Exception:
            # Fall through to other options / default
            pass

    # Base64 inline
    b64_val = os.getenv(f"{key}_B64")
    if b64_val not in (None, ""):
        try:
            decoded = base64.b64decode(b64_val).decode("utf-8").strip()
            if decoded != "":
                os.environ[key] = decoded
                return decoded
        except Exception:
            pass

    # Base64 from file
    b64_file = os.getenv(f"{key}_B64_FILE")
    if b64_file:
        try:
            if os.path.isfile(b64_file):
                with open(b64_file, "rb") as f:
                    decoded = base64.b64decode(f.read()).decode("utf-8").strip()
                if decoded != "":
                    os.environ[key] = decoded
                    return decoded
        except Exception:
            pass

    return default


def save_dotenv_value(key: str, value: str):
    if value is None:
        value = ""
    dotenv_path = get_dotenv_file_path()
    if not os.path.isfile(dotenv_path):
        with open(dotenv_path, "w") as f:
            f.write("")
    with open(dotenv_path, "r+") as f:
        lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if re.match(rf"^\s*{key}\s*=", line):
                lines[i] = f"{key}={value}\n"
                found = True
        if not found:
            lines.append(f"\n{key}={value}\n")
        f.seek(0)
        f.writelines(lines)
        f.truncate()
    load_dotenv()
