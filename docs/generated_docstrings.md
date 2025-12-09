# Generated Docstrings

This file contains suggested docstrings for the Python source code.

## `python/somaagent/capsule.py`

### `_get_capsule_registry_url()`

```python
"""Gets the capsule registry base URL from the environment variables.

Returns:
    The capsule registry base URL as a string.
"""
```

### `list_capsules()`

```python
"""Lists all available capsules from the capsule registry.

Returns:
    A list of dictionaries, where each dictionary contains the metadata for a capsule.

Raises:
    httpx.HTTPStatusError: If the request to the capsule registry fails.
"""
```

### `download_capsule()`

```python
"""Downloads a capsule file from the capsule registry.

Args:
    capsule_id: The UUID of the capsule to download.
    dest_dir: The directory to save the downloaded file in. If not provided,
        a temporary directory will be created.

Returns:
    The path to the downloaded capsule file.

Raises:
    httpx.HTTPStatusError: If the request to the capsule registry fails.
"""
```

### `install_capsule()`

```python
"""Downloads and extracts a capsule into a specified directory.

Capsules are expected to be zip archives. This function first downloads the
capsule and then extracts its contents.

Args:
    capsule_id: The UUID of the capsule to install.
    install_dir: The directory to extract the capsule into. If not provided,
        a temporary directory will be created.

Returns:
    The path to the directory where the capsule was extracted.
"""
```

## `python/somaagent/context_builder.py`

### `SomabrainHealthState`

```python
"""Represents the health status of the Somabrain service."""
```

### `RedactorProtocol`

```python
"""Defines a protocol for redacting sensitive information from text."""
```

### `_NoopRedactor`

```python
"""A default redactor implementation that performs no redaction."""
```

### `BuiltContext`

```python
"""A data class representing the fully constructed context for an agent's turn.

Attributes:
    system_prompt: The system prompt for the agent.
    messages: A list of messages forming the conversation history and context.
    token_counts: A dictionary detailing the token counts for different parts of the context.
    debug: A dictionary containing debugging information about the context-building process.
"""
```

### `ContextBuilder`

```python
"""Builds the context for an agent's turn, integrating with the Somabrain service.

This class manages the retrieval of relevant information (snippets) from Somabrain,
handles token budget limitations by trimming history and snippets, redacts sensitive
information, and constructs the final list of messages to be sent to the language model.
It also monitors the health of the Somabrain service to adjust its behavior accordingly.
"""
```

### `ContextBuilder.__init__()`

```python
"""Initializes the ContextBuilder.

Args:
    somabrain: An instance of `SomaBrainClient` to communicate with the Somabrain service.
    metrics: An instance of `ContextBuilderMetrics` for tracking performance and health.
    token_counter: A callable that takes a string and returns the number of tokens.
    redactor: An optional object that conforms to the `RedactorProtocol` for redacting text.
    health_provider: An optional callable that returns the current `SomabrainHealthState`.
    on_degraded: An optional callable that is triggered when the Somabrain service becomes degraded.
"""
```

### `ContextBuilder.build_for_turn()`

```python
"""Constructs the full context for a single turn of a conversation.

This method orchestrates the process of fetching snippets, managing token budgets,
trimming history, and assembling the final prompt for the language model.

Args:
    turn: A dictionary containing data for the current turn, including the user message and history.
    max_prompt_tokens: The maximum number of tokens allowed for the entire prompt.

Returns:
    A `BuiltContext` object containing the system prompt, messages, token counts, and debug info.
"""
```

### `ContextBuilder._current_health()`

```python
"""Determines the current health state of the Somabrain service.

Returns:
    The current `SomabrainHealthState`. Defaults to DEGRADED if the health provider fails.
"""
```

### `ContextBuilder._coerce_history()`

```python
"""Ensures that the conversation history is in the correct format.

Args:
    history: The raw history object, which could be of any type.

Returns:
    A list of message dictionaries, with invalid entries filtered out.
"""
```

### `ContextBuilder._retrieve_snippets()`

```python
"""Retrieves context snippets from the Somabrain service.

Args:
    turn: The data for the current turn.
    state: The current health state of the Somabrain service.

Returns:
    A list of snippet dictionaries retrieved from Somabrain.
"""
```

### `ContextBuilder._extract_text()`

```python
"""Extracts the main text content from a Somabrain result item.

Args:
    item: A dictionary representing a single result from Somabrain.

Returns:
    The extracted text as a string.
"""
```

### `ContextBuilder._rank_and_clip_snippets()`

```python
"""Sorts snippets by score and clips the list to the appropriate size based on health.

Args:
    snippets: A list of snippet dictionaries.
    state: The current health state of the Somabrain service.

Returns:
    A sorted and clipped list of snippets.
"""
```

### `ContextBuilder._apply_salience()`

```python
"""Applies a salience score to each snippet, combining relevance and recency.

Args:
    snippets: A list of snippet dictionaries.

Returns:
    A list of snippets with updated scores reflecting their salience.
"""
```

### `ContextBuilder._safe_float()`

```python
"""Safely converts a value to a float.

Args:
    value: The value to convert.

Returns:
    The float representation of the value, or 0.0 if conversion fails.
"""
```

### `ContextBuilder._recency_boost()`

```python
"""Calculates a recency boost for a snippet based on its timestamp.

Args:
    metadata: The metadata dictionary for the snippet.
    now: The current UTC datetime.

Returns:
    A boost factor between 0.0 and 1.0.
"""
```

### `ContextBuilder._redact_snippets()`

```python
"""Applies redaction to the text of each snippet.

Args:
    snippets: A list of snippet dictionaries.

Returns:
    A list of snippets with their text redacted.
"""
```

### `ContextBuilder._count_snippet_tokens()`

```python
"""Counts the total number of tokens in a list of snippets.

Args:
    snippets: A list of snippet dictionaries.

Returns:
    The total token count.
"""
```

### `ContextBuilder._trim_snippets_to_budget()`

```python
"""Trims a list of snippets to fit within a given token budget.

Args:
    snippets: A list of snippet dictionaries.
    snippet_tokens: The current total token count of the snippets.
    allowed_tokens: The maximum number of tokens allowed.

Returns:
    A tuple containing the trimmed list of snippets and their new total token count.
"""
```

### `ContextBuilder._trim_history()`

```python
"""Trims the conversation history to fit within a given token budget.

Args:
    history: The list of message dictionaries.
    allowed_tokens: The maximum number of tokens allowed.

Returns:
    The trimmed list of message dictionaries.
"""
```

### `ContextBuilder._format_snippet_block()`

```python
"""Formats a list of snippets into a single string block for the prompt.

Args:
    snippets: A list of snippet dictionaries.

Returns:
    A formatted string containing the snippet information.
"""
```

### `ContextBuilder._store_summary()`

```python
"""Creates and stores an extractive summary of pruned history in SomaBrain.

Args:
    turn: The data for the current turn.
    original_history: The conversation history before trimming.
    trimmed_history: The conversation history after trimming.
"""
```

### `ContextBuilder._build_summary()`

```python
"""Builds an extractive summary from the messages that were pruned from the history.

Args:
    original_history: The conversation history before trimming.
    trimmed_history: The conversation history after trimming.

Returns:
    A summary string, capped at 1024 characters.
"""
```

