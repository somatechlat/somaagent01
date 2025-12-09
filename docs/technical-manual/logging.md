# Logging and Error Handling

This document describes the logging and error handling mechanisms used in the Agent Zero application.

## Logging

The Agent Zero application uses a custom logging system defined in `python/helpers/log.py`. This system is designed to provide structured, detailed, and real-time logging for all agent activities.

### `Log` Class

The `Log` class is the main entry point for logging. It maintains a list of `LogItem` objects and provides methods for adding and updating log entries.

### `LogItem` Class

A `LogItem` represents a single entry in the log. It has the following attributes:

- **`type`**: The type of log entry (e.g., `agent`, `tool`, `error`).
- **`heading`**: A brief summary of the log entry.
- **`content`**: The detailed content of the log entry.
- **`kvps`**: A dictionary of key-value pairs for additional structured data.
- **`temp`**: A boolean indicating whether the log entry is temporary.

### Log Truncation

To prevent excessively large log files, the logging system automatically truncates long strings in the `heading`, `content`, and `kvps` fields.

### Secrets Masking

The logging system automatically masks sensitive information, such as API keys and passwords, before writing to the log. This is handled by the `SecretsManager` class.

## Error Handling

Error handling in the Agent Zero application is designed to be robust and informative.

### `handle_error()`

The `handle_error()` function in `python/helpers/errors.py` is a general-purpose error handler. It re-raises `asyncio.CancelledError` to allow for proper task cancellation and otherwise does nothing.

### `format_error()`

The `format_error()` function in `python/helpers/errors.py` formats an exception and its traceback into a human-readable string. This is used to provide detailed error information in the logs and to the user.

### `RepairableException`

The `RepairableException` class is a custom exception type that indicates an error that can potentially be repaired by the agent itself. When this exception is caught, the error message is surfaced to the agent, allowing it to attempt a self-correction.
