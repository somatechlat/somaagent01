# VIBE Rule Violations & Architecture Risks (SomaAgent01)

Documented per VIBE Coding Rules. Each entry lists the rule breached, location, and fix applied.

---

## ✅ 2026-03-05 Audit — Full VIBE Compliance Pass

**Auditor**: All 10 VIBE Personas active
**Scope**: Full codebase scan + cross-repo architecture audit
**Method**: grep scans (TODO/FIXME/HACK/NotImplementedError/placeholder) + manual code review

### Fixes Applied in This Session

| File | Violation | Fix |
|------|-----------|-----|
| `admin/auth/mfa.py` | **[CRITICAL — SECURITY]** Hardcoded TOTP secret `JBSWY3DPEHPK3PXP` used for real verification in `verify_mfa`, `validate_mfa_login`, `disable_mfa` | Replaced all 3 with `ServiceUnavailableError` (fail-closed). MFA cannot safely operate without a `MFASetup` DB model. |
| `admin/capsules/api/capsules.py` | Stub endpoint returning `[]` — silent fake data, misleading callers | Replaced with real tenant-scoped `Capsule.objects.filter()` query with pagination and status filter |
| `admin/voice/api.py` L248 | `POST /transcribe/stream` returned a fake JSON redirect pointing to a non-existent WebSocket path | Replaced with `ServiceUnavailableError` (honest fail-closed) |
| `admin/aaas/api/integrations.py` L100 | `# TODO:` comment left inline | Resolved with architectural explanation of why TenantSettings merge is deferred |
| `admin/aaas/api/integrations.py` L187 | `pass` for unknown provider — silently fell through to serve unconfigured data | Replaced with `HttpError(400, ...)` |
| `admin/aaas/api/integrations.py` L349 | Duplicate `return ConnectionTestResult(...)` after a prior `return` — unreachable dead code | Deleted |
| `admin/aaas/models/profiles.py` L228 | `merge_defaults()` was a `pass`-stub with "Placeholder" in docstring | Implemented real deep-merge of `PlatformConfig` global defaults into JSONB pillars (tenant values always win) |
| `admin/aaas/models/profiles.py` L160 | `AdminProfile.save()` docstring placed after first code line (string literal, not Python docstring) | Moved docstring to first statement |
| `admin/aaas/models/profiles.py` L320 | Same misplaced-docstring pattern in `UserPreferences.save()` | Fixed |
| `docs/README.md` | ChromaDB mentioned as valid vector store (VIBE Rule 9: Milvus ONLY) | Removed all ChromaDB references |
| `docs/README.md` | Port 8010 (incorrect) | Corrected to 20020 (API) and 20080 (frontend) per port namespace spec |

---

## ⚠️ Remaining Open Architecture Risks (Design Decision Required)

These require architectural decisions before implementation — code cannot be written without agreement:

| Risk | Location | Recommended Action |
|------|----------|-------------------|
| Chat pipeline duplication (2 remaining pipelines) | `admin/core/chat_orchestrator.py` (WebSocket/REST) vs `admin/core/application/use_cases/conversation/process_message.py` (conversation worker) | Consolidate worker onto V3 orchestrator or formally split responsibilities |
| Model router duplication | `admin/core/model_router.py` is canonical; `services/common/model_router.py` was deleted | Confirm all callers use `admin/core/model_router.py` |
| Context builder duplication | `admin/core/context/builder.py` vs `admin/core/application/use_cases/conversation/build_context.py` | Choose one, delete other |
| AuthZ stack overlap | Keycloak/JWT in `admin/common/auth.py`, SpiceDB client | Decide single authoritative auth path, deprecate duplicates |
| MFA DB model missing | `admin/auth/mfa.py` | Implement `MFASetup` model with encrypted secret storage before MFA endpoints can go live |

---

## ✅ Fixed in Prior Sessions (Rule 1, 4)

- `admin/core/chat_orchestrator.py` — Placeholder LLM call replaced with real `litellm.acompletion` invocation; fails closed on errors.

- `admin/multimodal/execution.py` — Placeholder multimodal outputs replaced with fail-closed `ServiceUnavailableError`.
- `admin/core/api/__init__.py` — Lingering TODO for API keys router removed.
- `admin/a2a/api.py` — Placeholder tool execution removed; fails closed when not configured.
- `admin/auth/mfa.py` — QR generation now requires `qrcode`; raises `ServiceUnavailableError` if absent.
- `admin/core/budget/gate.py` — TODO removed; fail-closed behavior documented.
