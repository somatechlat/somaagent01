"""Conversation use cases.

This module provides Clean Architecture use cases for conversation processing.
Use cases orchestrate business logic through injected domain ports.

Use Cases:
    - ProcessMessageUseCase: Main orchestration for message processing
    - BuildContextUseCase: Build LLM context from history and memory
    - StoreMemoryUseCase: Store conversation events to SomaBrain
    - GenerateResponseUseCase: Generate LLM responses with streaming
"""

from .build_context import BuildContextInput, BuildContextOutput, BuildContextUseCase
from .generate_response import (
    GenerateResponseInput,
    GenerateResponseOutput,
    GenerateResponseUseCase,
    normalize_usage,
)
from .process_message import (
    AnalysisResult,
    MessageAnalyzer,
    ProcessMessageInput,
    ProcessMessageOutput,
    ProcessMessageUseCase,
)
from .store_memory import StoreMemoryInput, StoreMemoryOutput, StoreMemoryUseCase

__all__ = [
    # Process Message
    "ProcessMessageUseCase",
    "ProcessMessageInput",
    "ProcessMessageOutput",
    "MessageAnalyzer",
    "AnalysisResult",
    # Build Context
    "BuildContextUseCase",
    "BuildContextInput",
    "BuildContextOutput",
    # Store Memory
    "StoreMemoryUseCase",
    "StoreMemoryInput",
    "StoreMemoryOutput",
    # Generate Response
    "GenerateResponseUseCase",
    "GenerateResponseInput",
    "GenerateResponseOutput",
    "normalize_usage",
]