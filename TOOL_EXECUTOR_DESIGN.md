# 🛠️ SomaAgent 01 Tool Executor - Complete Design Document

## 🎯 Vision
Transform the current minimal tool executor into a production-grade, secure, scalable tool execution platform that bridges the rich legacy Agent Zero tools with the new microservices architecture.

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                Tool Executor Service                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Kafka     │  │   Policy    │  │  Resource   │      │
│  │ Integration │  │ Enforcement │  │  Manager    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                Tool Registry & Loader                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Docker     │  │ Execution   │  │ Monitoring  │      │
│  │ Sandbox     │  │  Engine     │  │   & Logs    │      │
│  │ Manager     │  │             │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## 📋 Detailed Component Design

### 1. Enhanced Tool Executor Service

**File**: `services/tool_executor/enhanced_main.py`

```python
"""Enhanced Tool Executor with Docker sandboxing and legacy tool integration."""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# Core dependencies
from services.common.event_bus import KafkaEventBus
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.session_repository import PostgresSessionStore
from services.common.requeue_store import RequeueStore
from services.common.telemetry import TelemetryPublisher

# New components to build
from services.tool_executor.sandbox_manager import DockerSandboxManager
from services.tool_executor.tool_registry import ToolRegistry, ToolDefinition
from services.tool_executor.resource_manager import ResourceManager, ExecutionLimits
from services.tool_executor.execution_engine import ExecutionEngine, ExecutionResult


class ExecutionMode(Enum):
    SANDBOXED = "sandboxed"      # Docker container isolation
    RESTRICTED = "restricted"     # Host with restrictions (read-only, timeouts)
    TRUSTED = "trusted"          # Full host access (admin tools only)


@dataclass
class ToolRequest:
    event_id: str
    session_id: str
    persona_id: Optional[str]
    tool_name: str
    args: Dict[str, Any]
    metadata: Dict[str, Any]
    tenant: str = "default"
    priority: int = 0
    execution_mode: ExecutionMode = ExecutionMode.SANDBOXED
    limits: Optional[ExecutionLimits] = None


@dataclass
class ToolResult:
    event_id: str
    session_id: str
    tool_name: str
    status: str  # success, error, timeout, blocked, queued
    payload: Dict[str, Any]
    execution_time: float
    resource_usage: Dict[str, Any]
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedToolExecutor:
    """Production-grade tool executor with Docker sandboxing."""
    
    def __init__(self) -> None:
        # Core services
        self.bus = KafkaEventBus()
        self.policy = PolicyClient()
        self.store = PostgresSessionStore()
        self.requeue = RequeueStore()
        self.telemetry = TelemetryPublisher(self.bus)
        
        # New components
        self.sandbox_manager = DockerSandboxManager()
        self.tool_registry = ToolRegistry()
        self.resource_manager = ResourceManager()
        self.execution_engine = ExecutionEngine(
            self.sandbox_manager, 
            self.resource_manager
        )
        
        # Configuration
        self.settings = {
            "requests": os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests"),
            "results": os.getenv("TOOL_RESULTS_TOPIC", "tool.results"),
            "group": os.getenv("TOOL_EXECUTOR_GROUP", "tool-executor"),
            "max_concurrent": int(os.getenv("TOOL_MAX_CONCURRENT", "10")),
            "default_timeout": int(os.getenv("TOOL_DEFAULT_TIMEOUT", "300")),
        }
        
        # Active executions tracking
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.execution_queue: asyncio.Queue[ToolRequest] = asyncio.Queue()
        
    async def start(self) -> None:
        """Initialize and start the tool executor service."""
        LOGGER.info("Starting Enhanced Tool Executor")
        
        # Initialize components
        await self.sandbox_manager.initialize()
        await self.tool_registry.load_all_tools()
        await self.resource_manager.initialize()
        
        # Start background tasks
        background_tasks = [
            asyncio.create_task(self._process_execution_queue()),
            asyncio.create_task(self._monitor_executions()),
            asyncio.create_task(self._cleanup_resources()),
        ]
        
        # Start Kafka consumer
        await self.bus.consume(
            self.settings["requests"],
            self.settings["group"],
            self._handle_request,
        )
        
        # Cleanup on shutdown
        for task in background_tasks:
            task.cancel()
            
    async def _handle_request(self, event: Dict[str, Any]) -> None:
        """Handle incoming tool execution request."""
        try:
            # Parse and validate request
            request = self._parse_tool_request(event)
            
            # Policy check (unless override)
            if not event.get("metadata", {}).get("requeue_override"):
                allowed = await self._check_policy(request)
                if not allowed:
                    await self._handle_policy_blocked(request, event)
                    return
            
            # Check resource availability
            can_execute = await self.resource_manager.can_execute(request)
            if not can_execute:
                await self._queue_for_later(request)
                return
                
            # Execute immediately or queue based on concurrency
            if len(self.active_executions) < self.settings["max_concurrent"]:
                await self._execute_tool(request)
            else:
                await self.execution_queue.put(request)
                
        except Exception as exc:
            LOGGER.exception("Error handling tool request", extra={"event": event})
            await self._publish_error_result(event, str(exc))
    
    async def _execute_tool(self, request: ToolRequest) -> None:
        """Execute a tool request with full monitoring."""
        execution_id = f"{request.event_id}_{int(time.time())}"
        
        # Create execution task
        task = asyncio.create_task(
            self._run_tool_execution(request, execution_id)
        )
        self.active_executions[execution_id] = task
        
        # Emit telemetry
        await self.telemetry.emit_tool_started(
            session_id=request.session_id,
            tool_name=request.tool_name,
            execution_id=execution_id,
            mode=request.execution_mode.value
        )
    
    async def _run_tool_execution(self, request: ToolRequest, execution_id: str) -> None:
        """Execute tool and handle result publishing."""
        start_time = time.time()
        
        try:
            # Get tool definition
            tool_def = await self.tool_registry.get_tool(request.tool_name)
            if not tool_def:
                raise ValueError(f"Unknown tool: {request.tool_name}")
            
            # Execute with appropriate engine
            result = await self.execution_engine.execute_tool(
                tool_def, request, execution_id
            )
            
            # Publish success result
            await self._publish_tool_result(request, result)
            
        except Exception as exc:
            # Publish error result
            error_result = ToolResult(
                event_id=request.event_id,
                session_id=request.session_id,
                tool_name=request.tool_name,
                status="error",
                payload={"error": str(exc)},
                execution_time=time.time() - start_time,
                resource_usage={}
            )
            await self._publish_tool_result(request, error_result)
            
        finally:
            # Cleanup
            self.active_executions.pop(execution_id, None)
            await self.resource_manager.release_resources(execution_id)
```

