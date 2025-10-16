# Tooling Integration Guide

## Purpose
Explain how SomaAgent01 invokes and extends tools to perform actions beyond pure conversation.

## Tool Invocation Lifecycle

1. LLM response includes tool call (`function_call` in LiteLLM schema).
2. Gateway validates tool name, serializes arguments, publishes to Kafka (`somastack.tools`).
3. Tool Executor consumes message, runs corresponding tool.
4. Results returned via Kafka (`somastack.tool_results`) or HTTP callback.
5. Gateway streams outcome to UI, optionally saves memory.

## Built-in Tools

| Tool | Capability |
| --- | --- |
| `shell` | Execute shell commands in sandbox |
| `code_interpreter` | Run Python code, return stdout/plots |
| `http` | Perform HTTP requests (respecting allowlists) |
| `memory_save` / `memory_search` | Persist / query SomaBrain |
| `knowledge_base` | Query external knowledge articles |

## Creating Custom Tools

1. Implement class extending `Tool` base (see `python/tools/base.py`).
2. Define JSON schema for arguments and results.
3. Register tool in discovery map (`python/tools/__init__.py`).
4. Add documentation in `docs/features/tooling.md` (this file) under new section.
5. Provide integration tests to ensure Gateway/Executor roundtrip.

## Example: Weather Tool

```python
class WeatherTool(Tool):
    name = "weather"
    description = "Fetch weather for a city"
    args_schema = WeatherArgs

    async def run(self, city: str):
        resp = await http_client.get(f"https://api.weather.com/{city}")
        return resp.json()
```

LLM prompt snippet:
```json
{
  "type": "function",
  "function": {
    "name": "weather",
    "arguments": {"city": "Prague"}
  }
}
```

## Security Considerations

- Validate inputs; enforce allowlists for network calls.
- Sandbox file operations; use temporary directories.
- Redact secrets in logs (use `python/helpers/secrets.py`).

## Monitoring Tool Usage

- Kafka metrics reveal volume per tool.
- Gateway logs include `tool_name`, `task_id`.
- Add tracing spans to measure execution time.

## Machine Clients

Automation agents can queue tasks directly by writing to Kafka or using Gateway `POST /chat` with tool instructions. Ensure correlation IDs are tracked for result handling.
