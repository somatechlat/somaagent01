# UI-X-07 — Brain

**Brain** — Right-rail panel in context — route `right-rail surface [7]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-07 Brain                                                                     ┐
│  capsule <capsule.name> v<version>     │ Surface: Brain                                                                                 │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ model roles (read-only) ───────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ chat_model      <model.id or: <unbound>>                                 │                   │
│  facets [Soul][Brain][Hands][Memory][Bo│ │ image_model     <model.id or: <unbound>>                                 │                   │
│  <Cmd-K>                               │ │ voice_model     <model.id or: <unbound>>                                 │                   │
│                                        │ │ browser_model   <model.id or: <unbound>>                                 │                   │
│  WORKSPACE (abbrev)                    │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  ┌────────────────────────────────┐    │ ┌─ derived AgentIQ (READ-ONLY, greyed, never inputs) ─────────────────────┐                    │
│  │ screen content in context        │  │ │ temperature         <value>     max_tokens          <value>              │                   │
│  │ (see UI-S-07 chat workspace)     │  │ │ rlm_iterations      <value>     recall_limit        <value>              │                   │
│  │ surface rail select: UI-X-07 Brain  │ │ model_tier          <value>     brain_query_enabled <value>              │                   │
│  └────────────────────────────────┘    │ │ require_hitl        <value>     tool_approval       <value>              │                   │
│                                        │ │ egress_allowed      <value>     token_limit         <value>              │                   │
│  instance <session_id> <state>         │ │ cost_tier           <value>     thinking_budget     <value>              │                   │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│ └──────────────────────────────────────────────────────────────────────────┘                   │
│                                        │ The three persona knobs stay in UI-S-00 chrome. This panel                                     │
│                                        │ never edits them. [open Brain facet (UI-S-02)]                                                 │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-114 | model role readout | Four roles bound to real configured models only. Unbound roles show `<unbound>`, never a placeholder model id. |
| 2 | UI-C-074 | derived AgentIQ readouts (READ-ONLY) | temperature, max_tokens, rlm_iterations, recall_limit, model_tier, brain_query_enabled, require_hitl, tool_approval, egress_allowed, token_limit, cost_tier, thinking_budget — greyed readouts beside the three knobs. NEVER inputs. |
| 3 | UI-C-068 | open Brain facet (secondary) | Routes to UI-S-02 where the three knobs are editable. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No model roles bound. Bind a chat model in Settings > Models."
- **Error.** "Couldn't load brain state. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the brain surface. Requires the Brain facet access."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — model role detail (provider, key status masked, last sync).