### 2. Docker Sandbox Manager

**File**: `services/tool_executor/sandbox_manager.py`

```python
"""Docker-based sandbox management for secure tool execution."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import docker
from docker.models.containers import Container
from docker.models.images import Image

LOGGER = logging.getLogger(__name__)


@dataclass
class SandboxSpec:
    """Specification for a tool execution sandbox."""
    image: str
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    timeout: int = 300
    network_mode: str = "none"  # No network by default
    readonly_root: bool = True
    environment: Dict[str, str] = None
    volumes: Dict[str, str] = None
    working_dir: str = "/workspace"
    user: str = "nobody"  # Non-root user
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}
        if self.volumes is None:
            self.volumes = {}


@dataclass
class SandboxResult:
    """Result from sandbox execution."""
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_peak: Optional[int] = None
    cpu_time: Optional[float] = None
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0


class DockerSandboxManager:
    """Manages Docker containers for secure tool execution."""
    
    def __init__(self):
        self.client: docker.DockerClient = None
        self.base_images = {
            "python": "python:3.11-slim",
            "nodejs": "node:18-alpine", 
            "shell": "alpine:latest",
            "code": "soma/tool-executor:latest",  # Custom image with tools
        }
        self.active_containers: Dict[str, Container] = {}
        
    async def initialize(self) -> None:
        """Initialize Docker client and prepare base images."""
        LOGGER.info("Initializing Docker Sandbox Manager")
        
        try:
            self.client = docker.from_env()
            # Test Docker connection
            self.client.ping()
            
            # Ensure base images are available
            await self._ensure_base_images()
            
            # Cleanup any leftover containers
            await self._cleanup_orphaned_containers()
            
            LOGGER.info("Docker Sandbox Manager initialized successfully")
            
        except Exception as exc:
            LOGGER.error(f"Failed to initialize Docker: {exc}")
            raise RuntimeError(f"Docker initialization failed: {exc}")
    
    async def create_sandbox(
        self, 
        execution_id: str, 
        spec: SandboxSpec,
        files: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a new sandbox container."""
        
        # Create temporary workspace
        workspace_path = await self._create_workspace(execution_id, files or {})
        
        # Configure container
        container_config = {
            "image": spec.image,
            "name": f"soma-tool-{execution_id}",
            "working_dir": spec.working_dir,
            "user": spec.user,
            "network_mode": spec.network_mode,
            "read_only": spec.readonly_root,
            "mem_limit": spec.memory_limit,
            "cpu_count": int(spec.cpu_limit),
            "environment": spec.environment,
            "volumes": {
                **spec.volumes,
                workspace_path: {"bind": spec.working_dir, "mode": "rw"}
            },
            "detach": True,
            "remove": False,  # We'll remove manually for inspection
        }
        
        # Create container
        container = self.client.containers.create(**container_config)
        self.active_containers[execution_id] = container
        
        LOGGER.info(f"Created sandbox container: {container.id[:12]}")
        return container.id
    
    async def execute_command(
        self,
        execution_id: str,
        command: List[str],
        timeout: int = 300
    ) -> SandboxResult:
        """Execute a command in the sandbox."""
        
        container = self.active_containers.get(execution_id)
        if not container:
            raise ValueError(f"No sandbox found for execution: {execution_id}")
        
        start_time = time.time()
        
        try:
            # Start container if not running
            if container.status != "running":
                container.start()
            
            # Execute command
            exec_result = container.exec_run(
                command,
                stdout=True,
                stderr=True,
                timeout=timeout,
                user=container.attrs['Config']['User']
            )
            
            execution_time = time.time() - start_time
            
            # Get resource usage stats
            stats = await self._get_container_stats(container)
            
            return SandboxResult(
                exit_code=exec_result.exit_code,
                stdout=exec_result.output.decode('utf-8', errors='replace'),
                stderr="",  # exec_run combines stdout/stderr
                execution_time=execution_time,
                memory_peak=stats.get('memory_peak'),
                cpu_time=stats.get('cpu_time')
            )
            
        except Exception as exc:
            LOGGER.error(f"Sandbox execution failed: {exc}")
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Execution error: {exc}",
                execution_time=time.time() - start_time
            )
    
    async def destroy_sandbox(self, execution_id: str) -> None:
        """Destroy a sandbox and cleanup resources."""
        
        container = self.active_containers.pop(execution_id, None)
        if not container:
            return
        
        try:
            # Stop and remove container
            if container.status == "running":
                container.stop(timeout=10)
            container.remove()
            
            # Cleanup workspace
            await self._cleanup_workspace(execution_id)
            
            LOGGER.info(f"Destroyed sandbox: {execution_id}")
            
        except Exception as exc:
            LOGGER.error(f"Error destroying sandbox {execution_id}: {exc}")
    
    async def _create_workspace(self, execution_id: str, files: Dict[str, str]) -> str:
        """Create temporary workspace with provided files."""
        
        workspace_path = os.path.join(tempfile.gettempdir(), f"soma-workspace-{execution_id}")
        os.makedirs(workspace_path, exist_ok=True)
        
        # Write files to workspace
        for filename, content in files.items():
            file_path = os.path.join(workspace_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return workspace_path
    
    async def _cleanup_workspace(self, execution_id: str) -> None:
        """Cleanup temporary workspace."""
        import shutil
        
        workspace_path = os.path.join(tempfile.gettempdir(), f"soma-workspace-{execution_id}")
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)
    
    async def _get_container_stats(self, container: Container) -> Dict[str, Any]:
        """Get resource usage statistics from container."""
        try:
            stats = container.stats(stream=False)
            return {
                'memory_peak': stats['memory']['max_usage'],
                'cpu_time': stats['cpu_stats']['cpu_usage']['total_usage']
            }
        except Exception:
            return {}
    
    async def _ensure_base_images(self) -> None:
        """Ensure all base images are available."""
        for name, image_tag in self.base_images.items():
            try:
                self.client.images.get(image_tag)
                LOGGER.info(f"Base image '{image_tag}' available")
            except docker.errors.ImageNotFound:
                LOGGER.info(f"Pulling base image: {image_tag}")
                self.client.images.pull(image_tag)
    
    async def _cleanup_orphaned_containers(self) -> None:
        """Remove any leftover containers from previous runs."""
        containers = self.client.containers.list(
            all=True, 
            filters={"name": "soma-tool-"}
        )
        for container in containers:
            try:
                container.remove(force=True)
                LOGGER.info(f"Cleaned up orphaned container: {container.name}")
            except Exception as exc:
                LOGGER.warning(f"Failed to cleanup container {container.name}: {exc}")
```

