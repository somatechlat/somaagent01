# Golden UI Behavior Checklist (7001)

Source of truth for UI parity. Derived from Playwright golden project and manual inspection. All selectors are from `webui/tests/ui/specs/util.ts` and spec files.

Status legend: [✓] observed/green, [~] present but flaky/different, [⨯] missing or failing, [opt] optional/graceful-absent.

## Core shell
- [✓] Home loads and renders core controls
  - `#chat-input`, `#send-button`, `#chat-history` exist
- [✓] Sidebar present
  - `#left-panel` exists; sections list present; `#tasks-section` may be hidden initially [opt]
- [~] Visual baseline (full page)
  - Snapshot similarity expected; small diffs allowed; investigate branding/date/time variations

## Composer & message flow
- [✓] Send on Enter enqueues/thinks
  - Press Enter in `#chat-input` → `#progress-bar` shows activity ("thinking")
- [✓] Conversation basics
  - New chat, send message, assistant tokens stream or at least enqueue visible
- [⨯] Reset chat clears history
  - After clicking Reset, `#chat-history` should have ≤ 1 bubble before next send; currently many default bubbles present (welcome/notifications)
- [✓] Long stream stability
  - UI remains responsive; no console errors during long prompts

## Sidebar sessions
- [✓] Create and delete session via X
  - Session entry appears and is deletable via “X” button

## Settings and toggles
- [~] Settings modal opens
  - Click `#settings` or `#settings-button` → `#settingsModal .modal-container` visible; currently timing out on Golden
- [~] Header toggles persist across reload
  - Checkboxes for “Show thoughts”, “Show JSON”, “Show utility messages” exist and persist; currently some are off‑viewport in Golden and require scroll/visibility handling

## Scheduler & Tools
- [✓][opt] Scheduler tab present
  - Tab/button present or gracefully absent is acceptable
- [✓][opt] Tools Manager present
  - Endpoint present or gracefully absent is acceptable

## Uploads & attachments
- [✓] File chooser accepts a file
  - `#file-input` or first visible `input[type=file]` accepts a temp file; chip/badge may or may not appear [opt]

## Network/SSE
- [~] SSE present (no legacy polling)
  - EventSource should be present; polling must be absent. Marked skip in tests when not verifiable in Golden.

## Tokens capture (observability)
- [~] Capture home and settings tokens
  - Trace tokens saved; settings capture blocked if modal not present

## Known Golden gaps to annotate
- Default welcome/history content causes `reset` test to see >1 history items.
- Settings modal selector or appearance differs; ensure correct button id and modal id, or treat settings as optional on Golden.
- Toggles UI may require scrolling into view; some elements off‑viewport during test; adjust scrolling logic if/when stabilizing tests.

## Artifacts & references
- Playwright project: `webui/tests/ui`
- Config: `webui/tests/ui/playwright.config.ts`
- Selectors/util: `webui/tests/ui/specs/util.ts`
- Recent traces: `webui/tests/ui/test-results/*/trace.zip`
