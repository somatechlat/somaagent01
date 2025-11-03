# Frequently Asked Questions

**Standards**: ISO/IEC 21500§7.4

## General

### What is SomaAgent01?

SomaAgent01 is a microservices-based conversational AI platform built on Agent Zero framework. It provides a general-purpose AI assistant with code execution, memory, and multi-agent capabilities.

### What LLM providers are supported?

- OpenRouter (default)
- OpenAI
- Anthropic
- Groq
- Venice.ai
- GitHub Copilot
- Local models (via LiteLLM)

### Is my data secure?

Yes. All credentials are encrypted (Fernet), sessions are isolated by tenant, and OPA policies enforce access control. See [Security](../technical-manual/security.md) for details.

## Installation

### What are the minimum requirements?

- 8GB RAM
- 10GB disk space
- Docker 20.10+ or Python 3.11+

### Can I run without Docker?

Yes. Use `make deps-up` for infrastructure, then `make stack-up` for services. See [Installation Guide](./installation.md).

### Which ports are required?

Core ports: 20000 (Kafka), 20001 (Redis), 20002 (PostgreSQL), 21016 (Gateway). See [Port Reference](./installation.md#port-reference).

## Usage

### How do I save conversations?

Conversations are automatically saved to PostgreSQL. Use the UI's "Export Chat" button to download as JSON.

### Can I use custom tools?

Yes. Create tools in `python/tools/` following the existing pattern. See [Extensibility](../development-manual/extensibility.md).

### How does memory work?

Short-term memory is in-session context. Long-term memory is stored in SomaBrain (port 9696) and persisted across sessions.

### Can agents access the internet?

Yes, via web search tools (DuckDuckGo, SearXNG) and browser agent (Playwright).

## Troubleshooting

### Gateway returns 500 errors

Check logs: `docker compose logs gateway`. Common causes:
- Kafka not ready
- PostgreSQL connection failed
- Missing environment variables

### Agent responses are slow

Check:
- LLM provider rate limits
- Network latency to LLM API
- Kafka consumer lag: `docker compose logs conversation-worker`

### Memory not persisting

Verify SomaBrain is running:
```bash
curl http://localhost:9696/health
```

If not, check `docker compose logs somabrain`.

### UI won't load

1. Check gateway health: `curl http://localhost:${GATEWAY_PORT:-21016}/v1/health`
2. Check UI logs: `docker compose logs ui`
3. Clear browser cache

## Development

### How do I contribute?

See [Contribution Workflow](../development-manual/contribution-workflow.md).

### How do I run tests?

```bash
pytest tests/unit/
pytest tests/integration/
```

### How do I add a new service?

1. Create service in `services/<name>/`
2. Add to `docker-compose.yaml`
3. Update documentation
4. Add tests

## Support

### Where can I get help?

- GitHub Issues: https://github.com/somatechlat/somaagent01/issues
- Discord: https://discord.gg/B8KZKNsPpj
- Documentation: https://docs.somaagent01.ai

### How do I report a bug?

Open a GitHub issue with:
- Steps to reproduce
- Expected vs actual behavior
- Logs (`docker compose logs`)
- Environment details

### Is there a community?

Yes! Join our Discord server and Skool community. Links in [README](../README.md).