### 3. Tool Registry & Dynamic Loading

**File**: `services/tool_executor/tool_registry.py`

```python
"""Dynamic tool registry for loading and managing tools."""
from __future__ import annotations

import asyncio
import importlib
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

LOGGER = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of an executable tool."""
    name: str
    description: str
    execution_mode: str  # sandboxed, restricted, trusted
    sandbox_spec: Optional[Dict[str, Any]] = None
    timeout: int = 300
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    requires_network: bool = False
    requires_files: bool = False
    schema: Optional[Dict[str, Any]] = None  # JSON schema for args validation
    
    # Legacy tool integration
    legacy_class: Optional[Type] = None
    legacy_module_path: Optional[str] = None
    
    # Container-based tools
    container_image: Optional[str] = None
    container_command: Optional[List[str]] = None
    

class ToolRegistry:
    """Registry for managing and loading tools dynamically."""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.legacy_tools: Dict[str, Type] = {}
        
        # Tool discovery paths
        self.legacy_tools_path = Path("python/tools")
        self.new_tools_path = Path("services/tool_executor/tools")
        self.tools_config_path = Path("services/tool_executor/tool_definitions.yaml")
    
    async def load_all_tools(self) -> None:
        """Load all available tools from various sources."""
        LOGGER.info("Loading all tools into registry")
        
        # Load legacy Agent Zero tools
        await self._load_legacy_tools()
        
        # Load new containerized tools
        await self._load_containerized_tools()
        
        # Load tool definitions from config
        await self._load_tool_definitions()
        
        LOGGER.info(f"Loaded {len(self.tools)} tools into registry")
        
    async def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self.tools.get(name)
    
    async def list_tools(self) -> List[ToolDefinition]:
        """List all available tools."""
        return list(self.tools.values())
    
    async def register_tool(self, tool_def: ToolDefinition) -> None:
        """Register a new tool definition."""
        self.tools[tool_def.name] = tool_def
        LOGGER.info(f"Registered tool: {tool_def.name}")
    
    async def _load_legacy_tools(self) -> None:
        """Load legacy Agent Zero tools from python/tools/."""
        if not self.legacy_tools_path.exists():
            LOGGER.warning(f"Legacy tools path not found: {self.legacy_tools_path}")
            return
        
        # Discover tool modules
        tool_files = list(self.legacy_tools_path.glob("*.py"))
        tool_files = [f for f in tool_files if not f.name.startswith("_")]
        
        for tool_file in tool_files:
            try:
                await self._load_legacy_tool_module(tool_file)
            except Exception as exc:
                LOGGER.error(f"Failed to load legacy tool {tool_file}: {exc}")
    
    async def _load_legacy_tool_module(self, tool_file: Path) -> None:
        """Load a single legacy tool module."""
        module_name = tool_file.stem
        
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, tool_file)
        if not spec or not spec.loader:
            return
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find tool classes that inherit from Tool
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                hasattr(attr, '__bases__') and 
                any('Tool' in str(base) for base in attr.__bases__)):
                
                # Create tool definition for legacy tool
                tool_def = await self._create_legacy_tool_definition(
                    attr, module_name, tool_file
                )
                if tool_def:
                    await self.register_tool(tool_def)
                    self.legacy_tools[tool_def.name] = attr
    
    async def _create_legacy_tool_definition(
        self, 
        tool_class: Type, 
        module_name: str,
        tool_file: Path
    ) -> Optional[ToolDefinition]:
        """Create tool definition from legacy tool class."""
        
        # Determine tool name
        if hasattr(tool_class, 'name'):
            name = tool_class.name
        else:
            name = tool_class.__name__.lower().replace('tool', '').replace('_', '-')
        
        # Determine execution requirements based on tool type
        execution_mode = "sandboxed"  # Default
        requires_network = False
        requires_files = False
        
        # Analyze tool for requirements (heuristic)
        if 'search' in name or 'web' in name or 'browser' in name:
            requires_network = True
        
        if 'code' in name or 'terminal' in name or 'shell' in name:
            execution_mode = "restricted"  # Needs more access
        
        if 'file' in name or 'memory' in name or 'knowledge' in name:
            requires_files = True
        
        # Special cases for high-privilege tools
        if name in ['code_execution_tool', 'terminal', 'shell']:
            execution_mode = "trusted"
        
        return ToolDefinition(
            name=name,
            description=f"Legacy Agent Zero tool: {tool_class.__doc__ or name}",
            execution_mode=execution_mode,
            requires_network=requires_network,
            requires_files=requires_files,
            legacy_class=tool_class,
            legacy_module_path=str(tool_file),
            sandbox_spec={
                "image": "soma/tool-executor:legacy",
                "memory_limit": "1g" if execution_mode == "trusted" else "512m",
                "network_mode": "bridge" if requires_network else "none",
            }
        )
    
    async def _load_containerized_tools(self) -> None:
        """Load containerized tools from new tools directory."""
        # Implementation for new containerized tools
        pass
    
    async def _load_tool_definitions(self) -> None:
        """Load tool definitions from configuration files."""
        # Implementation for YAML-based tool definitions
        pass
```

