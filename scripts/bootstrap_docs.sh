#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_ROOT="${PROJECT_ROOT}/docs"

echo "📚 Bootstrapping somaStackPropagation documentation structure..."

# Create directory structure
mkdir -p "${DOCS_ROOT}"/{user-manual/features,technical-manual/{runbooks,security},development-manual,onboarding-manual,agent-onboarding,i18n/en}

# Create all required files
cat > "${DOCS_ROOT}/metadata.json" <<'EOF'
{
  "title": "somaStackPropagation Documentation",
  "version": "1.0.0",
  "last_updated": "2025-01-XX",
  "owner": "Documentation Team",
  "project": "somaAgent01",
  "standards": [
    "ISO/IEC 12207",
    "ISO/IEC 26512",
    "ISO/IEC 26514",
    "ISO/IEC 26515",
    "ISO/IEC 42010",
    "ISO 21500"
  ],
  "badge": "![Version](https://img.shields.io/badge/version-1.0.0-blue)"
}
EOF

cat > "${DOCS_ROOT}/README.md" <<'EOF'
# somaAgent01 Documentation

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Quick Overview
- **What**: Real-time agentic platform with perfect memory, built on Kubernetes, Kafka & SomaBrain
- **Who**: Engineers, SREs, Product owners, auditors, AI agents
- **Where**: Docs live under `/docs/` and are published via MkDocs-Material

## Documentation Structure
| Manual | Path | Audience |
|--------|------|----------|
| User Manual | `docs/user-manual/` | End-users, product managers |
| Technical Manual | `docs/technical-manual/` | SREs, Ops, Platform engineers |
| Development Manual | `docs/development-manual/` | Contributors, developers |
| Onboarding Manual | `docs/onboarding-manual/` | New hires, contractors |
| Agent Onboarding | `docs/agent-onboarding/` | AI agents, automation bots |

## Standards Compliance
This documentation set follows ISO/IEC 26514 (user docs), 26515 (online delivery), 26512 (processes), and 42010 (architecture).
EOF

cat > "${DOCS_ROOT}/.markdownlint.json" <<'EOF'
{
  "MD013": { "line_length": 120 },
  "MD033": false,
  "MD041": true
}
EOF

cat > "${DOCS_ROOT}/style-guide.md" <<'EOF'
# Documentation Style Guide (ISO 12207§8.3)

## Rules
- **File names**: `kebab-case.md`
- **Headings**: ATX style (`#`, `##`)
- **Code blocks**: Triple backticks with language
- **Diagrams**: PlantUML (`.puml`) or Mermaid
- **Links**: Relative (`[text](../path/file.md)`)
- **Accessibility**: All images need `alt` text

## Linting
CI runs `markdownlint-cli2` with `.markdownlint.json` rules.
EOF

# Create placeholder index files
for dir in user-manual technical-manual development-manual onboarding-manual agent-onboarding; do
  cat > "${DOCS_ROOT}/${dir}/index.md" <<EOF
# ${dir//-/ } Overview

This section is under construction.
EOF
done

# Create critical technical files
cat > "${DOCS_ROOT}/technical-manual/architecture.md" <<'EOF'
# System Architecture

## Overview
somaAgent01 is a distributed agentic platform with:
- Gateway (FastAPI edge)
- Conversation Worker (orchestration)
- Tool Executor (deterministic execution)
- SomaBrain (perfect memory)
- Kafka, Redis, Postgres (infrastructure)

See `architecture.puml` for C4 diagram.
EOF

touch "${DOCS_ROOT}/technical-manual/architecture.puml"
touch "${DOCS_ROOT}/technical-manual/data-flow.mermaid"

# Create minimal required files
touch "${DOCS_ROOT}"/{glossary.md,changelog.md,review-log.md,accessibility.md,security-classification.md}
touch "${DOCS_ROOT}/user-manual"/{installation.md,quick-start-tutorial.md,faq.md}
touch "${DOCS_ROOT}/user-manual/features"/{feature-data-pipeline.md,feature-real-time-propagation.md}
touch "${DOCS_ROOT}/technical-manual"/{deployment.md,monitoring.md,backup-and-recovery.md}
touch "${DOCS_ROOT}/technical-manual/runbooks"/{propagation-service.md,data-ingest-service.md}
touch "${DOCS_ROOT}/technical-manual/security"/{secrets-policy.md,rbac-matrix.md}
touch "${DOCS_ROOT}/development-manual"/{local-setup.md,first-contribution.md,coding-standards.md,testing-guidelines.md,api-reference.md,contribution-process.md}
touch "${DOCS_ROOT}/onboarding-manual"/{project-context.md,codebase-walkthrough.md,first-contribution.md,team-collaboration.md,domain-knowledge.md}
touch "${DOCS_ROOT}/agent-onboarding"/{agent-zero.md,propagation-agent.md,monitoring-agent.md,security-hardening.md}
touch "${DOCS_ROOT}/i18n/en/README.md"

echo "✅ Documentation structure created at ${DOCS_ROOT}"
echo "📝 Run 'ls -R ${DOCS_ROOT}' to verify"
