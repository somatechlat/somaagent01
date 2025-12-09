# Repository Overview

## Purpose

This repository contains the source code for Agent Zero, a personal, organic agentic framework that grows and learns with you. It is designed to be a dynamic, transparent, and customizable general-purpose assistant that uses the computer as a tool to accomplish tasks.

## High-Level Architecture

Agent Zero is a multi-agent system with a modular architecture. The core components are:

- **Agent:** The main worker that processes tasks, communicates with other agents, and utilizes tools to achieve its goals.
- **Tools:** A collection of Python scripts that provide the agent with capabilities such as web browsing, code execution, and memory management.
- **Web UI:** A web-based interface for interacting with the agent.
- **API:** A set of API endpoints for programmatic interaction with the agent and its services.

## Key Services

The Agent Zero ecosystem is composed of several key services that work together to provide its functionality. These services are defined in the `docker-compose.yml` file and include:

- **Gateway:** The main entry point for all API requests. It handles authentication, routing, and provides a unified interface to the other services.
- **Web UI:** The frontend application that provides a user-friendly interface for interacting with the agent.
- **Agent Worker:** The background worker that runs the agent and executes tasks.
- **SomaBrain:** A service that provides memory and context for the agent.
- **Capsule Registry:** A service for managing and distributing "capsules," which are pre-packaged sets of tools and prompts.

## Service Interactions

The services in the Agent Zero ecosystem interact with each other in the following ways:

1.  The **Web UI** communicates with the **Gateway** to send user requests and receive updates.
2.  The **Gateway** forwards requests to the appropriate service, such as the **Agent Worker** or **SomaBrain**.
3.  The **Agent Worker** executes tasks, using tools to interact with the local system and external services.
4.  The **Agent Worker** communicates with **SomaBrain** to store and retrieve memories.
5.  The **Agent Worker** can download and install capsules from the **Capsule Registry** to extend its capabilities.
