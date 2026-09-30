"""Seam-proof end-to-end: one chat turn → memory in BOTH stores → next-turn recall.

Proves the Wave 1 exit criteria of SOMA-PM-PLAN-TRIAD-001.md §1 ("THE SEAM")
against REAL services (no mocks of production code):

  STEP 1  Send a chat turn containing a unique marker through the
          orchestrator's real public entry — V3ChatOrchestrator.process_turn,
          the exact call admin/chat/api/chat.py::send_message makes
          (HTTP equivalent: POST /api/v2/chat/conversations/{id}/messages).
  STEP 2  The marker is retrievable from SomaFractalMemory via
          POST {SFM_URL}/memories/search (the live /memories* API).
  STEP 3  The marker is retrievable from SomaBrain via its recall
          POST {SOMABRAIN_URL}/memory/recall.
  STEP 4  A second turn's built context (memory lane) contains the marker —
          captured by wrapping admin.core.chat_orchestrator.build_context with
          a recorder that calls the real builder (instrumentation only, not a
          mock) because ChatResult does not expose BuiltContext.

Run the proof (one command):

    pytest tests/e2e/test_triad_integration.py -v

Environment — URLs are discovered from env ONLY by the ``seam_stack``
fixture; no port is hardcoded anywhere in this file:

    SOMABRAIN_URL                 base URL of the live SomaBrain
    SFM_URL                       base URL of the live SomaFractalMemory
                                  (alias SOMAFRACTALMEMORY_URL)

Optional:

    SOMA_API_TOKEN / SOMABRAIN_MEMORY_HTTP_TOKEN / SA01_TEST_TOKEN
                                  bearer token sent to the stores
    MEM_EMBED_DIM                 shared embedding dimension (settings.MEM_EMBED_DIM)
    SA01_DB_HOST / SA01_DB_PORT   Postgres for process_turn (probe matches
                                  tests/unit/test_chat_orchestrator.py)

Model credentials are NOT an env contract. A real LLM key must be seeded in
Vault at secret/agent/api_keys/{provider}_api_key via the agent's model
administration (LLMModelConfig + UnifiedSecretManager.set_provider_key).
This suite reads them the same way the runtime does.

Every step skips with an explanatory reason when a dependency is missing.
"""

from __future__ import annotations

import os
import socket
import uuid
from dataclasses import dataclass, field

import httpx
import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Environment discovery — fail closed, no hardcoded ports
# ---------------------------------------------------------------------------

_SFM_URL_ENV = ("SFM_URL", "SOMAFRACTALMEMORY_URL")
_STORE_PROBE_TIMEOUT = 5.0


def _env_url(*names: str) -> str | None:
    """First non-empty env URL among ``names``, normalized (no trailing slash)."""

    for name in names:
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return raw.rstrip("/")
    return None


