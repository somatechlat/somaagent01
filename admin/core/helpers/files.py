"""File system utility functions.

Production-grade file operations for SomaAgent01.
Legacy AgentZero prompt template functions have been removed.
"""

import base64
import glob
import os
import re
import shutil
import tempfile
import zipfile
from fnmatch import fnmatch

from admin.core.helpers.strings import sanitize_string


def read_file(relative_path: str, encoding="utf-8"):
    """Read file content.

    Args:
        relative_path: Relative path to the file.
        encoding: File encoding.
    """
    absolute_path = get_abs_path(relative_path)
    with open(absolute_path, "r", encoding=encoding) as f:
        return f.read()


def read_file_bin(relative_path: str):
    """Read binary file content.

    Args:
        relative_path: Relative path to the file.
    """
    absolute_path = get_abs_path(relative_path)
    with open(absolute_path, "rb") as f:
        return f.read()


def read_file_base64(relative_path):
    """Read file content as base64.

    Args:
        relative_path: Relative path to the file.
    """
    absolute_path = get_abs_path(relative_path)
    with open(absolute_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def write_file(relative_path: str, content: str, encoding: str = "utf-8"):
    """Write content to file.

    Args:
        relative_path: Relative path to the file.
        content: Content to write.
        encoding: File encoding.
    """
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    content = sanitize_string(content, encoding)
    with open(abs_path, "w", encoding=encoding) as f:
        f.write(content)


def write_file_bin(relative_path: str, content: bytes):
    """Write binary content to file.

    Args:
        relative_path: Relative path to the file.
        content: Binary content to write.
    """
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)


def write_file_base64(relative_path: str, content: str):
    """Write base64 encoded content to file.

    Args:
        relative_path: Relative path to the file.
        content: Base64 encoded content.
    """
    data = base64.b64decode(content)
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(data)


def delete_dir(relative_path: str):
    """Delete a directory safely.

    Args:
        relative_path: Relative path to the directory.
    """
    abs_path = get_abs_path(relative_path)
    if os.path.exists(abs_path):
        shutil.rmtree(abs_path, ignore_errors=True)
        if os.path.exists(abs_path):
            try:
                for root, dirs, files in os.walk(abs_path, topdown=False):
                    for name in files:
                        file_path = os.path.join(root, name)
                        os.chmod(file_path, 0o777)
                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        os.chmod(dir_path, 0o777)
                shutil.rmtree(abs_path, ignore_errors=True)
            except Exception:
                pass


def list_files(relative_path: str, filter: str = "*"):
    """List files in a directory.

    Args:
        relative_path: Relative path to the directory.
        filter: Glob pattern filter.
    """
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    return [file for file in os.listdir(abs_path) if fnmatch(file, filter)]


def make_dirs(relative_path: str):
    """Create directories.

    Args:
        relative_path: Relative path to create.
    """
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)


def get_abs_path(*relative_paths):
    """Convert relative paths to absolute paths based on the base directory."""
    return os.path.join(get_base_dir(), *relative_paths)


def deabsolute_path(path: str):
    """Convert absolute paths to relative paths based on the base directory."""
    return os.path.relpath(path, get_base_dir())


def fix_dev_path(path: str):
    """Convert legacy /a0/ paths to modern paths."""
    from admin.core.helpers.runtime import is_development

    if is_development():
        if path.startswith("/a0/"):
            path = path.replace("/a0/", "")
        elif path.startswith("/git/somaagent01/"):
            path = path.replace("/git/somaagent01/", "")
    return get_abs_path(path)


def exists(*relative_paths):
    """Check if path exists."""
    path = get_abs_path(*relative_paths)
    return os.path.exists(path)


def get_base_dir():
    """Get the base directory."""
    base_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, "../../")))
    return base_dir


def basename(path: str, suffix: str | None = None):
    """Get basename of a path.

    Args:
        path: The path.
        suffix: Suffix to remove.
    """
    if suffix:
        return os.path.basename(path).removesuffix(suffix)
    return os.path.basename(path)


def dirname(path: str):
    """Get directory name of a path.

    Args:
        path: The path.
    """
    return os.path.dirname(path)


def is_in_base_dir(path: str):
    """Check if path is within the base directory.

    Args:
        path: The path to check.
    """
    base_dir = get_base_dir()
    abs_path = os.path.abspath(path)
    return os.path.commonpath([abs_path, base_dir]) == base_dir


def get_subdirectories(
    relative_path: str,
    include: str | list[str] = "*",
    exclude: str | list[str] | None = None,
):
    """Get subdirectories with filtering.

    Args:
        relative_path: Relative path to search.
        include: Include patterns.
        exclude: Exclude patterns.
    """
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]
    return [
        subdir
        for subdir in os.listdir(abs_path)
        if os.path.isdir(os.path.join(abs_path, subdir))
        and any(fnmatch(subdir, inc) for inc in include)
        and (exclude is None or not any(fnmatch(subdir, exc) for exc in exclude))
    ]


def zip_dir(dir_path: str):
    """Zip a directory.

    Args:
        dir_path: Directory to zip.
    """
    full_path = get_abs_path(dir_path)
    zip_file_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False).name
    base_name = os.path.basename(full_path)
    with zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zip:
        for root, _, files in os.walk(full_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, full_path)
                zip.write(file_path, os.path.join(base_name, rel_path))
    return zip_file_path


def move_file(relative_path: str, new_path: str):
    """Move a file.

    Args:
        relative_path: Current path.
        new_path: New path.
    """
    abs_path = get_abs_path(relative_path)
    new_abs_path = get_abs_path(new_path)
    os.makedirs(os.path.dirname(new_abs_path), exist_ok=True)
    os.rename(abs_path, new_abs_path)


def safe_file_name(filename: str) -> str:
    """Sanitize filename.

    Args:
        filename: Filename to sanitize.
    """
    return re.sub(r"[^a-zA-Z0-9-._]", "_", filename)


def find_file_in_dirs(_filename: str, _directories: list[str]):
    """Search for a filename in directories.

    Returns the absolute path of the first found file.
    """
    for directory in _directories:
        full_path = get_abs_path(directory, _filename)
        if exists(full_path):
            return full_path
    raise FileNotFoundError(f"File '{_filename}' not found in any of the provided directories.")


def get_unique_filenames_in_dirs(dir_paths: list[str], pattern: str = "*"):
    """Get unique filenames from directories.

    Args:
        dir_paths: Directories to search.
        pattern: Glob pattern.
    """
    seen = set()
    result = []
    for dir_path in dir_paths:
        full_dir = get_abs_path(dir_path)
        for file_path in glob.glob(os.path.join(full_dir, pattern)):
            fname = os.path.basename(file_path)
            if fname not in seen and os.path.isfile(file_path):
                seen.add(fname)
                result.append(get_abs_path(file_path))
    result.sort(key=lambda path: os.path.basename(path))
    return result