### 4. Resource Management & Limits

**File**: `services/tool_executor/resource_manager.py`

```python
"""Resource management for tool execution."""
from __future__ import annotations

import asyncio
import logging
import psutil
import time
from dataclasses import dataclass
from typing import Dict, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class ExecutionLimits:
    """Resource limits for tool execution."""
    memory_mb: int = 512
    cpu_cores: float = 1.0
    timeout_seconds: int = 300
    disk_mb: int = 100
    network_enabled: bool = False
    max_processes: int = 10


@dataclass
class ResourceUsage:
    """Current resource usage tracking."""
    memory_mb: float
    cpu_percent: float
    active_executions: int
    total_executions: int
    

class ResourceManager:
    """Manages system resources for tool execution."""
    
    def __init__(self):
        self.max_memory_mb = int(os.getenv("TOOL_MAX_MEMORY_MB", "4096"))
        self.max_cpu_cores = float(os.getenv("TOOL_MAX_CPU_CORES", "4.0"))
        self.max_concurrent = int(os.getenv("TOOL_MAX_CONCURRENT", "10"))
        
        self.current_usage = ResourceUsage(0, 0, 0, 0)
        self.allocated_resources: Dict[str, ExecutionLimits] = {}
        
    async def initialize(self) -> None:
        """Initialize resource monitoring."""
        LOGGER.info("Initializing Resource Manager")
        
        # Start resource monitoring task
        asyncio.create_task(self._monitor_resources())
        
    async def can_execute(self, request) -> bool:
        """Check if resources are available for execution."""
        
        limits = request.limits or ExecutionLimits()
        
        # Check memory availability
        if (self.current_usage.memory_mb + limits.memory_mb) > self.max_memory_mb:
            return False
        
        # Check CPU availability  
        if (self.current_usage.cpu_percent / 100 * psutil.cpu_count() + limits.cpu_cores) > self.max_cpu_cores:
            return False
        
        # Check concurrent execution limit
        if self.current_usage.active_executions >= self.max_concurrent:
            return False
        
        return True
    
    async def allocate_resources(self, execution_id: str, limits: ExecutionLimits) -> None:
        """Allocate resources for execution."""
        self.allocated_resources[execution_id] = limits
        self.current_usage.active_executions += 1
        self.current_usage.memory_mb += limits.memory_mb
        
    async def release_resources(self, execution_id: str) -> None:
        """Release allocated resources."""
        limits = self.allocated_resources.pop(execution_id, None)
        if limits:
            self.current_usage.active_executions -= 1
            self.current_usage.memory_mb -= limits.memory_mb
    
    async def _monitor_resources(self) -> None:
        """Background task to monitor system resources."""
        while True:
            try:
                # Update current CPU usage
                self.current_usage.cpu_percent = psutil.cpu_percent(interval=1)
                
                # Log resource status periodically
                if self.current_usage.total_executions % 10 == 0:
                    LOGGER.info(f"Resource usage: {self.current_usage}")
                
            except Exception as exc:
                LOGGER.error(f"Resource monitoring error: {exc}")
            
            await asyncio.sleep(5)
```

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Week 1)
1. **Enhanced Tool Executor Service**
   - Implement `EnhancedToolExecutor` class
   - Add queue management and concurrency control
   - Integrate with existing Kafka/Policy infrastructure

