# Contribution Process

> **Standard**: SOMA Stack Engineering Workflow

This guide details the process for contributing to the SOMA Stack repositories (`somaAgent01`, `somabrain`, `somafractalmemory`).

## 1. Branching Strategy

We follow a strict, consolidated branching model to ensure stability and clarity.

- **`main`**: The single source of truth for production-ready code. Protected.
- **`django`**: The active development branch for the current Django migration/refactor phase.
- **`gh-pages`**: Restricted branch for documentation deployment. Automated.

**Do NOT create ad-hoc branches** like `fix/my-bug` or `feat/cool-thing` without prior approval. All work currently converges on `django` before release to `main`.

## 2. Development Workflow

1.  **Sync**: Ensure you are up-to-date with `origin/django`.
2.  **Develop**: Make your changes locally.
3.  **Verify**:
    - Run the **Zero-Warning Check**: Linting + Tests.
    - Build Documentation: `make html` in the `docs/sphinx` directory.
4.  **Commit**: Use semantic commit messages (e.g., `feat: add user profile`, `fix: resolve auth timeout`).

## 3. Pull Request Protocol

1.  **Template**: Fill out the PR template completely.
2.  **Scope**: Keep PRs focused on a single logical change.
3.  **Review**: All PRs require at least one Human review (`CODEOWNERS`).
4.  **CI/CD**: Wait for all checks to pass (Green build).

## 4. Documentation

Documentation is not an afterthought; it is part of the definition of functionality.
- **New Features**: Must include updated `QUICKSTART.md` or API docs.
- **Refactors**: Must verify that existing docs remain accurate.
- **Build**: You must successfully build the docs locally before submitting.

## 5. Deployment

Deployment is automated via the `final_deploy.sh` script, which handles:
1.  Building documentation for all repos.
2.  Pushing artifacts to `gh-pages`.
3.  Verifying site health.

**Note**: Manual deployment from local machines is permitted only by authorized Release Engineers using the verified script.