## `python/tools/a2a_chat.py`

### `A2AChatTool`

```python
"""A tool for communicating with other FastA2A-compatible agents."""
```

### `A2AChatTool.execute()`

```python
"""Executes the A2A chat tool.

This method establishes a connection with a remote agent, sends a message, and
waits for a response. It manages the conversation context by storing and reusing
session IDs.

Args:
    agent_url: The URL of the remote agent.
    message: The message to send to the remote agent.
    attachments: An optional list of file attachments to include with the message.
    reset: A boolean indicating whether to start a new conversation.

Returns:
    A `Response` object containing the remote agent's reply.
"""
```

## `python/tools/behaviour_adjustment.py`

### `UpdateBehaviour`

```python
"""A tool for updating the agent's behavioral ruleset."""
```

### `UpdateBehaviour.execute()`

```python
"""Executes the behavior update process.

Args:
    adjustments: A string containing the proposed adjustments to the behavior.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with a confirmation message.
"""
```

### `update_behaviour()`

```python
"""Merges behavior adjustments with the current ruleset and updates the agent's behavior file.

Args:
    agent: The `Agent` instance.
    log_item: The `LogItem` to stream updates to.
    adjustments: The proposed adjustments to the behavior.
"""
```

### `get_custom_rules_file()`

```python
"""Gets the absolute path to the agent's custom behavior rules file.

Args:
    agent: The `Agent` instance.

Returns:
    The absolute path to the behavior rules file.
"""
```

### `read_rules()`

```python
"""Reads the agent's behavior rules, falling back to the default rules if no custom file exists.

Args:
    agent: The `Agent` instance.

Returns:
    A string containing the agent's behavior rules.
"""
```

## `python/tools/browser_agent.py`

### `State`

```python
"""Manages the state of the browser agent, including the browser session and task execution."""
```

### `State.create()`

```python
"""Creates a new `State` instance.

Args:
    agent: The `Agent` instance.

Returns:
    A new `State` instance.
"""
```

### `State.__init__()`

```python
"""Initializes the `State` instance.

Args:
    agent: The `Agent` instance.
"""
```

### `State.get_user_data_dir()`

```python
"""Gets the user data directory for the browser session.

Returns:
    The path to the user data directory.
"""
```

### `State.start_task()`

```python
"""Starts a new browser agent task.

Args:
    task: The task to be executed by the browser agent.

Returns:
    The deferred task instance.
"""
```

### `State.kill_task()`

```python
"""Kills the currently running browser agent task and closes the browser session."""
```

### `State.get_page()`

```python
"""Gets the current page of the browser session.

Returns:
    The current page, or `None` if the session is not active.
"""
```

### `State.get_selector_map()`

```python
"""Gets the selector map for the current page state.

Returns:
    A dictionary mapping selectors to elements.
"""
```

### `BrowserAgent`

```python
"""A tool for browsing the web and interacting with web pages."""
```

### `BrowserAgent.execute()`

```python
"""Executes the browser agent tool.

Args:
    message: The task to be executed by the browser agent.
    reset: Whether to reset the browser agent state.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with the result of the browser agent task.
"""
```

### `BrowserAgent.get_log_object()`

```python
"""Gets the log object for the browser agent tool.

Returns:
    The log object.
"""
```

### `BrowserAgent.get_update()`

```python
"""Gets an update from the browser agent, including a log and a screenshot.

Returns:
    A dictionary with the latest log and screenshot.
"""
```

### `BrowserAgent.prepare_state()`

```python
"""Prepares the state of the browser agent, creating a new state if necessary.

Args:
    reset: Whether to reset the state.
"""
```

### `BrowserAgent.update_progress()`

```python
"""Updates the progress of the browser agent task in the log.

Args:
    text: The progress text.
"""
```

### `get_use_agent_log()`

```python
"""Gets the activity log from the browser agent.

Args:
    use_agent: The `browser_use.Agent` instance.

Returns:
    A list of log messages.
"""
```

## `python/tools/call_subordinate.py`

### `Delegation`

```python
"""A tool for delegating tasks to a subordinate agent."""
```

### `Delegation.execute()`

```python
"""Executes the delegation tool.

This method creates a subordinate agent if one does not exist or if the `reset`
flag is set. It then sends a message to the subordinate agent and waits for a
response.

Args:
    message: The message to send to the subordinate agent.
    reset: Whether to reset the subordinate agent.
    **kwargs: Additional keyword arguments, including an optional `profile`
        for the subordinate agent.

Returns:
    A `Response` object with the result from the subordinate agent.
"""
```

### `Delegation.get_log_object()`

```python
"""Gets the log object for the delegation tool.

Returns:
    The log object.
"""
```

## `python/tools/catalog.py`

### `ToolCatalog`

```python
"""A minimal Tool Catalog singleton used by tests.

This class provides lookup, listing, and schema generation for a handful of
built-in tools. It is implemented as a singleton to ensure a single
source of truth for the tool catalog.
"""
```

### `ToolCatalog.get()`

```python
"""Gets the singleton instance of the ToolCatalog.

Returns:
    The singleton instance of the ToolCatalog.
"""
```

### `ToolCatalog.list_tools()`

```python
"""Lists all the tools in the catalog.

Returns:
    A list of `ToolDefinition` objects.
"""
```

### `ToolCatalog.alist_tools()`

```python
"""Asynchronously lists all the tools in the catalog.

Returns:
    A list of `ToolDefinition` objects.
"""
```

### `ToolCatalog.get_tool()`

```python
"""Gets a tool by name.

Args:
    name: The name of the tool to get.

Returns:
    The `ToolDefinition` object for the tool, or `None` if the tool is
    not found.
"""
```

### `ToolCatalog.aget_tool()`

```python
"""Asynchronously gets a tool by name.

Args:
    name: The name of the tool to get.

Returns:
    The `ToolDefinition` object for the tool, or `None` if the tool is
    not found.
"""
```

### `ToolCatalog.get_tools_schema()`

```python
"""Gets the OpenAPI schema for all the tools in the catalog.

Returns:
    A dictionary containing the OpenAPI schema for the tools.
"""
```

## `python/tools/code_execution_tool.py`

### `State`

```python
"""Represents the state of the code execution tool.

Attributes:
    ssh_enabled: A boolean indicating whether SSH is enabled.
    shells: A dictionary of active shell sessions.
"""
```

### `CodeExecution`

```python
"""A tool for executing code in different runtimes."""
```

### `CodeExecution.execute()`

```python
"""Executes the code execution tool.

This method determines the runtime and executes the code accordingly.
It supports Python, NodeJS, and terminal commands.

Args:
    **kwargs: A dictionary of arguments. Expected keys are:
        - runtime (str): The runtime to use (python, nodejs, terminal).
        - code (str): The code to execute.
        - session (int, optional): The session ID to use. Defaults to 0.

Returns:
    A `Response` object with the result of the code execution.
"""
```

### `CodeExecution.get_log_object()`

```python
"""Gets the log object for the code execution tool.

Returns:
    The log object.
"""
```

### `CodeExecution.get_heading()`

