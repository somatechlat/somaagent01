# SOMA-01-STD-001 — Standards Register — Normative and Applied External Standards

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Standards Register — Normative and Applied External Standards |
| Document Identifier | SOMA-01-STD-001 |
| Version | 1.0.1 |
| Date | 2026-09-30 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 clause 7.5 — Control of documented information; ISO/IEC 27001:2022 — Information security management systems; ISO/IEC 42001:2023 — Artificial intelligence management systems |
| Next Review | 2027-03-30 |
| Related | SOMA-01-QMS-001; SOMA-01-DOCS-001; SOMA-01-SEC-001; SOMA-01-RISK-001; SOMA-01-DEPLOY-001; SOMA-01-SDP-001; SOMA-SETTINGS-MODEL-001 |
| Source of truth | This document. Citation defects are reported here; the citing document owns the correction. |
| Audience | Auditors, security engineering, platform engineering, documentation owners |
| Scope | Every external standard, framework and technical specification the somaAgent01 suite cites or implements. Not a certification claim. |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-09-30 | SomaTech Engineering | First issue. Inventory of every external standard cited across `docs/` or implemented in code, organised by standards body. Records six citation defects. |
| 1.0.1 | 2026-09-30 | SomaTech Engineering | §4.4 records the settled transport contract: UDS socket paths, one `.proto` on both carriers, mode dispatch with no probe. D-6 moves from "uncited" to "slot reserved". |

---

## Normative References

| ID | Reference | Role |
|----|-----------|------|
| N-1 | `SOMA-01-DOCS-001` | Document Control and Traceability Procedure; rules C-01…C-12 govern this document |
| N-2 | `SOMA-01-QMS-001` | Quality Manual; §7 Document Reference Matrix is the suite registry |
| N-3 | `SOMA-01-SDP-001` | Software Development Plan; §Engineering standards table |
| N-4 | `SOMA-01-SEC-001` | Security Assessment; §2 ISO 27001 Annex A control mapping |
| N-5 | `SOMA-SETTINGS-MODEL-001` | Settings Model; cites ISO/IEC 27001:2022 A.8.9 and ISO/IEC 25010 |
| N-6 | REQ-DOCS-011 | Evidence claims must cite `file:line` |

---

## 1. Purpose and Scope

### 1.1 Purpose

This register is the single place where the suite's relationship to **external** standards is
stated. Until now each document stamped its own `ISO Reference` front-matter field and nothing
checked those stamps against each other or against the code. The result is a body of citation
that is partly real mapping and partly boilerplate.

This document does three things:

1. **Finds** every external standard cited anywhere in `docs/`, and every standard the code
   actually implements.
2. **Saves** them in one register, organised by standards body and by standard number.
3. **Records the defects** — six of them (§5) — so a citation can be trusted or corrected.

It is **not** a certification. Nothing here claims somaAgent01 is certified to any standard.
Where a standard is used only as a lens, the table says so.

### 1.2 In scope

- ISO and ISO/IEC standards cited in the document suite.
- Non-ISO technical specifications the code implements (NIST, RFC, OWASP).
- Regulatory frameworks referenced in risk or scope language.
- Citation hygiene: designation form, clause mapping, and standards followed in code but
  absent from documentation.

### 1.3 Out of scope

- Certification, attestation, or audit-readiness claims of any kind.
- Standards internal to the suite — those are `docs/standards/SOMA-STD-*`.
- The product requirements themselves — `SOMA-01-SRS-001` and `docs/requirements/*`.
- SomaAgent Hub, SomaBrain and SomaFractalMemory as separate products; only the seam
  standards that cross that boundary are listed.

### 1.4 Audience

Auditors verifying what the suite claims to follow; security and platform engineering choosing
what to implement next; documentation owners correcting citation.

---

## 2. Conformance vocabulary

Three words are used strictly. Misusing them is what makes a register untrustworthy.

| Term | Meaning | What it entitles |
|------|---------|------------------|
| **Normative** | The suite treats the standard as binding. A deviation is a defect. | Cite clause numbers. Map controls. |
| **Applied** | A specific provision of the standard is implemented in code. Only that provision binds. | Cite `file:line`. Do not claim whole-standard conformance. |
| **Lens** | The standard's vocabulary organises our thinking. Nothing is certified against it. | Cite as a checklist. Never as a requirement. |