2. **Docker Sandbox Manager**
   - Implement `DockerSandboxManager`
   - Create base Docker images for tools
   - Add security policies and resource limits

### Phase 2: Tool Integration (Week 2)  
1. **Tool Registry System**
   - Implement dynamic tool loading
   - Bridge legacy `python/tools/` with new system
   - Add tool metadata and validation

2. **Resource Management**
   - Implement `ResourceManager` for system resources
   - Add execution monitoring and limits
   - Create resource allocation algorithms

### Phase 3: Advanced Features (Week 3)
1. **Execution Engine**
   - Multi-mode execution (sandboxed/restricted/trusted)
   - Advanced monitoring and telemetry
   - Error recovery and retry mechanisms

2. **Performance & Scaling**
   - Container pooling for performance
   - Parallel execution optimization
   - Advanced security policies

### Phase 4: Integration & Testing (Week 4)
1. **Full System Integration**
   - End-to-end testing with conversation worker
   - Policy enforcement testing
   - Performance benchmarking

2. **Production Readiness**
   - Comprehensive logging and monitoring
   - Error handling and recovery
   - Documentation and deployment guides

## 🔒 Security Architecture

### Container Security
- **Non-root execution** - All tools run as `nobody` user
- **Read-only root filesystem** - Prevents system modification
- **Network isolation** - No network by default, selective enablement
- **Resource limits** - Memory, CPU, and time constraints
- **Temporary workspaces** - Isolated file systems per execution

