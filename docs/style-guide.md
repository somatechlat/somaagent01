# Documentation Style Guide

**Standards**: ISO/IEC 12207§8.3

## Formatting Rules

### File Naming
- Use `kebab-case.md` for all files (e.g., `local-setup.md`)
- Directories use singular nouns (`runbook/`, not `runbooks/`)
- No spaces, underscores, or special characters

### Markdown Standards
- Headers: Use ATX-style (`#`, `##`, `###`)
- Code blocks: Always specify language (```bash, ```python, ```yaml)
- Lists: Use `-` for unordered, `1.` for ordered
- Links: Use reference-style for repeated URLs
- Tables: Align columns with pipes

### Terminology
- **Service** - Microservice component (e.g., Gateway, Conversation Worker)
- **Worker** - Kafka consumer service
- **Topic** - Kafka topic
- **Session** - Conversation context
- **Persona** - User identity
- **Tenant** - Multi-tenancy boundary

### Code Examples
- Include complete, runnable examples
- Show expected output
- Add verification commands
- Use real port numbers (20000-20099 range)

### Verification Pattern
Every procedure must include:
```bash
# Command to run
command --flag value

# Expected output
✅ Success message
```

## Linting
- Run `markdownlint` before commit
- No trailing whitespace
- One blank line at end of file
- Max line length: 120 characters (except code blocks)

## Accessibility
- Alt text for all images
- Descriptive link text (not "click here")
- Semantic HTML in embedded content
- Color contrast ratio ≥ 4.5:1