def _postgres_available() -> bool:
    """True when the Postgres used by process_turn answers a TCP connect."""

    host = os.environ.get("SA01_DB_HOST", "localhost")
    port = int(os.environ.get("SA01_DB_PORT", "63932"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        return False


def _provider_with_key() -> tuple[str, str] | None:
    """Return (provider, model_name) for the first provider Vault holds a key for.

    Model credentials are administered in the agent: LLMModelConfig selects the
    model and UnifiedSecretManager.get_provider_key() reads the key from Vault
    at secret/agent/api_keys/{provider}_api_key. They are NOT environment
    variables — checking os.environ here would test a source of truth the
    runtime never reads.
    """

    from services.common.unified_secret_manager import UnifiedSecretManager

    manager = UnifiedSecretManager()
    # provider -> the model LLMModelConfig should route to it
    candidates = (
        ("groq", "openai/gpt-oss-20b"),
        ("openai", "gpt-4o-mini"),
        ("openrouter", "openai/gpt-4o-mini"),
        ("anthropic", "claude-sonnet-4-5"),
    )
    for provider, model_name in candidates:
        key = manager.get_provider_key(provider)
        if key and key not in ("None", "NA"):
            return provider, model_name
    return None


def _llm_available() -> bool:
    """True when Vault holds a real provider key for at least one LLM provider."""

    return _provider_with_key() is not None


def _store_headers(tenant_id: str | None = None) -> dict[str, str]:
    """Auth/tenant headers for store calls — tokens come from env, never literals."""

    headers: dict[str, str] = {"Accept": "application/json"}
    token = (
        os.environ.get("SOMA_API_TOKEN")
        or os.environ.get("SOMABRAIN_MEMORY_HTTP_TOKEN")
        or os.environ.get("SA01_TEST_TOKEN")
    )
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if tenant_id:
        headers["X-Soma-Tenant"] = tenant_id
        headers["X-Tenant-ID"] = tenant_id
    return headers


@dataclass(frozen=True)
class SeamStack:
    """Live store endpoints discovered from env."""

    somabrain_url: str
    sfm_url: str


def _require_reachable(client: httpx.Client, name: str, base: str, health_paths: list[str]) -> None:
    """Skip with an explanatory reason when the store does not answer at all."""

    errors: list[str] = []
    for path in health_paths:
        try:
            response = client.get(f"{base}{path}", timeout=_STORE_PROBE_TIMEOUT)
            # Any HTTP answer means the process is up; endpoint health is
            # asserted by the seam steps themselves.
            if response.status_code < 500:
                return
            errors.append(f"{path} -> HTTP {response.status_code}")
        except Exception as exc:  # noqa: BLE001 - recorded for the skip reason
            errors.append(f"{path} -> {type(exc).__name__}: {exc}")
    pytest.skip(
        f"{name} at {base} is not reachable — seam stack is down. "
        f"Probe results: {'; '.join(errors) or 'no health endpoint answered'}. "
        "Start the store or point its env URL at the live instance."
    )


@pytest.fixture(scope="session")
def seam_stack() -> SeamStack:
    """Discover SOMABRAIN_URL / SFM_URL from env — never hardcodes ports.

    Skips cleanly with an explanatory reason when a URL is unset or when a
    store does not answer HTTP at all.
    """

    somabrain_url = _env_url("SOMABRAIN_URL")
    sfm_url = _env_url(*_SFM_URL_ENV)
    missing = [
        name
        for name, value in (("SOMABRAIN_URL", somabrain_url), ("SFM_URL", sfm_url))
        if not value
    ]
    if missing:
        pytest.skip(
            "Seam stack env incomplete: set SOMABRAIN_URL and SFM_URL "
            f"(alias SOMAFRACTALMEMORY_URL). Unset: {', '.join(missing)}. "
            "No ports are hardcoded in this suite."
        )

    assert somabrain_url is not None and sfm_url is not None
    stack = SeamStack(somabrain_url=somabrain_url, sfm_url=sfm_url)

    with httpx.Client(headers=_store_headers()) as client:
        _require_reachable(client, "SomaBrain", stack.somabrain_url, ["/health", "/healthz"])
        _require_reachable(client, "SomaFractalMemory", stack.sfm_url, ["/healthz", "/health"])
    return stack


# ---------------------------------------------------------------------------
# Evidence — the four steps run once, asserted by four tests
# ---------------------------------------------------------------------------


@dataclass
class StoreProbe:
    """Raw evidence of one store lookup (never raises; assertion lives in tests)."""

    ok: bool = False
    status_code: int | None = None
    body_text: str = ""
    error: str = ""


@dataclass
class SeamStory:
    """Everything the four steps assert, gathered by running the flow once."""

    marker: str = ""
    tenant_id: str = ""
    turn1_response: str = ""
    turn1_phase_completed: int = 0
    turn1_turn_id: str = ""
    turn1_errors: list[str] = field(default_factory=list)
    sfm_probe: StoreProbe = field(default_factory=StoreProbe)
    brain_probe: StoreProbe = field(default_factory=StoreProbe)
    memory_lane: str = ""
    turn2_response: str = ""
    turn2_phase_completed: int = 0


class AllowingGate:
    """Permissive gate — authz is proven in tests/unit/test_unified_gate.py.

    The seam proof isolates the memory contract (PLAN §1); it is not an
    authorization test. Injecting this keeps the memory path fully real
    (real orchestrator, real LLM, real stores) without requiring OPA/SpiceDB
    policies on the test stack.
    """

    async def check(self, *args, **kwargs) -> bool:
        return True

    async def check_endpoint_permission(self, *args, **kwargs) -> bool:
        return True


def _seed_llm_model() -> None:
    """Ensure the chat pipeline can select a model matching the key in Vault."""

    from admin.llm.models import LLMModelConfig

    resolved = _provider_with_key()
    if resolved is None:
        # Fail loudly rather than seed a model no provider key can serve.
        raise RuntimeError(
            "No LLM provider key in Vault (secret/agent/api_keys/{provider}_api_key). "
            "Seed one via the agent's model administration — model credentials "
            "are not read from the environment."
        )
    provider, name = resolved

    LLMModelConfig.objects.update_or_create(
        name=name,
        defaults={
            "provider": provider,
            "capabilities": ["text"],
            "priority": 80,
            "is_active": True,
        },
    )


def _probe_store(
    base: str,
    path: str,
    body: dict,
    tenant_id: str,
) -> StoreProbe:
    """POST to a store lookup route and capture the outcome without asserting."""

    try:
        response = httpx.post(
            f"{base}{path}",
            json=body,
            headers=_store_headers(tenant_id),
            timeout=10.0,
        )
        return StoreProbe(
            ok=response.status_code == 200,
            status_code=response.status_code,
            body_text=response.text,
        )
    except Exception as exc:  # noqa: BLE001 - recorded as evidence
        return StoreProbe(ok=False, error=f"{type(exc).__name__}: {exc}")


_STORY: SeamStory | None = None


async def _run_story(stack: SeamStack) -> SeamStory:
    """Run turn 1 → probe both stores → run turn 2. Gathers evidence only."""

    import admin.core.chat_orchestrator as orchestrator_module
    from admin.aaas.models import Tenant
    from admin.chat.models import Conversation
    from admin.core.chat_orchestrator import ChatTurn, V3ChatOrchestrator
    from admin.core.models import Capsule

    marker = f"SEAM-{uuid.uuid4().hex}"

    tenant = Tenant.objects.create(
        name="Seam Tenant", slug=f"seam-tenant-{uuid.uuid4().hex[:8]}"
    )
    capsule = Capsule.objects.create(
        name="Seam Capsule",
        tenant=tenant,
        system_prompt="You are a helpful assistant.",
        persona_config={
            "knobs": {
                "intelligence_level": 5,
                "autonomy_level": 5,
                "resource_budget": 0.1,
            }
        },
    )
    conversation = Conversation.objects.create(
        agent_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        title="Seam Proof Conversation",
    )
    _seed_llm_model()

    orchestrator = V3ChatOrchestrator(unified_gate=AllowingGate())

    # STEP 1 — one chat turn carrying the unique marker (real public entry).
    turn1 = ChatTurn(
        capsule=capsule,
        user_id="seam-user",
        tenant_id=str(tenant.id),
        user_message=(
            f"Remember this secret codeword: {marker}. " "Repeat the secret codeword back to me."
        ),
        conversation_id=str(conversation.id),
    )

    # Instrument build_context to observe the memory lane on turn 2: the real
    # builder runs unchanged; only its return value is recorded (ChatResult
    # does not expose BuiltContext).
    captured_contexts: list = []
    original_build_context = orchestrator_module.build_context

    async def _recording_build_context(*args, **kwargs):
        context = await original_build_context(*args, **kwargs)
        captured_contexts.append(context)
        return context

    orchestrator_module.build_context = _recording_build_context
    try:
        result1 = await orchestrator.process_turn(turn1)
    finally:
        orchestrator_module.build_context = original_build_context

    story = SeamStory(
        marker=marker,
        tenant_id=str(tenant.id),
        turn1_response=getattr(result1, "response", "") or "",
        turn1_phase_completed=int(getattr(result1, "phase_completed", 0) or 0),
        turn1_turn_id=str(getattr(result1, "turn_id", "") or ""),
        turn1_errors=list(getattr(result1, "errors", []) or []),
    )

    # STEP 2 — marker in SomaFractalMemory via the live search API.
    story.sfm_probe = _probe_store(
        stack.sfm_url,
        "/memories/search",
        {"query": marker, "top_k": 10, "offset": 0},
        story.tenant_id,
    )

    # STEP 3 — marker in SomaBrain via its recall.
    story.brain_probe = _probe_store(
        stack.somabrain_url,
        "/memory/recall",
        {"query": marker, "top_k": 10},
        story.tenant_id,
    )

    # STEP 4 — a second turn; its built context (memory lane) must recall the marker.
    turn2 = ChatTurn(
        capsule=capsule,
        user_id="seam-user",
        tenant_id=str(tenant.id),
        user_message="What secret codeword did I ask you to remember?",
        conversation_id=str(conversation.id),
    )
    orchestrator_module.build_context = _recording_build_context
    try:
        result2 = await orchestrator.process_turn(turn2)
    finally:
        orchestrator_module.build_context = original_build_context

    story.turn2_response = getattr(result2, "response", "") or ""
    story.turn2_phase_completed = int(getattr(result2, "phase_completed", 0) or 0)
    # The lane of the LAST context built (turn 2's) is the recall evidence.
    if captured_contexts:
        story.memory_lane = getattr(captured_contexts[-1], "memory", "") or ""
    return story


async def _story(stack: SeamStack) -> SeamStory:
    """Run the flow once per session; later steps read the cached evidence."""

    global _STORY
    if _STORY is None:
        _STORY = await _run_story(stack)
    return _STORY


def _marker_in_probe(probe: StoreProbe, marker: str) -> bool:
    """True when the marker appears anywhere in a store's lookup response."""

    return marker in (probe.body_text or "")


# ---------------------------------------------------------------------------
# The four seam steps
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(
    not _llm_available(),
    reason="no LLM provider key in Vault (secret/agent/api_keys/{provider}_api_key)",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_step1_chat_turn_carries_marker_through_public_entry(seam_stack):
    """STEP 1: process_turn (the real chat entry) accepts a marker-carrying turn."""

    story = await _story(seam_stack)

    assert story.marker, "STEP 1: no unique marker was generated for the seam flow"
    assert story.turn1_phase_completed >= 8, (
        "STEP 1: turn 1 did not complete through V3ChatOrchestrator.process_turn "
        f"(phase_completed={story.turn1_phase_completed}, errors={story.turn1_errors})"
    )
    assert story.turn1_turn_id, "STEP 1: no turn_id was returned for the marker turn"


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(
    not _llm_available(),
    reason="no LLM provider key in Vault (secret/agent/api_keys/{provider}_api_key)",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_step2_marker_reachable_in_somafractalmemory(seam_stack):
    """STEP 2: POST /memories/search returns the turn's marker from SFM."""

    story = await _story(seam_stack)
    probe = story.sfm_probe

    assert probe.error == "", f"STEP 2: SFM search call failed: {probe.error}"
    assert probe.status_code == 200, (
        f"STEP 2: SFM POST /memories/search returned HTTP {probe.status_code}: "
        f"{probe.body_text[:500]}"
    )
    assert _marker_in_probe(probe, story.marker), (
        "STEP 2: marker was not found in somafractalmemory via POST /memories/search — "
        "one chat turn must land in BOTH stores (PLAN §1 one write path). "
        f"Marker: {story.marker}. Response: {probe.body_text[:800]}"
    )


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(
    not _llm_available(),
    reason="no LLM provider key in Vault (secret/agent/api_keys/{provider}_api_key)",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_step3_marker_reachable_in_somabrain(seam_stack):
    """STEP 3: the brain's recall returns the turn's marker from SomaBrain."""

    story = await _story(seam_stack)
    probe = story.brain_probe

    assert probe.error == "", f"STEP 3: SomaBrain recall call failed: {probe.error}"
    assert probe.status_code == 200, (
        f"STEP 3: SomaBrain POST /memory/recall returned HTTP {probe.status_code}: "
        f"{probe.body_text[:500]}"
    )
    assert _marker_in_probe(probe, story.marker), (
        "STEP 3: marker was not found in somabrain via its recall — one chat turn "
        "must land in BOTH stores (PLAN §1 one write path). "
        f"Marker: {story.marker}. Response: {probe.body_text[:800]}"
    )


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(
    not _llm_available(),
    reason="no LLM provider key in Vault (secret/agent/api_keys/{provider}_api_key)",
)
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_step4_second_turn_memory_lane_recalls_marker(seam_stack):
    """STEP 4: the second turn's built context (memory lane) recalls the marker."""

    story = await _story(seam_stack)

    assert story.turn2_phase_completed >= 8, (
        "STEP 4: second turn did not complete " f"(phase_completed={story.turn2_phase_completed})"
    )
    assert story.marker in story.memory_lane, (
        "STEP 4: the marker does not appear in the second turn's memory lane — "
        "the one read path must feed MemoryGateway.recall() into BuiltContext.memory. "
        f"Marker: {story.marker}. Memory lane: {story.memory_lane[:800]!r}"
    )
