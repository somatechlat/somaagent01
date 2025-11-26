import pytest


def pytest_collection_modifyitems(config, items):
    """Add the ``ci`` marker to every collected test.

    The ``pytest.ini`` file sets ``addopts = -m ci`` so only items with this
    marker are executed when the CI suite runs. By attaching the marker here we
    avoid having to modify each individual test file.
    """
    for item in items:
        item.add_marker(pytest.mark.ci)
