# Data Models

This document describes the key data models used in the Agent Zero application.

## Tool Definition

The `ToolDefinition` and `ToolParameter` classes, defined in `python/tools/models.py`, are used to represent the definition of a tool that can be used by an agent.

### `ToolParameter`

The `ToolParameter` class represents a single parameter for a tool.

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | The name of the parameter. |
| `type` | `str` | The type of the parameter (e.g., `string`, `integer`). |
| `description` | `Optional[str]` | A description of the parameter. |
| `required` | `bool` | Whether the parameter is required. |
| `default` | `Any` | The default value of the parameter. |

### `ToolDefinition`

The `ToolDefinition` class represents the definition of a tool.

| Attribute | Type | Description |
|---|---|---|
| `name` | `str` | The name of the tool. |
| `description` | `str` | A description of the tool. |
| `parameters` | `List[ToolParameter]` | A list of parameters for the tool. |
| `category` | `Optional[str]` | The category of the tool. |

## `BuiltContext`

The `BuiltContext` class, defined in `python/somaagent/context_builder.py`, is a data class that holds the context for an agent's turn.

| Attribute | Type | Description |
|---|---|---|
| `system_prompt` | `str` | The system prompt for the agent. |
| `messages` | `List[Dict[str, Any]]` | A list of messages to be sent to the agent. |
| `token_counts` | `Dict[str, int]` | A dictionary of token counts for each part of the prompt. |
| `debug` | `Dict[str, Any]` | A dictionary of debugging information. |