**No entry in this register is a certification claim.** The strongest statement the suite may
make is *"we apply provision X of standard Y, evidenced at `file:line`"*.

---

## 3. Register — organised by standards body

### 3.1 ISO/IEC JTC 1 — Information technology

#### 3.1.1 ISO/IEC 27001:2022 — Information security management systems — Requirements

| Field | Value |
|-------|-------|
| Designation | ISO/IEC 27001:2022 |
| Status in this suite | **Normative** (management-system level) |
| Clause coverage | Annex A control families, mapped in `SOMA-01-SEC-001` §2 |
| Cited at | `docs/iso/SOMA-01-DEPLOY-001.md:15`, `:42`; `docs/iso/SOMA-01-SEC-001.md:15`, `:26`, `:32`, `:38`; `docs/iso/SOMA-SETTINGS-MODEL-001.md:15`, `:37`; `docs/iso/SOMA-01-QMS-001.md:225` |
| Also appears as | `ISO 27001` (bare) at `docs/iso/SOMA-01-SDP-001.md:83`, `docs/iso/SOMA-01-QMS-001.md:225` — **defect D-2** |
| Controls applied in code | A.8.9 configuration management (settings inventory); A.5.15 access control (`admin/core/authz.py`); A.5.17 authentication information (`services/common/identity/`); A.8.24 cryptography (argon2id + HMAC pepper) |
| Note | The security assessment claims "the system demonstrates" against Annex A. That is a self-assessment, not an audit. |

#### 3.1.2 ISO/IEC 27002:2022 — Information security controls — Guidance

| Field | Value |
|-------|-------|
| Designation | ISO/IEC 27002:2022 |
| Status in this suite | **Applied** — guidance for the Annex A mapping above |
| Cited at | `docs/iso/SOMA-01-DEPLOY-001.md:43` |
| Clause coverage | Referenced as guidance only; no clause-level mapping exists |
| Note | One citation in the whole suite. If Annex A is normative, its guidance document deserves at least a control-family map. |

#### 3.1.3 ISO/IEC 42001:2023 — Artificial intelligence management system — Requirements

| Field | Value |
|-------|-------|
| Designation | ISO/IEC 42001:2023 |
| Status in this suite | **Normative** (AI management-system level) |
| Cited at | `docs/iso/SOMA-01-DEPLOY-001.md:15`, `:44`; `docs/iso/SOMA-01-QMS-001.md:245` |
| Clause coverage | None mapped. Cited as a conformance target only. |
| Related code | Neuromodulator/cognitive controls (`admin/core/chat_orchestrator.py`), asset critic gate (`services/common/asset_critic.py`) — the AIMS-relevant surfaces |
| Note | Named as a conformance target in the deployment specification but no annex or clause of 42001 is mapped anywhere in the suite. **Defect D-4.** |

#### 3.1.4 ISO/IEC 25010 — Systems and software Quality Requirements and Evaluation (SQuaRE)

| Field | Value |
|-------|-------|
| Designation | ISO/IEC 25010 |
| Status in this suite | **Lens** — explicitly not certification |
| Editions cited | `:2018` at `docs/iso/SOMA-SETTINGS-MODEL-001.md:38`; `:2023` at `docs/requirements/SOMA-SRS-ARCHPATTERNS-001.md:101`; bare `ISO/IEC 25010` at `docs/iso/SOMA-A0-PARITY-001.md:99`, `docs/iso/SOMA-SETTINGS-MODEL-001.md:15` |
| Disposition | `SOMA-SETTINGS-MODEL-001.md:38` is explicit and correct: *"used only as a category lens, not as certification"*. Preserve that phrasing wherever 25010 is cited. |
| Note | Three edition spellings for one standard. **Defect D-3.** |

#### 3.1.5 ISO/IEC 12207:2017 — Software life cycle processes

| Field | Value |
|-------|-------|
| Designation | ISO/IEC 12207:2017 |
| Status in this suite | **Applied** — process framework for the lifecycle plan |
| Cited at | `docs/iso/SOMA-01-SDP-001.md:15`, `:30`; `docs/iso/SOMA-01-QMS-001.md:240` |
| Clause coverage | Lifecycle process families named in the SDP; no clause-level traceability |