```python
"""Gets the heading for the log object.

Args:
    text: The text to include in the heading.

Returns:
    The heading string.
"""
```

### `CodeExecution.after_execution()`

```python
"""Adds the tool result to the agent's history.

Args:
    response: The response from the tool execution.
    **kwargs: Additional keyword arguments.
"""
```

### `CodeExecution.prepare_state()`

```python
"""Prepares the state of the code execution tool.

This method initializes the shell sessions and handles resetting the state.

Args:
    reset: A boolean indicating whether to reset the state.
    session: The session ID to prepare.

Returns:
    The prepared state.
"""
```

### `CodeExecution.execute_python_code()`

```python
"""Executes Python code in an iPython shell.

Args:
    session: The session ID to use.
    code: The Python code to execute.
    reset: A boolean indicating whether to reset the session.

Returns:
    The output of the code execution.
"""
```

### `CodeExecution.execute_nodejs_code()`

```python
"""Executes NodeJS code.

Args:
    session: The session ID to use.
    code: The NodeJS code to execute.
    reset: A boolean indicating whether to reset the session.

Returns:
    The output of the code execution.
"""
```

### `CodeExecution.execute_terminal_command()`

```python
"""Executes a terminal command.

Args:
    session: The session ID to use.
    command: The terminal command to execute.
    reset: A boolean indicating whether to reset the session.

Returns:
    The output of the command execution.
"""
```

### `CodeExecution.terminal_session()`

```python
"""Handles the terminal session for executing commands.

Args:
    session: The session ID to use.
    command: The command to execute.
    reset: A boolean indicating whether to reset the session.
    prefix: The prefix to add to the output.

Returns:
    The output of the command execution.
"""
```

### `CodeExecution.format_command_for_output()`

```python
"""Formats a command for output.

Args:
    command: The command to format.

Returns:
    The formatted command.
"""
```

### `CodeExecution.get_terminal_output()`

```python
"""Gets the output from the terminal.

This method reads the output from the shell session and handles timeouts
and dialog detection.

Args:
    session: The session ID to use.
    reset_full_output: A boolean indicating whether to reset the full output.
    first_output_timeout: The timeout for the first output.
    between_output_timeout: The timeout between outputs.
    dialog_timeout: The timeout for dialog detection.
    max_exec_timeout: The maximum execution timeout.
    sleep_time: The time to sleep between reads.
    prefix: The prefix to add to the output.

Returns:
    The output from the terminal.
"""
```

### `CodeExecution.reset_terminal()`

```python
"""Resets the terminal session.

Args:
    session: The session ID to reset.
    reason: The reason for the reset.

Returns:
    A response message.
"""
```

### `CodeExecution.get_heading_from_output()`

```python
"""Gets the heading from the output.

Args:
    output: The output to get the heading from.
    skip_lines: The number of lines to skip from the end.
    done: A boolean indicating whether the command is done.

Returns:
    The heading string.
"""
```

### `CodeExecution.fix_full_output()`

```python
"""Fixes the full output by removing escape characters and truncating.

Args:
    output: The output to fix.

Returns:
    The fixed output.
"""
```

## `python/tools/document_query.py`

### `DocumentQueryTool`

```python
"""A tool for querying documents."""
```

### `DocumentQueryTool.execute()`

```python
"""Executes the document query tool.

This method retrieves the content of a document or performs a question-answering
task on the document.

Args:
    **kwargs: A dictionary of arguments. Expected keys are:
        - document (str): The URI of the document to query.
        - queries (list[str], optional): A list of queries to ask the document.
        - query (str, optional): A single query to ask the document.

Returns:
    A `Response` object with the result of the query.
"""
```

## `python/tools/input.py`

### `Input`

```python
"""A tool for providing keyboard input to a terminal session."""
```

### `Input.execute()`

```python
"""Executes the input tool.

This method forwards the keyboard input to the code execution tool.

Args:
    keyboard (str): The keyboard input to send to the terminal.
    **kwargs: Additional keyword arguments.

Returns:
    The response from the code execution tool.
"""
```

### `Input.get_log_object()`

```python
"""Gets the log object for the input tool.

Returns:
    The log object.
"""
```

## `python/tools/memory_delete.py`

### `MemoryDelete`

```python
"""A tool for deleting memories."""
```

### `MemoryDelete.execute()`

```python
"""Executes the memory deletion tool.

Args:
    ids (str): A comma-separated string of memory IDs to delete.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with a message indicating the number of memories deleted.
"""
```

## `python/tools/memory_forget.py`

### `MemoryForget`

```python
"""A tool for forgetting memories based on a query."""
```

### `MemoryForget.execute()`

```python
"""Executes the memory forget tool.

Args:
    query (str): The query to search for memories to forget.
    threshold (float): The similarity threshold to use when searching for memories.
    filter (str): A filter to apply to the search.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with a message indicating the number of memories forgotten.
"""
```

## `python/tools/memory_load.py`

### `MemoryLoad`

```python
"""A tool for loading memories based on a query."""
```

### `MemoryLoad.execute()`

```python
"""Executes the memory load tool.

Args:
    query (str): The query to search for memories.
    threshold (float): The similarity threshold to use when searching for memories.
    limit (int): The maximum number of memories to return.
    filter (str): A filter to apply to the search.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with the loaded memories.
"""
```

## `python/tools/memory_save.py`

### `MemorySave`

```python
"""A tool for saving memories."""
```

### `MemorySave.execute()`

```python
"""Executes the memory save tool.

Args:
    text (str): The text of the memory to save.
    area (str): The area to save the memory in.
    **kwargs: Additional keyword arguments to be stored as metadata.

Returns:
    A `Response` object with a message indicating the memory has been saved.
"""
```

## `python/tools/models.py`

### `ToolParameter`

```python
"""Represents a parameter for a tool.

Attributes:
    name: The name of the parameter.
    type: The type of the parameter.
    description: The description of the parameter.
    required: Whether the parameter is required.
    default: The default value of the parameter.
"""
```

### `ToolParameter.normalized_type()`

```python
"""Return a Python-esque type name for tests while keeping original.

Maps JSON Schema numeric types ("integer", "number") to Python's
"int" / "float" for comparison in test expectations.

Returns:
    The normalized type name.
"""
```

### `ToolDefinition`

```python
"""Represents the definition of a tool.

Attributes:
    name: The name of the tool.
    description: The description of the tool.
    parameters: A list of parameters for the tool.
    category: The category of the tool.
"""
```

### `ToolDefinition.to_openapi_function()`

```python
"""Converts the tool definition to an OpenAPI function dictionary.

Returns:
    A dictionary representing the tool in OpenAPI format.
"""
```

## `python/tools/notify_user.py`

### `NotifyUserTool`

```python
"""A tool for sending notifications to the user."""
```

### `NotifyUserTool.execute()`

```python
"""Executes the notify user tool.

Args:
    **kwargs: A dictionary of arguments. Expected keys are:
        - message (str): The message to send in the notification.
        - title (str, optional): The title of the notification.
        - detail (str, optional): The detail text of the notification.
        - type (str, optional): The type of the notification (e.g., info, warning, error).
        - priority (str, optional): The priority of the notification (e.g., low, high).
        - timeout (int, optional): The timeout for the notification in seconds.

Returns:
    A `Response` object with a message indicating the notification has been sent.
"""
```

