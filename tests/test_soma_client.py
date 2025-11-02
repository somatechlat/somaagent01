from python.integrations import soma_client


def test_sanitize_rewrites_legacy_port_only():
    sanitized = soma_client._sanitize_legacy_base_url("http://localhost:9595")
    assert sanitized == "http://localhost:9696"


def test_sanitize_keeps_valid_endpoint():
    target = "http://localhost:9696"
    assert soma_client._sanitize_legacy_base_url(target) == target