#### 3.1.6 ISO/IEC/IEEE 42010 — Architecture description

| Field | Value |
|-------|-------|
| Designation | ISO/IEC/IEEE 42010 |
| Status in this suite | **Lens** — view vocabulary for architecture description |
| Cited at | `docs/iso/SOMA-01-SDP-001.md:82`; `docs/iso/SOMA-01-QMS-001.md:221` |
| Note | Cited without a year. **Defect D-2.** The current edition is 2022. |

### 3.2 ISO/TC 176 — Quality management, quality assurance and statistics

#### 3.2.1 ISO 9001:2015 — Quality management systems — Requirements

| Field | Value |
|-------|-------|
| Designation | ISO 9001:2015 |
| Status in this suite | **Normative** at management-system level; **boilerplate** in most front-matter |
| Citations | **109** front-matter `ISO Reference` stamps across `docs/` |
| Clause coverage | Clause 7.5 (Control of documented information) is the only clause mapped anywhere — `SOMA-01-DOCS-001.md:34`, `SOMA-01-QMS-001.md:229-238`, `SOMA-01-UIUX-*.md` Normative References |
| Disposition | Clause 7.5 is genuinely applied: `scripts/check_docs.py` implements C-01…C-12, `make docs-register`, `make docs-check`. That is real. |
| Note | The other 100+ stamps carry no clause and no mapping. They assert a relationship the suite has not established. **Defect D-1.** |

### 3.3 ISO/TC 159/SC 4 — Ergonomics of human-system interaction

#### 3.3.1 ISO 9241-210 — Human-centred design for interactive systems

| Field | Value |
|-------|-------|
| Designation | ISO 9241-210 |
| Status in this suite | **Lens** — HCD process vocabulary for the UI/UX suite |
| Cited at | `docs/iso/SOMA-A0-PARITY-001.md:98` |
| Note | Cited without an edition year. **Defect D-2.** |

### 3.4 ISO/TC 262 — Risk management

#### 3.4.1 ISO 31000 — Risk management — Guidelines

| Field | Value |
|-------|-------|
| Designation | ISO 31000 |
| Status in this suite | **Applied** — the risk register is structured on it |
| Cited at | `docs/iso/SOMA-01-RISK-001.md:15`; `docs/iso/SOMA-01-QMS-001.md:226` |
| Note | Cited without edition (2018 is current). **Defect D-2.** |

### 3.5 ISO/TC 176 — Auditing

#### 3.5.1 ISO 19011 — Guidelines for auditing management systems

| Field | Value |
|-------|-------|
| Designation | ISO 19011 |
| Status in this suite | **Applied** — audit-report method |
| Cited at | `docs/iso/SOMA-01-QMS-001.md:224` |
| Note | Single citation, no edition year. **Defect D-2.** |

---

## 4. Non-ISO standards the code actually implements

These bind in code but are under-recorded in documentation. They are listed here because a
register that only lists what documents *claim* is not a register of what the product *does*.

### 4.1 NIST

| Standard | Status | Implemented at | Cited in docs | Disposition |
|----------|--------|----------------|---------------|-------------|
| **NIST SP 800-63B** — Digital Identity Guidelines, Authentication and Lifecycle Management | **Applied** — password policy is length-first, no composition rules, no forced rotation | `services/common/identity/password.py:17` (`"Policy is length-first (NIST SP 800-63B)"`), `:12` `MIN_PASSWORD_LENGTH = 12`, `:13` `PRIVILEGED_MIN_PASSWORD_LENGTH = 14`, `:14` `MAX_PASSWORD_LENGTH = 128` | **Nowhere** | **Defect D-5.** A standard we follow and never record. Cite it in `SOMA-01-SEC-001` and in the identity specification. |

Related, applied but likewise uncited: the session model uses opaque tokens with idle and
absolute timeouts (`services/common/identity/session.py:21-26`), which is the SP 800-63B
session-binding posture. No NIST document is cited for it.

### 4.2 IETF RFC

