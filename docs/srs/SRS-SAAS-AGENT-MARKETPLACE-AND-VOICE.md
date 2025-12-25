# SRS: Eye of God — Agent Marketplace & Voice Studio

**Document ID:** SA01-SRS-AGENT-MARKETPLACE-2025-12
**Persona:** 🔴 SAAS SysAdmin (God Mode)
**Focus:** The Commercial Engine & Creative Studio
**Status:** CANONICAL DESIGN

---

## 1. The Marketplace Philosophy

The **Agent Marketplace** is the engine of value exchange. It allows:
1.  **SysAdmins** to publish "Golden Templates" (e.g., "HR Assistant Pro").
2.  **Developers** to monetize their highly tuned agents.
3.  **Tenants** to rapidly onboard capabilities without prompting from scratch.

---

## 2. Core Modules

### 2.1 🏪 The Agent Store (`/saas/marketplace`)

**Route:** `/saas/marketplace` (Public View) / `/saas/settings/marketplace` (Admin Config)

#### Marketplace Item Schema
| Field | Type | Description |
|-------|------|-------------|
| `template_id` | UUID | Unique ID |
| `name` | String | e.g. "Customer Support V2" |
| `price_model` | Enum | `Free`, `One-time`, `Subscription` |
| `price_cents` | Int | Cost in cents |
| `capabilities`| List | `[web_browsing, code_exec]` |
| `tools` | List | Required tools (e.g. `jira-connector`) |
| `voice_enabled`| Bool | Does it have a custom voice? |

#### User Journey: "Buying an Agent"
1.  **Browse:** Tenant Admin filters by "Support".
2.  **Preview:** Sees a demo chat window (Sandbox Mode).
3.  **Purchase:** Clicks [Install for $49/mo].
4.  **Provision:** System instantiates:
    *   `Agent` row in Tenant DB.
    *   `VoicePersona` (if applicable).
    *   `Tool` connections (prompts for API keys).

### 2.2 🎙 The Voice Studio (`/saas/voice-studio`)

A "God Mode" interface for managing the auditory experience of the platform.

#### The Voice Lab Feature
**Route:** `/saas/voice-studio/lab`

*   **Voice Cloning:** Drag & drop 30s audio sample.
    *   *Backend:* Uploads to ElevenLabs/OpenAI `voice-clone` endpoint.
    *   *Result:* "Soma-Clone-X" ID generated.
*   **Parameter Tuning:**
    *   `Stability`: Slider (0.0 - 1.0)
    *   `Similarity`: Slider (0.0 - 1.0)
    *   `Style Exaggeration`: Slider (0.0 - 1.0)
*   **Preview:** Type text -> [Generate Audio].

#### Global Voice Catalog (`/saas/settings/voices`)
(Extends `admin/voice/models.py`)

*   **System Voices:** Hardcoded (Alloy, Echo).
*   **Premium Voices:** Only available on Enterprise Tier.
*   **Marketplace Voices:** "Celebrity" voices or highly tuned personas available for purchase.

---

## 3. UI Specifications

### 3.1 Screen: Marketplace Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏪 AGENT MARKETPLACE                                     [Upload Template]  │
├─────────────────────────────────────────────────────────────────────────────┤
│  [ Search Agents... ]   [ Filter: Support | Coding | Creative | 🎙 Voice ]  │
│                                                                             │
│  FEATURED                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐ │
│  │ 👩‍💼 HR Manager Pro    │  │ 👨‍💻 Python Expert     │  │ 🎨 DALL-E Artist   │ │
│  │ By: System           │  │ By: DevComm          │  │ By: System         │ │
│  │ ⭐️ 4.9 (12k)         │  │ ⭐️ 4.7 (8k)          │  │ ⭐️ 4.8 (5k)        │ │
│  │ $29/mo               │  │ Free                 │  │ $10/mo             │ │
│  │ [Install]            │  │ [Install]            │  │ [Install]          │ │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘ │
│                                                                             │
│  VOICE PACKS                                                                │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │ 🎙 British Narrator  │  │ 🎙 Sci-Fi Hardware   │                         │
│  │ Sample: ▶️           │  │ Sample: ▶️           │                         │
│  │ $5 one-time          │  │ $2 one-time          │                         │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Screen: Voice Studio (`/saas/voice-studio`)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎙 VOICE STUDIO                                            [+ Clone Voice]  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Managed Voice Personas (Platform Wide)                                     │
│                                                                             │
│  NAME           PROVIDER      TYPE       GENDER     TIER         ACTIONS    │
│  Rachel         ElevenLabs    Standard   Female     Free         [Edit]     │
│  Batman         Custom (Clone)Cloned     Male       Enterprise   [Edit]     │
│  Jarvis         OpenAI        Standard   Male       Starter+     [Edit]     │
│                                                                             │
│  -------------------------------------------------------------------------  │
│  🎤 VOICE LAB PREVIEW                                                       │
│  Text: [ Welcome to Soma... ]  Voice: [ Batman ▼ ]  [▶️ Generate]           │
│  <Audio Waveform Visualization>                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Monetization & Billing

**Integration with Lago:**
When a Marketplace Item is purchased:
1.  **Bill Charge:** One-time fees are pushed to Lago as `add_on` charges.
2.  **Subscription:** Recurring fees are added as `billable_metric` or `plan_override` in Lago.

**Revenue Share (Future):**
*   Developer Payouts: Calculated by `(Revenue - PlatformFee) * 0.70`.
*   Needs `Stripe Connect` integration (Phase 2).

---

## 5. Security Implications

*   **Malicious Agents:** All marketplace templates MUST undergo a `Security Audit` (manual approval status in DB) before public listing.
*   **Voice Deepfakes:** Cloning requires "Voice Rights Verification" (Upload consent form).
*   **Tool Sandbox:** Agents from marketplace run in restricted `ephemeral` pods by default.
