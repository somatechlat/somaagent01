"""Bootstrap the Clef decision-model seam: settings chain + LLMModelConfig row.

Seeds (idempotent, fail-closed):

1. ``InfrastructureConfig`` operator-layer settings used by
   ``services.common.decisions.clef_client`` via ``require_setting``::

       CLEF_BACKEND      = workers_ai
       CLEF_API_BASE     = {CLOUDFLARE_API_BASE}/accounts/{account_id}/ai
       CLEF_ACCOUNT_ID   = from Vault secret/agent/credentials/cloudflare_account_id
       CLEF_MODEL_ID     = @cf/openai/gpt-oss-120b   (Workers AI decision model)
       CLEF_TIMEOUT_MS   = 5000

   ``CLEF_API_BASE`` is derived from the Cloudflare protocol constant plus the
   account id - never a host invented here, never a secret in source.

2. ``LLMModelConfig`` decision row::

       name='clef-decision' model_type='decision' provider='cloudflare'
       api_base=CLEF_API_BASE (from the settings chain)
       capabilities=['decision','score','noul'] priority=95 is_active=True

Usage::

    python manage.py bootstrap_clef
    python manage.py bootstrap_clef --check
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

CLEF_BACKEND = "workers_ai"
CLEF_MODEL_ID = "@cf/openai/gpt-oss-120b"
CLEF_TIMEOUT_MS = "5000"
DECISION_ROW_NAME = "clef-decision"
DECISION_CAPABILITIES = ["decision", "score", "noul"]
DECISION_PRIORITY = 95


def _vault_credential(key: str) -> str | None:
    from services.common.unified_secret_manager import get_secret_manager

    value = get_secret_manager().get_credential(key)
    if value and str(value).strip() and str(value) not in ("None", "NA"):
        return str(value).strip()
    return None


def _upsert_infra_setting(key: str, value: str) -> bool:
    """One InfrastructureConfig row under the clef service entity."""
    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    service, _ = ServiceHealth.objects.get_or_create(
        service_name="clef",
        defaults={
            "display_name": "Cloudflare Clef",
            "category": "integration",
            "status": "unknown",
        },
    )
    row, created = InfrastructureConfig.objects.get_or_create(
        service=service,
        key=key,
        defaults={
            "value": value,
            "is_secret": False,
            "is_editable": True,
            "description": f"Clef decision seam - {key}",
        },
    )
    if not created and row.value != value:
        if not row.is_editable:
            raise CommandError(f"{key} is not editable at runtime")
        row.value = value
        row.save(update_fields=["value"])
        return True
    return created


def _ensure_decision_row(api_base: str) -> None:
    from admin.llm.models import LLMModelConfig

    defaults = {
        "display_name": "Clef Decision (Workers AI)",
        "model_type": "decision",
        "provider": "cloudflare",
        "api_base": api_base,
        "capabilities": list(DECISION_CAPABILITIES),
        "priority": DECISION_PRIORITY,
        "cost_tier": "low",
        "is_active": True,
    }
    LLMModelConfig.objects.update_or_create(name=DECISION_ROW_NAME, defaults=defaults)


class Command(BaseCommand):
    """Seed Clef settings + the decision LLMModelConfig row. Never prints secrets."""

    help = (
        "Seed CLEF_* into the settings chain (InfrastructureConfig) and upsert "
        "the clef-decision LLMModelConfig row. Values never printed."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--check",
            action="store_true",
            help="report what would be seeded; change nothing",
        )

    def handle(self, *args, **options) -> None:
        check = bool(options.get("check"))

        account_id = _vault_credential("cloudflare_account_id")
        if not account_id:
            raise CommandError(
                "cloudflare_account_id missing from Vault "
                "(secret/agent/credentials/cloudflare_account_id). "
                "Run infra/standalone/seed_clef_vault.py first."
            )

        from admin.core.helpers.vendor_api_bases import CLOUDFLARE_API_BASE

        api_base = f"{CLOUDFLARE_API_BASE}/accounts/{account_id}/ai"

        settings_rows = {
            "CLEF_BACKEND": CLEF_BACKEND,
            "CLEF_API_BASE": api_base,
            "CLEF_ACCOUNT_ID": account_id,
            "CLEF_MODEL_ID": CLEF_MODEL_ID,
            "CLEF_TIMEOUT_MS": CLEF_TIMEOUT_MS,
        }

        if check:
            for key in settings_rows:
                self.stdout.write(f"would seed InfrastructureConfig[{key}]")
            self.stdout.write(
                f"would upsert LLMModelConfig[{DECISION_ROW_NAME}] "
                f"model_type=decision api_base=<from settings>"
            )
            return

        for key, value in settings_rows.items():
            created = _upsert_infra_setting(key, value)
            state = "created" if created else "updated/present"
            self.stdout.write(f"   ok InfrastructureConfig[{key}] {state}")

        _ensure_decision_row(api_base)
        self.stdout.write(
            f"   ok LLMModelConfig[{DECISION_ROW_NAME}] "
            f"model_type=decision provider=cloudflare priority={DECISION_PRIORITY}"
        )
        self.stdout.write(self.style.SUCCESS("Clef decision seam ready."))
