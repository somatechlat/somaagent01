# Python Modules and Packages

This document provides an overview of the key Python modules and packages in the Agent Zero repository.

## `python/`

This directory contains the core Python source code for the Agent Zero application.

### `python/api/`

This package defines the main API endpoints for interacting with the Agent Zero application. It uses Flask to create a web server and handles incoming requests, routing them to the appropriate services.

### `python/extensions/`

This package contains a collection of extension points that allow for the customization and extension of the agent's behavior. Each subdirectory corresponds to a specific event in the agent's lifecycle, and the Python files within these directories are executed when the corresponding event occurs.

### `python/helpers/`

This package provides a collection of helper functions and utility classes that are used throughout the application. These include utilities for file I/O, data manipulation, and interacting with external services.

### `python/integrations/`

This package contains integrations with external services, such as the SomaBrain and the tool catalog.

### `python/observability/`

This package provides functionality for monitoring and observability, including metrics and event publishing.

### `python/somaagent/`

This package contains the core logic for the SomaAgent, including the context builder and capsule management.

### `python/tasks/`

This package defines a set of Celery tasks for performing background operations, such as running agent-to-agent chats.

### `python/tools/`

This package contains the various tools that the agent can use to perform actions. These tools include a code execution tool, a browser agent, and tools for managing the agent's memory.