### Policy Integration
- **Pre-execution checks** - OPA policy evaluation before tool execution
- **Runtime monitoring** - Resource usage tracking and limits
- **Post-execution audit** - Complete audit trail for all executions

## 📊 Monitoring & Observability

### Metrics Collection
- Execution success/failure rates
- Resource utilization (CPU, memory, disk)
- Tool popularity and usage patterns
- Security policy violations
- Performance benchmarks

### Telemetry Events
```python
# Tool execution lifecycle events
await self.telemetry.emit_tool_started(session_id, tool_name, execution_id)
await self.telemetry.emit_tool_completed(session_id, tool_name, execution_id, result)
await self.telemetry.emit_resource_usage(execution_id, cpu, memory, duration)
await self.telemetry.emit_security_event(execution_id, policy_violation, action)
```

## 🎯 Success Criteria

1. **Security**: All tools execute in isolated environments
2. **Performance**: <2s cold start, <500ms warm start for simple tools  
3. **Reliability**: 99.9% successful execution rate
4. **Scalability**: Support 100+ concurrent tool executions
5. **Compatibility**: Full integration with legacy Agent Zero tools
6. **Monitoring**: Complete observability and audit trails

This design transforms the current minimal tool executor into a production-grade platform that maintains security while providing the rich functionality of the existing Agent Zero tool ecosystem.