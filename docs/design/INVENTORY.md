# System Inventory

**Architecture Version**: 2.0 (Django Migration Complete)

## 📦 Django Apps (`admin/`)
These apps encapsulate the core business logic and domain boundaries.

1.  **`admin.agents`**: Agent Lifecycle & Configuration.
2.  **`admin.api`**: Internal API Interfaces.
3.  **`admin.capsules`**: Policy & Security Enclaves.
4.  **`admin.chat`**: Real-time Messaging.
5.  **`admin.common`**: Shared Utilities & Base Classes.
6.  **`admin.core`**: Core Config, Models, & Infrastructure.
7.  **`admin.features`**: Feature Flagging.
8.  **`admin.files`**: File Management & Storage.
9.  **`admin.gateway`**: Request Routing & Validation.
10. **`admin.llm`**: LLM Integration & Provider Abstraction.
11. **`admin.memory`**: Vector Store & Long-term Memory.
12. **`admin.multimodal`**: Vision & Audio Processing.
13. **`admin.notifications`**: Alerting System.
14. **`admin.orchestrator`**: Service Orchestration.
15. **`admin.aaas`**: Multi-tenancy & Billing.
16. **`admin.tools`**: Tool Execution Engine.
17. **`admin.voice`**: Speech-to-Text & TTS.

## ⚙️ Services (`services/`)
Executable services managed by Docker.

-   **`services.gateway`**: Main API Gateway (Django Ninja).
-   **`services.conversation_worker`**: Async Chat Processor.
-   **`services.tool_executor`**: Secure Tool Sandbox.
-   **`services.memory_replicator`**: Vector Sync Service.
-   **`services.delegation_gateway`**: Agent-to-Agent Coordination.

## 💾 Infrastructure
-   **PostgreSQL**: Primary Data Store.
-   **Redis**: Cache & Pub/Sub.
-   **ChromaDB/Milvus**: Vector Store (Managed by `admin.memory`).