## `python/tools/response.py`

### `ResponseTool`

```python
"""A tool for sending a final response to the user."""
```

### `ResponseTool.execute()`

```python
"""Executes the response tool.

This method returns a `Response` object that breaks the message loop
and sends the final response to the user.

Args:
    **kwargs: A dictionary of arguments. Expected keys are `text` or `message`.

Returns:
    A `Response` object with the final message.
"""
```

### `ResponseTool.before_execution()`

```python
"""Does nothing before execution."""
```

### `ResponseTool.after_execution()`

```python
"""Marks the response message as finished after execution."""
```

## `python/tools/scheduler.py`

### `SchedulerTool`

```python
"""A tool for managing scheduled, ad-hoc, and planned tasks."""
```

### `SchedulerTool.execute()`

```python
"""Executes the scheduler tool.

This method routes the request to the appropriate method based on the `method`
argument.

Args:
    **kwargs: A dictionary of arguments. The `method` key is required.

Returns:
    A `Response` object with the result of the method execution.
"""
```

### `SchedulerTool.list_tasks()`

```python
"""Lists all tasks, with optional filtering.

Args:
    **kwargs: A dictionary of arguments. Optional keys are:
        - state (list[str]): A list of states to filter by.
        - type (list[str]): A list of types to filter by.
        - next_run_within (int): Filter by next run within this many minutes.
        - next_run_after (int): Filter by next run after this many minutes.

Returns:
    A `Response` object with a JSON array of tasks.
"""
```

### `SchedulerTool.find_task_by_name()`

```python
"""Finds a task by name.

Args:
    **kwargs: A dictionary of arguments. The `name` key is required.

Returns:
    A `Response` object with a JSON array of tasks.
"""
```

### `SchedulerTool.show_task()`

```python
"""Shows the details of a task.

Args:
    **kwargs: A dictionary of arguments. The `uuid` key is required.

Returns:
    A `Response` object with a JSON object of the task.
"""
```

### `SchedulerTool.run_task()`

```python
"""Runs a task.

Args:
    **kwargs: A dictionary of arguments. The `uuid` key is required.

Returns:
    A `Response` object with a message indicating the task has started.
"""
```

### `SchedulerTool.delete_task()`

```python
"""Deletes a task.

Args:
    **kwargs: A dictionary of arguments. The `uuid` key is required.

Returns:
    A `Response` object with a message indicating the task has been deleted.
"""
```

### `SchedulerTool.create_scheduled_task()`

```python
"""Creates a scheduled task.

Args:
    **kwargs: A dictionary of arguments. Expected keys are:
        - name (str): The name of the task.
        - system_prompt (str): The system prompt for the task.
        - prompt (str): The prompt for the task.
        - attachments (list[str]): A list of attachments for the task.
        - schedule (dict[str, str]): The cron schedule for the task.
        - dedicated_context (bool): Whether to run the task in a dedicated context.

Returns:
    A `Response` object with a message indicating the task has been created.
"""
```

### `SchedulerTool.create_adhoc_task()`

```python
"""Creates an ad-hoc task.

Args:
    **kwargs: A dictionary of arguments. Expected keys are:
        - name (str): The name of the task.
        - system_prompt (str): The system prompt for the task.
        - prompt (str): The prompt for the task.
        - attachments (list[str]): A list of attachments for the task.
        - dedicated_context (bool): Whether to run the task in a dedicated context.

Returns:
    A `Response` object with a message indicating the task has been created.
"""
```

### `SchedulerTool.create_planned_task()`

```python
"""Creates a planned task.

Args:
    **kwargs: A dictionary of arguments. Expected keys are:
        - name (str): The name of the task.
        - system_prompt (str): The system prompt for the task.
        - prompt (str): The prompt for the task.
        - attachments (list[str]): A list of attachments for the task.
        - plan (list[str]): A list of datetimes for the task plan.
        - dedicated_context (bool): Whether to run the task in a dedicated context.

Returns:
    A `Response` object with a message indicating the task has been created.
"""
```

### `SchedulerTool.wait_for_task()`

```python
"""Waits for a task to complete.

Args:
    **kwargs: A dictionary of arguments. The `uuid` key is required.

Returns:
    A `Response` object with the result of the task.
"""
```

## `python/tools/search_engine.py`

### `SearchEngine`

```python
"""A tool for searching the web using SearXNG."""
```

### `SearchEngine.execute()`

```python
"""Executes the search engine tool.

Args:
    query (str): The search query.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with the search results.
"""
```

### `SearchEngine.searxng_search()`

```python
"""Performs a search using SearXNG.

Args:
    question (str): The search query.

Returns:
    The formatted search results.
"""
```

### `SearchEngine.format_result_searxng()`

```python
"""Formats the search results from SearXNG.

Args:
    result (dict): The search results from SearXNG.
    source (str): The source of the search results.

Returns:
    The formatted search results as a string.
"""
```

## `python/tools/unknown.py`

### `Unknown`

```python
"""A tool that is executed when an unknown tool is called."""
```

### `Unknown.execute()`

```python
"""Executes the unknown tool.

This method returns a message indicating that the tool was not found
and provides a list of available tools.

Args:
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with an error message.
"""
```

## `python/tools/vision_load.py`

### `VisionLoad`

```python
"""A tool for loading and processing images for vision-enabled models."""
```

### `VisionLoad.execute()`

```python
"""Executes the vision load tool.

This method processes a list of image paths, compresses and encodes them,
and prepares them for use by a vision-enabled model.

Args:
    paths (list[str]): A list of paths to the images to load.
    **kwargs: Additional keyword arguments.

Returns:
    A `Response` object with a message indicating the number of images processed.
"""
```

### `VisionLoad.after_execution()`

```python
"""Adds the processed images to the agent's history.

Args:
    response: The response from the tool execution.
    **kwargs: Additional keyword arguments.
"""
```

## `python/helpers/api.py`

### `ApiHandler`

```python
"""A base class for handling API requests."""
```

### `ApiHandler.__init__()`

```python
"""Initializes the ApiHandler.

Args:
    app: The Flask application instance.
    thread_lock: A lock for synchronizing threads.
"""
```

### `ApiHandler.requires_loopback()`

```python
"""Returns whether the handler requires a loopback connection."""
```

### `ApiHandler.requires_api_key()`

```python
"""Returns whether the handler requires an API key."""
```

### `ApiHandler.requires_auth()`

```python
"""Returns whether the handler requires authentication."""
```

### `ApiHandler.get_methods()`

```python
"""Returns the HTTP methods supported by the handler."""
```

### `ApiHandler.requires_csrf()`

```python
"""Returns whether the handler requires CSRF protection."""
```

### `ApiHandler.process()`

```python
"""Processes the API request.

This method must be implemented by subclasses.

Args:
    input: The input data from the request.
    request: The Flask request object.

Returns:
    The output to be sent in the response.
"""
```

### `ApiHandler.handle_request()`

```python
"""Handles an incoming API request.

Args:
    request: The Flask request object.

Returns:
    A Flask response object.
"""
```

