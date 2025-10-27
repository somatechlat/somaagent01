# Quick Start Tutorial

**Standards**: ISO/IEC 29148§5.2

## Your First Conversation

### 1. Access the UI

Open your browser to:
- Docker: `http://localhost:50001`
- Local dev: `http://127.0.0.1:3000`

### 2. Login

Enter the password you set in `.env` (`AUTH_PASSWORD`)

### 3. Start a Conversation

Type in the chat input:
```
Hello! Can you help me understand what you can do?
```

**Expected**: The agent responds with its capabilities.

### 4. Execute Code

Try a simple task:
```
Create a Python script that prints the current date and time, then run it.
```

**Expected**: The agent writes Python code, executes it, and shows the output.

### 5. Use Memory

Ask the agent to remember something:
```
Remember that my favorite programming language is Python.
```

Then in a new session:
```
What's my favorite programming language?
```

**Expected**: The agent recalls the information from memory.

## Common Tasks

### File Operations

```
Create a file called test.txt with "Hello World" in it.
```

### Web Search

```
Search for the latest news about AI agents.
```

### Multi-Agent Delegation

```
I need to analyze a large dataset. Can you delegate this to a subordinate agent?
```

## Next Steps

- [Features Overview](./features.md)
- [FAQ](./faq.md)
- [Troubleshooting](./troubleshooting.md)
