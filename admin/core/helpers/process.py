"""Module process."""

import os
import sys

from admin.core.helpers import runtime
from admin.core.helpers.print_style import PrintStyle

_server = None


def set_server(server):
    """Set server.

    Args:
        server: The server.
    """

    global _server
    _server = server


def get_server(server):
    """Retrieve server.

    Args:
        server: The server.
    """

    global _server
    return _server


def stop_server():
    """Execute stop server."""

    global _server
    if _server:
        _server.shutdown()
        _server = None


def reload():
    """Execute reload."""

    stop_server()
    if runtime.is_dockerized():
        exit_process()
    else:
        restart_process()


def restart_process():
    """Execute restart process."""

    PrintStyle.standard("Restarting process...")
    python = sys.executable
    os.execv(python, [python] + sys.argv)


def exit_process():
    """Execute exit process."""

    PrintStyle.standard("Exiting process...")
    sys.exit(0)
