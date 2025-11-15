# Quick Start Tutorial

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Your First Conversation

### 1. Start the Stack

```bash
make dev-up
make health-wait
```

### 2. Open the UI

Navigate to: http://localhost:21016/ui

### 3. Configure LLM Provider

1. Click **Settings** (gear icon)
2. Go to **Model** tab
3. Set:
   - **Provider**: `groq`
   - **Model**: `llama-3.1-8b-instant`
4. Go to **API Keys** tab
5. Add: `api_key_groq` = `your-groq-api-key`
6. Click **Save** (this UI flow is the single source of truth for LLM secrets)

### 4. Start a Chat

1. Type: `"Hello! Can you help me with Python?"`
2. Press **Enter**
3. Watch the assistant respond in real-time via SSE

## Example Use Cases

### Code Execution
```
User: Write a Python script to calculate fibonacci numbers
Assistant: [Executes code_execution tool, returns result]
```

### Web Search
```
User: What are the latest AI developments?
Assistant: [Uses search_engine tool, summarizes findings]
```

### Memory Persistence
```
User: Remember that I prefer Python over JavaScript
Assistant: [Saves to SomaBrain via memory_save tool]
```

## Understanding the Flow

1. **Message Sent**: UI → Gateway `/v1/session/message` → Kafka `conversation.inbound`
2. **Processing**: Conversation Worker consumes message → Calls Gateway `/v1/llm/invoke/stream`
3. **Streaming**: Assistant response → Kafka `conversation.outbound` → Gateway SSE → UI
4. **Memory**: All messages written to SomaBrain for perfect recall

## Next Steps

- [Features Overview](./features.md)
- [Using Tools](./using-the-agent.md)
- [Troubleshooting](./troubleshooting.md)
