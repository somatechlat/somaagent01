# Duplicate Documentation Audit — quick report

Generated: automated scan (exact duplicates, very small docs, and duplicate filenames across directories).

Summary
- Exact duplicate files found (content identical) between the top-level `docs/` and `a0_data/docs/` directories. These appear to be mirrored copies. Examples include:
  - `docs/contribution.md` and `a0_data/docs/contribution.md`
  - `docs/notifications.md` and `a0_data/docs/notifications.md`
  - many `docs/SomaAgent01_*.md` files present also under `a0_data/docs/`

- Very small files (<200 bytes) exist (prompts and agent _context files). Many are duplicated under both the normal path and `a0_data/`.

- Several files with the same filename exist in different directories (e.g., `README.md`, `requirements.txt`, many prompt files). The majority of these duplicates are the `a0_data/` content mirroring the root content.

Why this matters
- Redundant documentation increases maintenance burden and causes confusion about the canonical source. It also bloats the repo and makes searches ambiguous.

Recommendations (safe, low-risk cleanup plan)
1. Keep `docs/` as the canonical documentation folder. The `docs/` content is complete and organized. Where `a0_data/docs/` is an exact mirror, remove the duplication by:
   - Option A (preferred): Remove `a0_data/docs/` and keep a small `a0_data/README.md` indicating why `a0_data/` exists (if required by tooling). Commit the removal as a single change.
   - Option B: Add a `README` to `a0_data/` that points to the canonical `docs/` and update any scripts that reference `a0_data/docs/` to use `docs/` instead.

2. For prompt files under `prompts/` that are duplicated under `a0_data/prompts/`:
   - Consolidate into `prompts/` as canonical and remove `a0_data/prompts/` duplicates. These are small text snippets and are safe to deduplicate.

3. Very small `_context.md` and agent prompt files under `agents/*` and `a0_data/agents/*`:
   - If the `a0_data/` tree is a packaged snapshot, keep the active `agents/` directory and delete `a0_data/agents/`.
   - If `a0_data/` must remain (for artifact or snapshot reasons), add a note in `a0_data/README.md` and consider adding a small script that syncs canonical docs from `docs/` into `a0_data/` only when intended.

4. Files with the same filename in several places (e.g., `requirements.txt`) — review the contents manually and deduplicate only if they are identical. Keep environment-specific ones (e.g., `a0_data/requirements.txt` might be for the packaged artifact) but clarify with a filename suffix or folder-level README.

Proposed immediate safe actions (I can run these if you want)
- Action A (safe, reversible): Create `a0_data/README.md` explaining that `a0_data/` contains packaged snapshots and that canonical docs live in `docs/`. This avoids accidental edits in the mirror location.
- Action B (cleanup): Move exact duplicate files from `a0_data/docs/` into a single commit that deletes them. This is reversible via git revert.

Next steps
- Tell me which option you prefer for `a0_data/` content:
  1) Remove `a0_data/docs/` duplicates now (I will create a cleanup patch and commit it). This is the cleanest.
  2) Keep `a0_data/` but add `a0_data/README.md` and leave duplicates in place.
  3) I should produce a smaller, more detailed per-file list (CSV) and create a PR with suggested deletions for your review.

I left the process lightweight and non-destructive; nothing was deleted. Tell me how you'd like to proceed and I’ll perform the chosen cleanup (I’ll update the todo list and commit changes). 