| Standard | Status | Implemented at | Cited in docs | Disposition |
|----------|--------|----------------|---------------|-------------|
| **RFC 8785** — JSON Canonicalization Scheme (JCS) | **Applied** — deterministic signature payload | `services/registry_service.py:10` (`"JCS (RFC 8785) Normalization"`), `:167-168` | **Nowhere** | **Defect D-5.** |
| **RFC 8032** — Edwards-Curve Digital Signature Algorithm | Applied — Ed25519 signatures | registry signing path | `docs/` once | Adequate |
| **RFC 5322** — Internet Message Format | Applied — email address validation | identity/profile validation | `docs/` once | Adequate |
| **RFC 9113** — HTTP/2 | Applied — transport substrate for gRPC | all gRPC paths | **Nowhere** | See §4.4 |
| **RFC 8446** — TLS 1.3 | Applied — transport security for distributed hops | `services/common/spicedb_client.py:171-176`, Vault client | **Nowhere** | See §4.4 |
| **RFC 5280** — X.509 PKI | Applied — certificate validation on mTLS hops | same | **Nowhere** | See §4.4 |

### 4.3 OWASP

| Reference | Status | Implemented at | Disposition |
|-----------|--------|----------------|-------------|
| OWASP Password Storage Cheat Sheet — argon2id as first choice | **Applied** | `services/common/identity/password.py:5` (`"argon2id. Memory-hard, the OWASP first choice"`); parameters at `:26-30` (m=64 MiB, t=3, p=4) | Cite as **Applied**, not normative. OWASP guidance is not an ISO standard and must never be listed as one. |

### 4.4 Transport standards — applied, entirely uncited

The memory lane and its neighbours use the following. **No document in the suite names any of
them.** This is the largest single hole in the register, and it is live: the transport layer is
under active specification.

| Hop | Protocol | Standards it rests on | Where |
|-----|----------|----------------------|-------|
| Telemetry export | OTLP over gRPC | RFC 9113 (HTTP/2), gRPC wire format | `services/common/tracing.py:3`, `:12` |
| Authorization (SpiceDB) | gRPC, TLS-secured | RFC 9113, RFC 8446, RFC 5280 | `services/common/spicedb_client.py:146-176` |
| Agent ↔ SomaBrain | HTTP/1.1 + JSON today; gRPC under design | RFC 9110, RFC 9113 | `admin/core/somabrain_client.py:24`, `:169` |
| Policy (OPA) | HTTP/1.1 | RFC 9110 | `services/common/policy_client.py` |
| Events | Kafka wire protocol | Apache Kafka protocol | `services/common/trace_context.py:1` |

**The transport contract (settled 2026-09-30).** These three decisions govern every hop
above. They are architecture decisions, recorded here so the register and the implementation
cannot drift apart.

| # | Decision | Value |
|---|----------|-------|
| TC-1 | **Local socket layout** | One directory `/run/soma/`, not one per service. Sockets at `/run/soma/brain.sock` (Agent ↔ SomaBrain) and `/run/soma/sfm.sock` (SomaBrain ↔ SFM). Mode `0600`, owned by the service uid, never world-writable. Compose bind-mounts a single volume. |
| TC-2 | **One `.proto`, two carriers** | The same `brain.proto` and the same protobuf messages on UDS and on TCP. UDS removes the TCP, TLS and bearer layers; it does not change the message. A lighter local framing would be a second schema, and a second schema is the divergence this contract exists to prevent. |
| TC-3 | **Mode dispatch, never a probe** | `SA01_DEPLOYMENT_MODE` selects the topology from the settings registry; the registry constructs the adapter and its address. No runtime discovery, no "try UDS then fall back to TCP". A probe is a silent fallback under another name. If the configured transport cannot connect, the call fails and names the endpoint it was configured for. |

**Why UDS is the single-node answer.** On one machine a Unix domain socket removes the TCP
three-way handshake, `TIME_WAIT` accumulation and the TLS handshake entirely, and it removes the
bearer from the wire: file mode `0600` plus uid ownership replaces network authentication with
kernel access control, which is both cheaper and stronger. gRPC multiplexes HTTP/2 streams over
that one socket and protobuf is binary, so the same contract is two to five times faster locally
than HTTP/1.1 with JSON over loopback.