### `ApiHandler.get_context()`

```python
"""Gets the agent context for a given context ID.

If no context ID is provided, it returns the first available context or
creates a new one.

Args:
    ctxid: The context ID.

Returns:
    The agent context.
"""
```

## `python/helpers/attachment_manager.py`

### `AttachmentManager`

```python
"""A class for managing file attachments."""
```

### `AttachmentManager.__init__()`

```python
"""Initializes the AttachmentManager.

Args:
    work_dir: The directory to save attachments in.
"""
```

### `AttachmentManager.is_allowed_file()`

```python
"""Checks if a file has an allowed extension.

Args:
    filename: The name of the file.

Returns:
    True if the file is allowed, False otherwise.
"""
```

### `AttachmentManager.get_file_type()`

```python
"""Gets the type of a file based on its extension.

Args:
    filename: The name of the file.

Returns:
    The type of the file (e.g., image, code, document).
"""
```

### `AttachmentManager.get_file_extension()`

```python
"""Gets the extension of a file.

Args:
    filename: The name of the file.

Returns:
    The extension of the file.
"""
```

### `AttachmentManager.validate_mime_type()`

```python
"""Validates the MIME type of a file.

Args:
    file: The file to validate.

Returns:
    True if the MIME type is valid, False otherwise.
"""
```

### `AttachmentManager.save_file()`

```python
"""Saves a file and returns its path and metadata.

Args:
    file: The file to save.
    filename: The name of the file.

Returns:
    A tuple containing the path to the saved file and its metadata.
"""
```

### `AttachmentManager.generate_image_preview()`

```python
"""Generates a base64-encoded preview for an image.

Args:
    image_path: The path to the image.
    max_size: The maximum size of the preview image.

Returns:
    A base64-encoded string of the preview image, or None if an error occurs.
"""
```

## `python/helpers/backup.py`

### `BackupService`

```python
"""A service for creating and restoring backups of Agent Zero."""
```

### `BackupService.__init__()`

```python
"""Initializes the BackupService."""
```

### `BackupService.get_default_backup_metadata()`

```python
"""Gets the default backup patterns and metadata.

Returns:
    A dictionary containing the default backup metadata.
"""
```

### `BackupService.test_patterns()`

```python
"""Tests the backup patterns and returns a list of matched files.

Args:
    metadata: The backup metadata containing the patterns to test.
    max_files: The maximum number of files to return.

Returns:
    A list of dictionaries, where each dictionary represents a matched file.
"""
```

### `BackupService.create_backup()`

```python
"""Creates a backup archive and returns the path to the created file.

Args:
    include_patterns: A list of patterns to include in the backup.
    exclude_patterns: A list of patterns to exclude from the backup.
    include_hidden: Whether to include hidden files and directories.
    backup_name: The name of the backup file.

Returns:
    The path to the created backup file.
"""
```

### `BackupService.inspect_backup()`

```python
"""Inspects a backup archive and returns its metadata.

Args:
    backup_file: The backup file to inspect.

Returns:
    A dictionary containing the backup metadata.
"""
```

### `BackupService.preview_restore()`

```python
"""Previews which files would be restored based on the given patterns.

Args:
    backup_file: The backup file to preview.
    restore_include_patterns: A list of patterns to include in the restore.
    restore_exclude_patterns: A list of patterns to exclude from the restore.
    overwrite_policy: The policy to use when a file already exists.
    clean_before_restore: Whether to clean the destination before restoring.
    user_edited_metadata: User-edited metadata to use for the preview.

Returns:
    A dictionary containing the preview of the restore operation.
"""
```

### `BackupService.restore_backup()`

```python
"""Restores files from a backup archive.

Args:
    backup_file: The backup file to restore from.
    restore_include_patterns: A list of patterns to include in the restore.
    restore_exclude_patterns: A list of patterns to exclude from the restore.
    overwrite_policy: The policy to use when a file already exists.
    clean_before_restore: Whether to clean the destination before restoring.
    user_edited_metadata: User-edited metadata to use for the restore.

Returns:
    A dictionary containing the result of the restore operation.
"""
```

## `python/helpers/browser_use_monkeypatch.py`

### `gemini_clean_and_conform()`

```python
"""Sanitizes and conforms JSON output from Gemini to match browser-use schema.

This function handles markdown fences, aliases actions (e.g., 'complete_task' to 'done'),
and constructs a valid 'data' object for the final action.

Args:
    text: The raw text output from the Gemini model.

Returns:
    A JSON string conforming to the browser-use schema, or None if parsing fails.
"""
```

### `apply()`

```python
"""Applies the monkey-patch to `browser_use.llm.ChatGoogle`."""
```

## `python/helpers/call_llm.py`

### `call_llm()`

```python
"""Calls a language model with a system message, user message, and optional few-shot examples.

Args:
    system: The system message to send to the model.
    model: The language model to call.
    message: The user message to send to the model.
    examples: A list of few-shot examples to include in the prompt.
    callback: An optional callback function to receive streaming responses.

Returns:
    The full response from the language model.
"""
```

## `python/helpers/circuit_breaker.py`

### `ensure_metrics_exporter()`

```python
"""Starts the standalone Prometheus exporter if a port is configured.

The helper is opt-in to avoid binding ports in every consumer process. Set
`CIRCUIT_BREAKER_METRICS_PORT` (and optionally `CIRCUIT_BREAKER_METRICS_HOST`)
in the environment of a long-lived service and call this function during
startup to expose the counters defined in this module.
"""
```

### `CircuitOpenError`

```python
"""Raised when the circuit is open and a call is blocked."""
```

### `circuit_breaker()`

```python
"""A decorator that wraps a function with circuit-breaker logic.

Args:
    failure_threshold: The number of consecutive failures before opening the circuit.
    reset_timeout: The number of seconds to wait before attempting to close the circuit.

Returns:
    A decorator that can be applied to a function.
"""
```

## `python/helpers/cloudflare_tunnel._py`

### `CloudflareTunnel`

```python
"""A class for managing a Cloudflare Tunnel."""
```

### `CloudflareTunnel.__init__()`

```python
"""Initializes the CloudflareTunnel.

Args:
    port: The port to expose through the tunnel.
"""
```

### `CloudflareTunnel.download_cloudflared()`

```python
"""Downloads the appropriate cloudflared binary for the current system."""
```

### `CloudflareTunnel.start()`

```python
"""Starts the Cloudflare tunnel."""
```

### `CloudflareTunnel.stop()`

```python
"""Stops the Cloudflare tunnel."""
```

## `python/helpers/crypto.py`

### `hash_data()`

```python
"""Hashes data using HMAC-SHA256.

Args:
    data: The data to hash.
    password: The password to use for hashing.

Returns:
    The hashed data as a hex digest.
"""
```

### `verify_data()`

```python
"""Verifies data against a hash.

Args:
    data: The data to verify.
    hash: The hash to verify against.
    password: The password used for hashing.

Returns:
    True if the data matches the hash, False otherwise.
"""
```

### `encrypt_data()`

```python
"""Encrypts data using a public key.

Args:
    data: The data to encrypt.
    public_key_pem: The public key in PEM format as a hex string.

Returns:
    The encrypted data as a hex string.
"""
```

