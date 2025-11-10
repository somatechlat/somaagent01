import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def test_scheduler_no_polling_interval():
    path = os.path.join(ROOT, "webui", "js", "scheduler.js")
    src = read(path)
    assert "setInterval(" not in src, "scheduler.js should not use setInterval"
    assert "startPolling" not in src, "remove legacy startPolling stub"
    assert "stopPolling" not in src, "remove legacy stopPolling stub"


def test_health_banner_no_polling_interval():
    path = os.path.join(ROOT, "webui", "components", "health-banner.js")
    src = read(path)
    assert "setInterval(" not in src, "health-banner should not use setInterval"
    assert "healthCheckInterval" not in src, "healthCheckInterval state should be removed"
