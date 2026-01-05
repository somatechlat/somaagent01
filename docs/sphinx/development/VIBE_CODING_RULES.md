# VIBE Coding Rules

> **Authority**: SOMA Stack Architecture Board
> **Version**: 4.90.0 (Ph.D. Edition)

This document establishes the non-negotiable coding standards for the SOMA Stack. Adherence is mandatory for all contributions.

## Rule 1: The Human-First Standard
Code must be written for human readability and auditability. "AI Slop"—code generated without intent, understanding, or aesthetic consideration—is strictly prohibited.
- **No Boilerplate Comments**: Avoid `// this function does X`. Code should be self-documenting.
- **Meaningful Variable Names**: Use descriptive names (`user_active_status`) over cryptic abbreviations (`uas`).

## Rule 2: 100% Documentation Coverage
Every module, class, and public function must have a docstring (Google Style for Python).
- **Modules**: Explain the *purpose* and *architectural context*.
- **Classes**: Define the *responsibility* and *invariants*.
- **Functions**: Specify *args*, *returns*, and *raises*.

## Rule 3: The Simple Elegant Core
Complexity is a liability. Prefer simple, proven solutions over complex, "clever" abstractions.
- **No Over-Engineering**: Do not build for hypothetical future requirements.
- **Explicit over Implicit**: Avoid magic. Imports and control flow should be obvious.

## Rule 4: Zero-Warning Policy
The codebase must build and run with zero warnings.
- **Linting**: All linters (flake8, black, isort) must pass.
- **Docs**: Sphinx builds must generate no warnings.
- **Tests**: All tests must pass without warnings.

## Rule 5: Architecture Parity
Maintain strict alignment with the Master Architecture.
- **Triad Structure**: Respect the separation of `somaAgent01` (Action), `somabrain` (Cognition), and `somafractalmemory` (Storage).
- **Service Boundaries**: Do not leak implementation details across defined service interfaces.

## Rule 6: Testing Mandate
No code is merged without verification.
- **Unit Tests**: Test logic in isolation.
- **Integration Tests**: Verify component interactions.
- **No Mocks (Where Possible)**: Prefer testing against real dependencies (e.g., test databases) whenever feasible to ensure reality-aligned behavior.
