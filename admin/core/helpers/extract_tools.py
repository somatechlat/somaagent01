"""Module extract_tools."""

import importlib
import importlib.util
import inspect
import logging
import os
import re
from fnmatch import fnmatch
from types import ModuleType
from typing import Any, Type, TypeVar

import regex

from .dirty_json import DirtyJson
from .files import get_abs_path

LOGGER = logging.getLogger(__name__)


def json_parse_dirty(json: str) -> dict[str, Any] | None:
    """Execute json parse dirty.

        Args:
            json: The json.
        """

    if not json or not isinstance(json, str):
        return None

    ext_json = extract_json_object_string(json.strip())
    if ext_json:
        try:
            data = DirtyJson.parse_string(ext_json)
            if isinstance(data, dict):
                return data
        except Exception:
            # If parsing fails, return None instead of crashing
            return None
    return None


def extract_json_object_string(content):
    """Execute extract json object string.

        Args:
            content: The content.
        """

    start = content.find("{")
    if start == -1:
        return ""

    # Find the first '{'
    end = content.rfind("}")
    if end == -1:
        # If there's no closing '}', return from start to the end
        return content[start:]
    else:
        # If there's a closing '}', return the substring from start to end
        return content[start : end + 1]


def extract_json_string(content):
    # Regular expression pattern to match a JSON object
    """Execute extract json string.

        Args:
            content: The content.
        """

    pattern = r'\{(?:[^{}]|(?R))*\}|\[(?:[^\[\]]|(?R))*\]|"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'

    # Search for the pattern in the content
    match = regex.search(pattern, content)

    if match:
        # Return the matched JSON string
        return match.group(0)
    else:
        return ""


def fix_json_string(json_string):
    # Function to replace unescaped line breaks within JSON string values
    """Execute fix json string.

        Args:
            json_string: The json_string.
        """

    def replace_unescaped_newlines(match):
        """Execute replace unescaped newlines.

            Args:
                match: The match.
            """

        return match.group(0).replace("\n", "\\n")

    # Use regex to find string values and apply the replacement function
    fixed_string = re.sub(
        r'(?<=: ")(.*?)(?=")', replace_unescaped_newlines, json_string, flags=re.DOTALL
    )
    return fixed_string


T = TypeVar("T")  # Define a generic type variable


def import_module(file_path: str) -> ModuleType:
    # Handle file paths with periods in the name using importlib.util
    """Execute import module.

        Args:
            file_path: The file_path.
        """

    abs_path = get_abs_path(file_path)
    module_name = os.path.basename(abs_path).replace(".py", "")

    # Do not silently ignore missing files — importing should fail loudly so
    # CI / dev environments surface missing expected modules. Callers will
    # continue to handle ImportError/None as before when appropriate.
    if not os.path.exists(abs_path):
        raise ImportError(f"Module file not found: {abs_path}")

    # Create the module spec and load the module
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {abs_path}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        # Log import failure but don't let a single failing API handler crash the
        # whole UI process. Caller functions will skip None modules.
        LOGGER.warning("Warning: failed importing %s: %s", abs_path, e, exc_info=True)
        return None
    return module


def load_classes_from_folder(
    folder: str, name_pattern: str, base_class: Type[T], one_per_file: bool = True
) -> list[Type[T]]:
    """Execute load classes from folder.

        Args:
            folder: The folder.
            name_pattern: The name_pattern.
            base_class: The base_class.
            one_per_file: The one_per_file.
        """

    classes = []
    abs_folder = get_abs_path(folder)

    # Get all .py files in the folder that match the pattern, sorted alphabetically
    py_files = sorted(
        [
            file_name
            for file_name in os.listdir(abs_folder)
            if fnmatch(file_name, name_pattern) and file_name.endswith(".py")
        ]
    )

    # Iterate through the sorted list of files
    for file_name in py_files:
        file_path = os.path.join(abs_folder, file_name)
        # Use the new import_module function
        module = import_module(file_path)
        if module is None:
            # Skip modules that failed to import
            continue

        # Get all classes in the module
        class_list = inspect.getmembers(module, inspect.isclass)

        # Filter for classes that are subclasses of the given base_class
        # iterate backwards to skip imported superclasses
        for cls in reversed(class_list):
            if cls[1] is not base_class and issubclass(cls[1], base_class):
                classes.append(cls[1])
                if one_per_file:
                    break

    return classes


def load_classes_from_file(
    file: str, base_class: type[T], one_per_file: bool = True
) -> list[type[T]]:
    """Execute load classes from file.

        Args:
            file: The file.
            base_class: The base_class.
            one_per_file: The one_per_file.
        """

    classes = []
    # Use the new import_module function
    module = import_module(file)

    # Get all classes in the module
    class_list = inspect.getmembers(module, inspect.isclass)

    # Filter for classes that are subclasses of the given base_class
    # iterate backwards to skip imported superclasses
    for cls in reversed(class_list):
        if cls[1] is not base_class and issubclass(cls[1], base_class):
            classes.append(cls[1])
            if one_per_file:
                break

    return classes