**Disposition.** Each hop has a permanent home in `SOMA-01-SEC-001` (transport security) and
`SOMA-01-ARCH-001` (transport architecture). **D-6 slot is reserved in `SOMA-01-ARCH-001`**;
the exact normative citations (RFC 9113 HTTP/2, RFC 8446 TLS 1.3, RFC 5280 X.509, and the UDS
security model) are to be supplied by the transport implementer rather than invented here.
Until they land, the standards are recorded in this register so the suite can see what it
depends on.

---

## 5. Citation defects

Found by cross-reading every citation against every other. Each has an owner and a fix.

| ID | Defect | Evidence | Fix | Owner |
|----|--------|----------|-----|-------|
| **D-1** | **Boilerplate conformance stamp.** 109 front-matter fields assert `ISO 9001:2015` with no clause mapping. Only clause 7.5 is actually mapped. | `grep -rc 'ISO 9001:2015' docs/**` → 109; clause mapping exists only at `SOMA-01-DOCS-001.md:34`, `SOMA-01-QMS-001.md:229-238` | Two options: (a) map the clause each document actually satisfies, or (b) demote the stamp to `ISO 9001:2015 clause 7.5` where that is all that applies. Prefer (b) — it is honest and cheap. | Documentation owners |
| **D-2** | **Incomplete designation.** Standards cited without a year, or under an obsolete short form. | `ISO 27001` bare at `SOMA-01-SDP-001.md:83`, `SOMA-01-QMS-001.md:225`; `ISO/IEC 42010` bare at `SOMA-01-SDP-001.md:82`, `SOMA-01-QMS-001.md:221`; `ISO 31000` bare at `SOMA-01-RISK-001.md:15`; `ISO 19011` bare at `SOMA-01-QMS-001.md:224`; `ISO 9241-210` bare at `SOMA-A0-PARITY-001.md:98` | Cite in full: `ISO/IEC 27001:2022`, `ISO/IEC/IEEE 42010:2022`, `ISO 31000:2018`, `ISO 19011:2018`, `ISO 9241-210:2019`. | Documentation owners |
| **D-3** | **Edition drift.** One standard cited under three editions. | `ISO/IEC 25010` bare, `:2018` (`SOMA-SETTINGS-MODEL-001.md:38`), `:2023` (`SOMA-SRS-ARCHPATTERNS-001.md:101`) | Pin to `ISO/IEC 25010:2023` and keep the "lens, not certification" qualifier. | Documentation owners |
| **D-4** | **Unmapped conformance target.** ISO/IEC 42001:2023 is named as a conformance target and no clause of it is mapped anywhere. | `SOMA-01-DEPLOY-001.md:15`, `:44`; zero clause references suite-wide | Either map the applicable clauses (AI risk, AI impact, data quality, human oversight) or demote 42001 to a stated *objective* rather than a *target*. | Security + documentation |
| **D-5** | **Implemented but never cited.** NIST SP 800-63B and RFC 8785 are binding in code and appear in no document. | `services/common/identity/password.py:17`; `services/registry_service.py:10` | Cite both here (done) and in `SOMA-01-SEC-001` §2 alongside the ISO 27001 Annex A map. | Security |
| **D-6** | **Transport standards not yet normatively cited.** gRPC, HTTP/2, TLS 1.3, X.509 are all in the runtime; no document names them as requirements. Contract decisions TC-1…TC-3 are now recorded in §4.4. | `services/common/tracing.py:12`; `services/common/spicedb_client.py:146-176`; `admin/core/somabrain_client.py:24` | **Slot reserved** in `SOMA-01-ARCH-001`. Citations to be supplied by the transport implementer — RFC 9113, RFC 8446, RFC 5280, plus the UDS file-mode security model. Do not invent them here. | Architecture (contract: this register) |

---

## 6. Organising principle — where each standard permanently lives

This register is the **index**. It is not the place a standard is applied. Each standard has one
home where its clauses are mapped, so a reader always knows where to look and an auditor never
hunts.

