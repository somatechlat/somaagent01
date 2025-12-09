# Development Manual

This document provides a guide for developers working on the Agent Zero repository.

## Coding Standards

The Agent Zero repository follows the PEP 8 style guide for Python code. All code should be formatted using the `black` code formatter.

## AI-Assisted Coding Policy

This repository has a strict policy against AI-generated code being committed directly to the codebase. While AI assistants can be used for research, brainstorming, and generating documentation, all code must be written and thoroughly reviewed by a human developer.

## Testing Strategy

The Agent Zero repository uses a multi-layered testing strategy to ensure code quality and prevent regressions.

### Unit Tests

Unit tests are located in the `tests/unit/` directory and are written using the `pytest` framework. These tests are designed to test individual components in isolation.

### Integration Tests

Integration tests are located in the `tests/integration/` directory and are designed to test the interactions between different components.

### End-to-End Tests

End-to-end tests are located in the `tests/e2e/` directory and are designed to test the entire application from the user's perspective.

## CI Pipeline

The Agent Zero repository uses GitHub Actions for its continuous integration (CI) pipeline. The CI pipeline is defined in the `.github/workflows/` directory and is triggered on every push to the `main` branch. The pipeline performs the following steps:

1.  **Linting and Formatting:** The code is checked for compliance with the PEP 8 style guide and formatted using `black`.
2.  **Unit Tests:** The unit tests are run to ensure that all components are working as expected.
3.  **Integration Tests:** The integration tests are run to ensure that all components are working together as expected.
4.  **End-to-End Tests:** The end-to-end tests are run to ensure that the entire application is working as expected.