### `decrypt_data()`

```python
"""Decrypts data using a private key.

Args:
    data: The encrypted data as a hex string.
    private_key: The private key object.

Returns:
    The decrypted data as a string.
"""
```

## `python/helpers/defer.py`

### `EventLoopThread`

```python
"""A singleton class that manages a background thread with an event loop."""
```

### `EventLoopThread.__init__()`

```python
"""Initializes the event loop thread."""
```

### `EventLoopThread.terminate()`

```python
"""Terminates the event loop thread."""
```

### `EventLoopThread.run_coroutine()`

```python
"""Runs a coroutine in the event loop thread.

Args:
    coro: The coroutine to run.

Returns:
    A future representing the result of the coroutine.
"""
```

### `ChildTask`

```python
"""A data class that represents a child task."""
```

### `DeferredTask`

```python
"""A class for running a coroutine in a background thread."""
```

### `DeferredTask.__init__()`

```python
"""Initializes the DeferredTask.

Args:
    thread_name: The name of the background thread.
"""
```

### `DeferredTask.start_task()`

```python
"""Starts the task.

Args:
    func: The coroutine function to run.
    *args: The arguments to pass to the function.
    **kwargs: The keyword arguments to pass to the function.

Returns:
    The DeferredTask instance.
"""
```

### `DeferredTask.is_ready()`

```python
"""Returns whether the task is ready."""
```

### `DeferredTask.result_sync()`

```python
"""Gets the result of the task synchronously.

Args:
    timeout: The maximum time to wait for the result.

Returns:
    The result of the task.
"""
```

### `DeferredTask.result()`

```python
"""Gets the result of the task asynchronously.

Args:
    timeout: The maximum time to wait for the result.

Returns:
    The result of the task.
"""
```

### `DeferredTask.kill()`

```python
"""Kills the task and optionally terminates its thread."""
```

### `DeferredTask.kill_children()`

```python
"""Kills all child tasks."""
```

### `DeferredTask.is_alive()`

```python
"""Returns whether the task is alive."""
```

### `DeferredTask.restart()`

```python
"""Restarts the task."""
```

### `DeferredTask.add_child_task()`

```python
"""Adds a child task.

Args:
    task: The child task to add.
    terminate_thread: Whether to terminate the thread when the child task is killed.
"""
```

### `DeferredTask.execute_inside()`

```python
"""Executes a function inside the task's event loop.

Args:
    func: The function to execute.
    *args: The arguments to pass to the function.
    **kwargs: The keyword arguments to pass to the function.

Returns:
    An awaitable that resolves with the result of the function.
"""
```

## `python/helpers/dirty_json.py`

### `try_parse()`

```python
"""Tries to parse a JSON string, falling back to a dirty JSON parser if needed.

Args:
    json_string: The JSON string to parse.

Returns:
    The parsed JSON object, or None if parsing fails.
"""
```

### `parse()`

```python
"""Parses a JSON string using a dirty JSON parser.

Args:
    json_string: The JSON string to parse.

Returns:
    The parsed JSON object, or None if parsing fails.
"""
```

### `stringify()`

```python
"""Converts a Python object to a JSON string.

Args:
    obj: The object to convert.
    **kwargs: Additional keyword arguments to pass to `json.dumps`.

Returns:
    The JSON string representation of the object.
"""
```

### `DirtyJson`

```python
"""A parser for dirty JSON strings that are not strictly compliant with the JSON standard."""
```

### `DirtyJson.parse_string()`

```python
"""Parses a JSON string.

Args:
    json_string: The JSON string to parse.

Returns:
    The parsed JSON object, or None if parsing fails.
"""
```

### `DirtyJson.parse()`

```python
"""Parses a JSON string.

Args:
    json_string: The JSON string to parse.

Returns:
    The parsed JSON object, or None if parsing fails.
"""
```

### `DirtyJson.feed()`

```python
"""Feeds a chunk of a JSON string to the parser.

Args:
    chunk: The chunk of the JSON string to feed.

Returns:
    The parsed JSON object, or None if parsing is not complete.
"""
```

## `python/helpers/docker.py`

### `DockerContainerManager`

```python
"""A class for managing Docker containers."""
```

### `DockerContainerManager.__init__()`

```python
"""Initializes the DockerContainerManager.

Args:
    image: The name of the Docker image to use.
    name: The name to give the container.
    ports: A dictionary of port mappings.
    volumes: A dictionary of volume mappings.
    logger: An optional logger instance.
"""
```

### `DockerContainerManager.init_docker()`

```python
"""Initializes the Docker client."""
```

### `DockerContainerManager.cleanup_container()`

```python
"""Stops and removes the container."""
```

### `DockerContainerManager.get_image_containers()`

```python
"""Gets a list of containers for the image.

Returns:
    A list of dictionaries, where each dictionary contains information
    about a container.
"""
```

### `DockerContainerManager.start_container()`

```python
"""Starts a container.

If a container with the same name already exists, it will be started.
Otherwise, a new container will be created.
"""
```

## `python/helpers/dotenv.py`

### `load_dotenv()`

```python
"""Loads environment variables from the .env file."""
```

### `get_dotenv_file_path()`

```python
"""Gets the absolute path to the .env file.

Returns:
    The absolute path to the .env file.
"""
```

### `get_dotenv_value()`

```python
"""Gets an environment variable with production-friendly fallbacks.

The resolution order is as follows (the first non-empty value wins):
1. The value of the environment variable `key`.
2. The contents of the file specified by the environment variable `key_FILE`.
3. The base64-decoded value of the environment variable `key_B64`.
4. The base64-decoded contents of the file specified by the environment variable `key_B64_FILE`.

If a file-based value is loaded, this function also sets `os.environ[key]` so that
downstream libraries that only read `key` will continue to work.

Args:
    key: The name of the environment variable.
    default: The default value to return if the environment variable is not found.

Returns:
    The value of the environment variable, or the default value if it is not found.
"""
```

### `save_dotenv_value()`

```python
"""Saves a value to the .env file.

Args:
    key: The key of the environment variable.
    value: The value to save.
"""
```

## `python/helpers/errors.py`

### `handle_error()`

```python
"""Handles an exception, re-raising it if it is a `CancelledError`."""
```

### `error_text()`

```python
"""Returns the string representation of an exception.

Args:
    e: The exception.

Returns:
    The string representation of the exception.
"""
```

### `format_error()`

```python
"""Formats an exception and its traceback into a human-readable string.

Args:
    e: The exception to format.
    start_entries: The number of traceback entries to show from the beginning.
    end_entries: The number of traceback entries to show from the end.

Returns:
    The formatted error string.
"""
```

### `RepairableException`

```python
"""An exception type indicating errors that can be surfaced to the LLM for potential self-repair."""
```

## `python/helpers/extension.py`

### `Extension`

```python
"""A base class for creating extensions."""
```

### `Extension.__init__()`

```python
"""Initializes the Extension.

Args:
    agent: The agent instance.
    **kwargs: Additional keyword arguments.
"""
```

### `Extension.execute()`

