import pathlib

ALLOWED = {
    # bootstrap/settings and facade
    "services/common/runtime_config.py",
    "services/common/settings_base.py",
    # Legacy modules that still use direct getenv – temporarily allowed until refactored
    "services/common/attachments_store.py",
    "services/common/audit_store.py",
    "services/common/budget_manager.py",
    "services/common/delegation_store.py",
    "services/common/dlq_store.py",
    "services/common/event_bus.py",
    "services/common/export_job_store.py",
    "services/common/idempotency.py",
    "services/common/llm_credentials_store.py",
    "services/common/logging_config.py",
    "services/common/memory_replica_store.py",
    "services/common/memory_write_outbox.py",
    "services/common/model_profiles.py",
    "services/common/openfga_client.py",
    "services/common/outbox_repository.py",
    "services/common/policy_client.py",
    "services/common/publisher.py",
    "services/common/requeue_store.py",
    "services/common/router_client.py",
    "services/common/secret_manager.py",
    "services/common/session_repository.py",
    "services/common/settings_sa01.py",
    "services/common/slm_client.py",
    "services/common/telemetry_store.py",
    "services/common/tenant_config.py",
    "services/common/tool_catalog.py",
    "services/common/ui_settings_store.py",
    "services/common/vault_secrets.py",
    "services/conversation_worker/main.py",
    "services/conversation_worker/policy_integration.py",
    "services/delegation_gateway/main.py",
    "services/delegation_worker/main.py",
    "services/gateway/main.py",
    "services/memory_replicator/main.py",
    "services/memory_sync/main.py",
    "services/outbox_sync/main.py",
    "services/tool_executor/execution_engine.py",
    "services/tool_executor/main.py",
    "services/tool_executor/resource_manager.py",
    "services/tool_executor/tools.py",
    # tests and scripts are excluded by path checks below
}


def test_no_direct_getenv_outside_allowed():
    repo = pathlib.Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for path in repo.rglob("*.py"):
        rel = path.relative_to(repo).as_posix()
        if rel.startswith("tests/") or rel.startswith("scripts/") or rel.startswith("python/"):
            continue
        if not rel.startswith("services/"):
            continue
        if rel in ALLOWED:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "os.getenv(" in text or "os.environ[" in text:
            offenders.append(rel)
    assert not offenders, f"Direct getenv usage in: {', '.join(sorted(set(offenders)))}"
