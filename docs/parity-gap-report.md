# SA01 ↔ Golden UI Parity Gap Report (2025-11-03)

This report compares Golden (7001) vs SA01 Local (21016) using the Playwright suites under `webui/tests/ui`.

Summary
- Golden: 13 passed, 6 skipped, 0 failed (serial, 1 worker).
- Local: 12 passed, 3 skipped, 4 failed (serial, 1 worker).
- Parity (dual-browser): 10 passed, 5 skipped, 4 failed.

Key gaps and fixes
1) Thinking indicator (composer) — FAIL on Local
   - Test: `chat.composer.spec.ts` → `waitForThinking()` did not detect activity in 10s.
   - Golden behavior: `#progress-bar` shows activity after hitting Enter.
   - SA01 fix (UI): Emit a visible progress element/state during message send (e.g., add/update `#progress-bar` text while SSE is pending). Wire to existing send lifecycle.

2) Settings container — tests assume modal; Local renders a panel
   - Tests failing: `settings.persistence.spec.ts` (expects `#settingsModal .modal-container`).
   - Golden: Settings captured via modal or panel; tests now tolerate both.
   - SA01 options: (a) Switch to modal with `#settingsModal` (preferred for parity) or (b) standardize panel and update local-only tests to target the panel container and selectors.

3) Header toggles persistence — FAIL on Local/Parity
   - Tests: `toggles.persistence.spec.ts`, `thought.bubbles.and.toggles.spec.ts`.
   - Golden: captured states only (no strict persistence). Local suite enforces persistence across reload.
   - SA01 fix (UI): Persist toggles to `localStorage` (e.g., showThoughts, showJSON, showUtils) and rehydrate on load. Ensure checkboxes are operable (in-viewport) before click.

4) Utilities toggle off-viewport issues — FIXED in tests
   - We hardened interactions (center-in-view, fallback events) in `utilities.spec.ts`. No UI change required.

5) Tokens capture
   - Golden and Local tokens now captured at:
     - `webui/tests/ui/tokens/golden/{home,settings}.json`
     - `webui/tests/ui/tokens/local/{home,settings}.json`
   - Use these diffs to drive CSS/class name alignment for exact visual parity.

6) Visual parity (parity.spec.ts)
   - Snapshot bootstrap added; comparison will fail if layout deviates beyond threshold (5%/2500px).
   - SA01 fix: Align layout and spacing (sidebar/#right-panel heights, margins, fonts) to reduce diff.

Artifacts & traces
- Golden: `webui/tests/ui/test-results/*-golden/trace.zip`
- Local: `webui/tests/ui/test-results/*-local/trace.zip`
- Parity: `webui/tests/ui/test-results/*-parity/trace.zip`
- Snapshots: `webui/tests/ui/specs/golden.visual.spec.ts-snapshots/`, `webui/tests/ui/specs/parity.spec.ts-snapshots/`
- Tokens: `webui/tests/ui/tokens/{golden,local}`

Proposed acceptance for SA01 parity
- Composer: `waitForThinking()` returns true within 10s.
- Settings: Either modal at `#settingsModal .modal-container` or standardized panel recognized by tests.
- Toggles: After changing and reloading, states persist (Show thoughts=false, Show JSON=true, Show utilities=true).
- Visual: Parity snapshot within 5%/≤2500px diff.

Implementation pointers (UI)
- Composer state: update the send lifecycle in `webui/js/messages.js` to set/unset a visible progress element `#progress-bar`.
- Settings modal: reuse `webui/js/modal.js` and assign `id="settingsModal"` to the container; ensure `Settings` button opens this modal.
- Toggles persistence: in `webui/js/settings.js` (or a small new module), read/write `localStorage` for `showThoughts`, `showJSON`, `showUtils` and bind checkboxes accordingly on init.

Next steps
- Implement the three UI fixes above on a feature branch.
- Re-run `npx playwright test --project=local --workers=1` and `--project=parity` until green.
- Commit updated snapshots only if layout changes are intentional and within the defined thresholds.
