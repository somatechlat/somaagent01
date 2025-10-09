# 🏗️ SomaKamachiq Tool Executor - Service-Oriented Design

## 🎯 **Revised Architecture Vision**

Based on the SomaKamachiq architecture, the agent should **NOT** be constrained by Docker sandboxing that limits its OS capabilities. Instead, the agent should call external orchestrated services that have the full power to execute complex operations.

### 📌 Current Status (Sprint 1B)
- The tool executor shipped in this repository (`services/tool_executor/main.py`) already behaves as an orchestrator: it validates policy, looks up the requested tool, runs through the sandbox abstraction, and publishes results to Kafka.
- Execution is still in-process while the dedicated SomaKamachiq service is being built. The new registry and execution engine provide the seam where remote execution clients will plug in.
- Built-in tools are intentionally lightweight Python adapters. High-power operations (browser, shell, Docker) will live inside SomaKamachiq services before being exposed to agents.

## 🔄 **Corrected Architecture Pattern**

```
┌─────────────────────────────────────────────────────────┐
│                   SomaKamachiq Agent                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Conversation Worker                    │    │
│  │  - Receives user intent                         │    │
│  │  - Determines required tools/capabilities       │    │
│  │  - Calls external service APIs                  │    │
│  │  - Orchestrates responses                       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   Tool Requests │
                    │  (Kafka Topic)  │
                    └───────┬────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│              SomaGent Tool Orchestration Service        │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Tool Executor Service                  │    │
│  │  - Full OS access and capabilities              │    │
│  │  - Code execution (Python, Node, Shell)        │    │
│  │  - File system operations                      │    │
│  │  - Network operations                          │    │
│  │  - Browser automation                          │    │
│  │  - System integrations                         │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Security & Policy Layer               │    │
│  │  - OPA/OpenFGA policy enforcement              │    │
│  │  - Resource monitoring                         │    │
│  │  - Audit logging                               │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Orchestration Engine                  │    │
│  │  - Multi-step workflow execution               │    │
│  │  - Error handling and recovery                 │    │
│  │  - Resource allocation                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Tool Results   │
                    │  (Kafka Topic)  │
                    └───────┬────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │     SomaKamachiq       │
              │   Response Stream      │
              └─────────────────────────┘
```

## 🎯 **Key Architectural Principles**

### **1. Agent as Orchestrator, Not Executor**
- **SomaKamachiq Agent**: High-level reasoning, intent understanding, response orchestration
- **SomaGent Service**: Heavy lifting, OS operations, complex tool execution
- **Clean Separation**: Agent focuses on conversation logic, service handles capabilities

### **2. Service-Oriented Tool Architecture**

```python
# Agent Side - Simple Service Calls
class ServiceOrientedToolExecutor:
    """Agent-side tool executor that calls external services."""
    
    async def execute_tool(self, tool_request: ToolRequest) -> ToolResponse:
        # Agent determines WHAT to do, not HOW
        service_request = {
            "tool_name": tool_request.tool_name,
            "parameters": tool_request.args,
            "context": {
                "session_id": tool_request.session_id,
                "persona_id": tool_request.persona_id,
                "tenant": tool_request.tenant
            },
            "requirements": {
                "os_access": self._requires_os_access(tool_request.tool_name),
                "network_access": self._requires_network(tool_request.tool_name),
                "file_system": self._requires_filesystem(tool_request.tool_name)
            }
        }
        
        # Send to SomaGent service via Kafka
        await self.bus.publish("tool.requests", service_request)
        
        # Wait for orchestrated response
        response = await self._await_tool_response(service_request["request_id"])
        return response
    
    def _requires_os_access(self, tool_name: str) -> bool:
        """Determine if tool needs OS-level access."""
        os_tools = {
            "code_execution_tool", "terminal", "shell", 
            "file_operations", "system_info", "process_management"
        }
        return tool_name in os_tools
    
    def _requires_network(self, tool_name: str) -> bool:
        """Determine if tool needs network access."""
        network_tools = {
            "search_engine", "web_scraping", "api_calls",
            "browser_agent", "download", "upload"
        }
        return tool_name in network_tools
```

### **3. SomaGent Service - Full Capability Executor**

