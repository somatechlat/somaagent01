---
title: Documentation Style Guide
slug: documentation-style-guide
version: 1.0.0
last-reviewed: 2025-10-15
audience: documentation authors
owner: docs-lead
reviewers:
  - developer-experience
  - product
verification:
  - Lint & link checks pass via `make docs-verify`
---

# Documentation Style Guide

Use this guide to keep SomaAgent01 documentation consistent across manuals.

## Structure

- Manuals live under `docs/<manual-name>/` using kebab-case directories.
- Each page begins with YAML front matter declaring `title`, `version`, `last-reviewed`, `audience`, `owner`, `reviewers`, `prerequisites`, and `verification` when applicable.
- Use sentence case for headings (`## Install dependencies`).

## Voice & Tone

- Direct, action-oriented instructions.
- Highlight decisions with callouts (`> [!TIP]`, `> [!NOTE]`).
- Avoid marketing language; focus on actionable guidance.

## Formatting

- Wrap file paths and commands in backticks.
- Use fenced code blocks with language hints (` ```bash`).
- Tables require header separators and concise columns.
- Diagrams authored in Mermaid; store sources in `docs/diagrams/`.

## Links & References

- Prefer relative links (`../technical-manual/architecture.md`).
- Update links when relocating content; run link checker before merging.
- Reference change log entries when updating procedures.

## Media

- Store images under `docs/res/<manual>/<topic>/`.
- Provide alt text and captions.
- Optimize images for web (<500 KB) before committing.

## Metadata

- Update `last-reviewed` on every substantive change.
- Add reviewers who approved the content.
- State verification criteria so readers can confirm success.

## Checklist

See [`docs/documentation-audit-checklist.md`](./documentation-audit-checklist.md) before submitting PRs.
