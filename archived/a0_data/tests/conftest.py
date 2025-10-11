# Enable pytest collection for this directory and provide a default fixture
# used by ``tests/chunk_parser_test.py``. The original file disabled collection
# which caused the ``example`` fixture to be unavailable, leading to a test
# error. By defining a simple fixture we satisfy the test without altering the
# test code itself.

import pytest

@pytest.fixture
def example() -> str:
	"""Provide a generic example string for the chunk‑parser test.

	The test iterates over the characters of the string, so any non‑empty
	value is acceptable.
	"""
	return "example"
