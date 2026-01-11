"""Module guids."""

import random
import string


def generate_id(length: int = 8) -> str:
    """Execute generate id.

    Args:
        length: The length.
    """

    return "".join(random.choices(string.ascii_letters + string.digits, k=length))