```python
# Service Side - Full OS Access and Orchestration
class SomaGentToolService:
    """External service with full OS capabilities."""
    
    def __init__(self):
        self.capabilities = {
            "code_execution": CodeExecutionEngine(),
            "file_operations": FileSystemEngine(), 
            "network_operations": NetworkEngine(),
            "browser_automation": BrowserEngine(),
            "system_integration": SystemEngine()
        }
        self.orchestrator = WorkflowOrchestrator()
        self.policy_engine = PolicyEngine()
        
    async def handle_tool_request(self, request: Dict[str, Any]) -> None:
        """Handle incoming tool execution requests."""
        
        # Policy check
        allowed = await self.policy_engine.evaluate(request)
        if not allowed:
            await self._send_blocked_response(request)
            return
        
        # Determine execution strategy
        if request["requirements"]["os_access"]:
            result = await self._execute_with_full_access(request)
        elif request["requirements"]["network_access"]:
            result = await self._execute_with_network(request)
        else:
            result = await self._execute_sandboxed(request)
        
        # Send orchestrated response
        await self._send_tool_response(request, result)
    
    async def _execute_with_full_access(self, request: Dict[str, Any]) -> Any:
        """Execute tools that need full OS access."""
        tool_name = request["tool_name"]
        
        if tool_name == "code_execution_tool":
            # Full code execution with real terminal access
            return await self.capabilities["code_execution"].execute(
                code=request["parameters"]["code"],
                runtime=request["parameters"]["runtime"],
                session=request["parameters"].get("session", 0)
            )
        
        elif tool_name == "file_operations":
            # Real file system operations
            return await self.capabilities["file_operations"].execute(
                operation=request["parameters"]["operation"],
                path=request["parameters"]["path"],
        # ... other OS-level tools
    
    async def _execute_with_network(self, request: Dict[str, Any]) -> Any:
        """Execute tools that need network access."""
        tool_name = request["tool_name"]
        
        if tool_name == "search_engine":
            # Real web search with full internet access
            return await self.capabilities["network_operations"].search(
                query=request["parameters"]["query"],
                engines=request["parameters"].get("engines", ["searxng"])
            )
        
        elif tool_name == "browser_agent":
            # Full browser automation
            return await self.capabilities["browser_automation"].execute(
                url=request["parameters"]["url"],
                actions=request["parameters"]["actions"]
            )
        
        # ... other network tools
```

## 🏗️ **Revised Implementation Strategy**

### **Phase 1: Service Separation**
1. **Extract Tool Service**: Move heavy tool execution to separate `SomaGent` service
2. **Agent Simplification**: Reduce agent to conversation logic + service calls
3. **Kafka Integration**: Proper async request/response patterns

### **Phase 2: Capability Distribution**
1. **OS Operations**: Code execution, file ops, system commands → SomaGent
2. **Network Operations**: Web search, APIs, browser automation → SomaGent  
3. **Light Operations**: Text processing, calculations → Agent (or SomaGent)

### **Phase 3: Orchestration Enhancement**
1. **Workflow Engine**: Multi-step tool orchestration in SomaGent
2. **Smart Routing**: Agent determines which service handles which capability
3. **Resource Management**: SomaGent manages compute resources, not Agent

## 🔒 **Security Through Service Boundaries**

### **Agent Security (SomaKamachiq)**
- **Conversation Security**: Input validation, prompt injection protection
- **Service Call Security**: Authenticated calls to SomaGent APIs
- **No Direct Execution**: Agent never executes dangerous operations directly

### **Service Security (SomaGent)**  
- **Policy Enforcement**: OPA/OpenFGA at service boundary
- **Resource Limits**: Service-level CPU, memory, time constraints
- **Audit Logging**: Complete execution audit trail
- **Isolation**: Different tenants/personas isolated at service level

## 🎯 **Benefits of This Architecture**

### **1. Full Agent Capabilities**
- **No Docker Limitations**: SomaGent has full OS access for powerful operations
- **Rich Tool Ecosystem**: All existing Agent Zero tools work at full capacity
- **Complex Workflows**: Multi-step operations orchestrated by service

### **2. Better Security**
- **Service Boundary**: Clear separation between reasoning and execution
- **Centralized Policy**: All dangerous operations gated by SomaGent policies
- **Audit Trail**: Complete visibility into all operations

### **3. Scalability**
- **Independent Scaling**: Scale conversation vs execution separately
- **Resource Optimization**: Heavy operations on dedicated service infrastructure
- **Multi-Tenant**: Service can handle multiple agents/tenants safely

## 🚀 **Integration with SomaKamachiq Ecosystem**

This aligns perfectly with the SomaKamachiq architecture:

- **Conversation Worker** → Calls SomaGent for tool execution
- **Tool Executor** → Runs as SomaGent service with full capabilities  
- **Policy Client** → Enforced at SomaGent service boundary
- **Audio Service** → Separate service for speech processing
- **Analytics** → Kafka streams from all services to ClickHouse

## 💡 **Immediate Next Steps**

1. **Service API Design**: Finalise the request/response contracts between the agent-side executor and SomaKamachiq services.
2. **Remote Execution Client**: Replace the in-process sandbox with RPC calls to SomaKamachiq (containers, browser automation, OS access).
3. **Policy Integration**: Enforce OPA/OpenFGA decisions at the SomaKamachiq boundary and honour overrides via requeue.
4. **Telemetry Expansion**: Capture resource usage, sandbox logs, and audit trails emitted by the remote services.
5. **Tool Catalogue**: Surface the available remote tools via the registry so agents can advertise capabilities dynamically.

This approach gives the agent full power through service orchestration while maintaining security and scalability. The agent becomes the "brain" that orchestrates powerful external capabilities rather than being limited by its own execution constraints.
