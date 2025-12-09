# Setup Guide

This guide provides detailed instructions for setting up the Agent Zero development environment.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker:** Docker is used to run the Agent Zero services in a containerized environment.
- **Python:** Python 3.11 or higher is required.
- **Node.js:** Node.js is required for the Web UI.

## Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/agent0-ai/agent-zero.git
    cd agent-zero
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

4.  **Start the Docker services:**
    ```bash
    make dev-up
    ```
    This will start all the necessary services, including the Gateway, Agent Worker, and SomaBrain.

5.  **Access the Web UI:**
    Open your web browser and navigate to `http://localhost:21016/ui` to access the Agent Zero Web UI.

## Docker Compose Usage

The `docker-compose.yml` file in the root of the repository defines the services that make up the Agent Zero application. You can use the following `make` commands to manage the services:

- **`make dev-up`:** Start the services in development mode.
- **`make dev-down`:** Stop the services.
- **`make dev-logs`:** View the logs for all services.
- **`make dev-rebuild`:** Rebuild the Docker images and restart the services.

## Running Tests

To run the tests, use the following command:

```bash
pytest
```

This will run all the unit, integration, and end-to-end tests.

## Debugging

To debug the application, you can use the following methods:

- **View logs:** Use the `make dev-logs` command to view the logs for all services.
- **Attach a debugger:** You can attach a debugger to the Python services by setting the `DEBUG` environment variable to `true`.