```python
"""Executes the extension.

This method must be implemented by subclasses.

Args:
    **kwargs: Additional keyword arguments.
"""
```

### `call_extensions()`

```python
"""Calls all extensions for a given extension point.

Args:
    extension_point: The name of the extension point to call.
    agent: The agent instance.
    **kwargs: Additional keyword arguments to pass to the extensions.
"""
```

## `python/helpers/extract_tools.py`

### `json_parse_dirty()`

```python
"""Parses a dirty JSON string into a dictionary.

Args:
    json: The dirty JSON string to parse.

Returns:
    A dictionary representing the parsed JSON, or None if parsing fails.
"""
```

### `extract_json_object_string()`

```python
"""Extracts a JSON object string from a larger string.

Args:
    content: The string to extract the JSON object from.

Returns:
    The extracted JSON object string, or an empty string if no object is found.
"""
```

### `extract_json_string()`

```python
"""Extracts a JSON string from a larger string using a regular expression.

Args:
    content: The string to extract the JSON from.

Returns:
    The extracted JSON string, or an empty string if no JSON is found.
"""
```

### `fix_json_string()`

```python
"""Fixes a JSON string by escaping unescaped line breaks within string values.

Args:
    json_string: The JSON string to fix.

Returns:
    The fixed JSON string.
"""
```

### `import_module()`

```python
"""Imports a Python module from a file path.

Args:
    file_path: The path to the Python file to import.

Returns:
    The imported module.

Raises:
    ImportError: If the module file is not found or cannot be loaded.
"""
```

### `load_classes_from_folder()`

```python
"""Loads all classes from a folder that match a given pattern and are subclasses of a given base class.

Args:
    folder: The folder to search for classes.
    name_pattern: The pattern to match file names against.
    base_class: The base class to filter by.
    one_per_file: Whether to load only one class per file.

Returns:
    A list of the loaded classes.
"""
```

### `load_classes_from_file()`

```python
"""Loads all classes from a file that are subclasses of a given base class.

Args:
    file: The file to load classes from.
    base_class: The base class to filter by.
    one_per_file: Whether to load only one class per file.

Returns:
    A list of the loaded classes.
"""
```

## `python/helpers/fasta2a_client.py`

### `AgentConnection`

```python
"""A helper class for connecting to and communicating with other Agent Zero instances via FastA2A."""
```

### `AgentConnection.__init__()`

```python
"""Initializes a connection to an agent.

Args:
    agent_url: The base URL of the agent (e.g., "https://agent.example.com").
    timeout: The request timeout in seconds.
    token: The authentication token.
"""
```

### `AgentConnection.get_agent_card()`

```python
"""Retrieves the agent card from the remote agent.

Returns:
    A dictionary containing the agent card information.
"""
```

### `AgentConnection.send_message()`

```python
"""Sends a message to the remote agent and returns the task response.

Args:
    message: The message to send.
    attachments: A list of attachment URLs.
    context_id: The context ID to use for the conversation.
    metadata: Additional metadata to send with the message.

Returns:
    A dictionary containing the task response.
"""
```

### `AgentConnection.get_task()`

```python
"""Gets the status and results of a task.

Args:
    task_id: The ID of the task to query.

Returns:
    A dictionary containing the task information.
"""
```

### `AgentConnection.wait_for_completion()`

```python
"""Waits for a task to complete and returns the final result.

Args:
    task_id: The ID of the task to wait for.
    poll_interval: How often to check the task status in seconds.
    max_wait: The maximum time to wait in seconds.

Returns:
    A dictionary containing the completed task information.
"""
```

### `AgentConnection.close()`

```python
"""Closes the HTTP client connection."""
```

### `connect_to_agent()`

```python
"""Creates a connection to a remote agent.

Args:
    agent_url: The base URL of the agent.
    timeout: The request timeout in seconds.

Returns:
    An `AgentConnection` instance.
"""
```

### `is_client_available()`

```python
"""Checks if the FastA2A client is available.

Returns:
    True if the client is available, False otherwise.
"""
```

## `python/helpers/fasta2a_server.py`

### `AgentZeroWorker`

```python
"""Agent Zero implementation of a FastA2A Worker."""
```

### `AgentZeroWorker.__init__()`

```python
"""Initializes the AgentZeroWorker.

Args:
    broker: The message broker.
    storage: The storage backend.
"""
```

### `AgentZeroWorker.run_task()`

```python
"""Executes a task by processing a message through Agent Zero.

Args:
    params: The task parameters.
"""
```

### `AgentZeroWorker.cancel_task()`

```python
"""Cancels a running task.

Args:
    params: The task parameters.
"""
```

### `AgentZeroWorker.build_message_history()`

```python
"""Builds a message history. Not used in this implementation."""
```

### `AgentZeroWorker.build_artifacts()`

```python
"""Builds a list of artifacts. Not used in this implementation."""
```

### `DynamicA2AProxy`

```python
"""A dynamic proxy for a FastA2A server that allows for reconfiguration."""
```

### `DynamicA2AProxy.__init__()`

```python
"""Initializes the DynamicA2AProxy."""
```

### `DynamicA2AProxy.get_instance()`

```python
"""Gets the singleton instance of the DynamicA2AProxy."""
```

### `DynamicA2AProxy.reconfigure()`

```python
"""Reconfigures the FastA2A server with a new token.

Args:
    token: The new authentication token.
"""
```

### `DynamicA2AProxy.__call__()`

```python
"""The ASGI application interface with token-based routing."""
```

### `is_available()`

```python
"""Check if FastA2A is available and properly configured."""
```

### `get_proxy()`

```python
"""Get the FastA2A proxy instance."""
```

## `python/helpers/file_browser.py`

### `FileBrowser`

```python
"""A class for browsing and managing files."""
```

### `FileBrowser.__init__()`

```python
"""Initializes the FileBrowser."""
```

### `FileBrowser.save_file_b64()`

```python
"""Saves a base64-encoded file.

Args:
    current_path: The path to save the file in.
    filename: The name of the file.
    base64_content: The base64-encoded content of the file.

Returns:
    True if the file was saved successfully, False otherwise.
"""
```

### `FileBrowser.save_files()`

```python
"""Saves uploaded files and returns the successful and failed filenames.

Args:
    files: A list of files to save.
    current_path: The path to save the files in.

Returns:
    A tuple containing two lists: the names of the successfully saved files
    and the names of the files that failed to save.
"""
```

### `FileBrowser.delete_file()`

```python
"""Deletes a file or an empty directory.

Args:
    file_path: The path to the file or directory to delete.

Returns:
    True if the file or directory was deleted successfully, False otherwise.
"""
```

### `FileBrowser.get_files()`

```python
"""Gets a list of files and folders in a directory.

Args:
    current_path: The path to the directory to list.

Returns:
    A dictionary containing the list of entries, the current path, and
    the parent path.
"""
```

### `FileBrowser.get_full_path()`

```python
"""Gets the full path to a file if it exists and is within the base directory.

Args:
    file_path: The path to the file.
    allow_dir: Whether to allow directories.

Returns:
    The full path to the file.
"""
```

## `python/helpers/files.py`

### `load_plugin_variables()`