| Standard | Home document | What lives there |
|----------|---------------|------------------|
| ISO/IEC 27001:2022 Annex A | `SOMA-01-SEC-001` §2 | Control-by-control mapping |
| ISO/IEC 27002:2022 | `SOMA-01-SEC-001` §2 | Guidance alongside each control |
| ISO/IEC 42001:2023 | `SOMA-01-SEC-001` §2b *(to be created — D-4)* | AIMS clause mapping |
| ISO 9001:2015 clause 7.5 | `SOMA-01-DOCS-001` | Document control rules C-01…C-12 |
| ISO/IEC 12207:2017 | `SOMA-01-SDP-001` | Lifecycle process mapping |
| ISO/IEC/IEEE 42010:2022 | `SOMA-01-ARCH-001` | View catalogue |
| ISO/IEC 25010:2023 | `SOMA-A0-PARITY-001`, `SOMA-SETTINGS-MODEL-001` | Quality lens only |
| ISO 9241-210:2019 | `SOMA-01-UIUX-004` | HCD evidence |
| ISO 31000:2018 | `SOMA-01-RISK-001` | Risk method |
| ISO 19011:2018 | `SOMA-01-AUDIT-002` | Audit method |
| NIST SP 800-63B | `SOMA-01-SEC-001` *(D-5)* + `services/common/identity/` | Credential policy |
| RFC 8785, RFC 8032 | `services/registry_service.py` + `SOMA-01-SEC-001` | Signature canonicalisation |
| Transport stack (RFC 9113, 8446, 5280, 9110) | `SOMA-01-ARCH-001` *(D-6)* | Transport architecture |

---

## 7. Regulatory frameworks referenced

Not standards. Listed so they are not mistaken for normative references.

| Framework | Where referenced | Nature of the reference |
|-----------|------------------|-------------------------|
| GDPR | `docs/iso/SOMA-01-RISK-001.md:86` | Named as an unaddressed compliance risk (`R-018`) |
| CCPA | `docs/iso/SOMA-01-RISK-001.md:86` | Same risk entry |
| SOC 2 | `docs/requirements/SOMA-SRS-MULTITENANCY-001.md:80` | Named as a certification the product does **not** hold |
| HIPAA | `docs/requirements/SOMA-SRS-MULTITENANCY-001.md:80` | Same — explicitly not claimed |

**Rule:** these four must never appear in an `ISO Reference` field. They are legal regimes, not
ISO standards, and citing them as conformance targets would be a false claim.

---

## 8. Traceability

| Req | Statement | Evidence |
|-----|-----------|----------|
| REQ-STD-001 | Every external standard cited or implemented is registered here | §3, §4 |
| REQ-STD-002 | Each standard carries a conformance vocabulary term: Normative / Applied / Lens | §2, applied in every §3 entry |
| REQ-STD-003 | A standard used only as a lens is never presented as a certification | §2; `SOMA-SETTINGS-MODEL-001.md:38` preserved |
| REQ-STD-004 | Citation defects are recorded with evidence and an owner | §5 D-1…D-6 |
| REQ-STD-005 | Each standard has exactly one home document for clause mapping | §6 |
| REQ-STD-006 | Standards implemented in code but absent from documentation are registered | §4.1 NIST SP 800-63B, §4.2 RFC 8785 |
| REQ-STD-007 | Regulatory frameworks are listed separately and never in `ISO Reference` | §7 |
| REQ-STD-008 | No entry claims certification | §2, §1.1 |

---

## 9. Verification

| # | Check | Method |
|---|-------|--------|
| V-01 | Register is complete against `docs/` | `grep -rhoE 'ISO(/IEC)?[ -/A-Za-z0-9]*[0-9]{4,5}[^ ,;.)|]*' docs/` compared to §3 |
| V-02 | Register is complete against code | `grep -rniE 'NIST|RFC [0-9]{3,4}|OWASP|FIPS' services/ admin/ config/` compared to §4 |
| V-03 | Every defect has evidence | §5 rows cite `file:line` per REQ-DOCS-011 |
| V-04 | No certification claim | `grep -niE 'certified|certification|compliant with ISO' docs/iso/SOMA-01-STD-001.md` returns only negations |
| V-05 | Document control is valid | `make docs-check` exits 0 |
| V-06 | Register and QMS §7 agree | C-10 check inside `make docs-check` |

---

## 10. Change control

Adding a standard is a controlled change to this document: bump `Version`, add a
`## Revision History` row, and cite the evidence. Adding a clause mapping belongs in the home
document from §6, not here.

Removing a standard is permitted only when no code implements it and no document cites it.

---

End of Document