```python
"""Loads variables from a plugin file.

Args:
    file: The path to the file.
    backup_dirs: A list of backup directories to search for the plugin file.

Returns:
    A dictionary of variables, or an empty dictionary if no plugin is found.
"""
```

### `parse_file()`

```python
"""Parses a file, replacing placeholders and processing include statements.

Args:
    _filename: The name of the file to parse.
    _directories: A list of directories to search for the file.
    _encoding: The encoding of the file.
    **kwargs: Additional keyword arguments to use as placeholders.

Returns:
    The parsed content of the file.
"""
```

### `read_prompt_file()`

```python
"""Reads a prompt file, replacing placeholders and processing include statements.

Args:
    _file: The name of the file to read.
    _directories: A list of directories to search for the file.
    _encoding: The encoding of the file.
    **kwargs: Additional keyword arguments to use as placeholders.

Returns:
    The content of the file with placeholders replaced and includes processed.
"""
```

### `read_file()`

```python
"""Reads the content of a file.

Args:
    relative_path: The relative path to the file.
    encoding: The encoding of the file.

Returns:
    The content of the file.
"""
```

### `read_file_bin()`

```python
"""Reads the binary content of a file.

Args:
    relative_path: The relative path to the file.

Returns:
    The binary content of the file.
"""
```

### `read_file_base64()`

```python
"""Reads the base64-encoded content of a file.

Args:
    relative_path: The relative path to the file.

Returns:
    The base64-encoded content of the file.
"""
```

### `replace_placeholders_text()`

```python
"""Replaces placeholders in a string with the given values.

Args:
    _content: The string to replace placeholders in.
    **kwargs: The placeholder values.

Returns:
    The string with placeholders replaced.
"""
```

### `replace_placeholders_json()`

```python
"""Replaces placeholders in a JSON string with the given values.

Args:
    _content: The JSON string to replace placeholders in.
    **kwargs: The placeholder values.

Returns:
    The JSON string with placeholders replaced.
"""
```

### `replace_placeholders_dict()`

```python
"""Recursively replaces placeholders in a dictionary.

Args:
    _content: The dictionary to replace placeholders in.
    **kwargs: The placeholder values.

Returns:
    The dictionary with placeholders replaced.
"""
```

### `process_includes()`

```python
"""Processes `{{ include 'path' }}` statements in a string.

Args:
    _content: The string to process.
    _directories: A list of directories to search for the included files.
    **kwargs: Additional keyword arguments to pass to the included files.

Returns:
    The string with include statements replaced by the content of the files.
"""
```

### `find_file_in_dirs()`

```python
"""Searches for a file in a list of directories and returns the absolute path of the first match.

Args:
    _filename: The name of the file to search for.
    _directories: A list of directories to search in.

Returns:
    The absolute path of the first found file.

Raises:
    FileNotFoundError: If the file is not found in any of the directories.
"""
```

### `get_unique_filenames_in_dirs()`

```python
"""Gets a list of unique filenames from a list of directories, with priority given by the order of the directories.

Args:
    dir_paths: A list of directory paths to search.
    pattern: A glob pattern to filter files by.

Returns:
    A sorted list of absolute paths to the unique files.
"""
```

### `remove_code_fences()`

```python
"""Removes code fences (``` or ~~~) from a string.

Args:
    text: The string to remove code fences from.

Returns:
    The string with code fences removed.
"""
```

### `is_full_json_template()`

```python
"""Checks if a string is a full JSON template enclosed in code fences.

Args:
    text: The string to check.

Returns:
    True if the string is a full JSON template, False otherwise.
"""
```

### `write_file()`

```python
"""Writes content to a file.

Args:
    relative_path: The relative path to the file.
    content: The content to write to the file.
    encoding: The encoding of the file.
"""
```

### `write_file_bin()`

```python
"""Writes binary content to a file.

Args:
    relative_path: The relative path to the file.
    content: The binary content to write to the file.
"""
```

### `write_file_base64()`

```python
"""Writes base64-encoded content to a file.

Args:
    relative_path: The relative path to the file.
    content: The base64-encoded content to write to the file.
"""
```

### `delete_dir()`

```python
"""Deletes a directory and its contents.

Args:
    relative_path: The relative path to the directory to delete.
"""
```

### `list_files()`

```python
"""Lists the files in a directory.

Args:
    relative_path: The relative path to the directory.
    filter: A glob pattern to filter the files by.

Returns:
    A list of the files in the directory.
"""
```

### `make_dirs()`

```python
"""Creates a directory and any necessary parent directories.

Args:
    relative_path: The relative path to the directory to create.
"""
```

### `get_abs_path()`

```python
"""Converts a relative path to an absolute path based on the base directory."""
```

### `deabsolute_path()`

```python
"""Converts an absolute path to a relative path based on the base directory."""
```

### `fix_dev_path()`

```python
"""Converts legacy /a0/ paths to modern /git/agent-zero/ paths in a development environment."""
```

### `exists()`

```python
"""Checks if a file or directory exists.

Args:
    *relative_paths: The relative path to the file or directory.

Returns:
    True if the file or directory exists, False otherwise.
"""
```

### `get_base_dir()`

```python
"""Gets the base directory of the project.

Returns:
    The absolute path to the base directory.
"""
```

### `basename()`

```python
"""Gets the basename of a path, optionally removing a suffix.

Args:
    path: The path to get the basename of.
    suffix: An optional suffix to remove from the basename.

Returns:
    The basename of the path.
"""
```

### `dirname()`

```python
"""Gets the directory name of a path.

Args:
    path: The path to get the directory name of.

Returns:
    The directory name of the path.
"""
```

### `is_in_base_dir()`

```python
"""Checks if a path is within the base directory of the project.

Args:
    path: The path to check.

Returns:
    True if the path is within the base directory, False otherwise.
"""
```

### `get_subdirectories()`

```python
"""Gets a list of subdirectories in a directory.

Args:
    relative_path: The relative path to the directory.
    include: A glob pattern or list of glob patterns to include.
    exclude: A glob pattern or list of glob patterns to exclude.

Returns:
    A list of the subdirectories in the directory.
"""
```

### `zip_dir()`

```python
"""Zips a directory.

Args:
    dir_path: The path to the directory to zip.

Returns:
    The path to the created zip file.
"""
```

### `move_file()`

```python
"""Moves a file.

Args:
    relative_path: The relative path to the file to move.
    new_path: The new relative path of the file.
"""
```

### `safe_file_name()`

```python
"""Sanitizes a filename to make it safe for use in a file system.

Args:
    filename: The filename to sanitize.

Returns:
    The sanitized filename.
"""
```

## `python/helpers/git.py`

### `get_git_info()`

```python
"""Gets information about the Git repository.

Returns:
    A dictionary containing the following information:
    - branch: The name of the current branch.
    - commit_hash: The hash of the latest commit.
    - commit_time: The timestamp of the latest commit.
    - tag: The latest tag.
    - short_tag: The latest tag, without the commit hash.
    - version: A string combining the branch and tag/commit hash.
"""
```

## `python/helpers/guids.py`

### `generate_id()`

```python
"""Generates a random ID of a given length.

Args:
    length: The length of the ID to generate.

Returns:
    A random ID string.
"""
```
