"""Memory use cases.

Memory writes and reads go through the single seam:
``services.common.memory_gateway.MemoryGateway``. The former
``StoreMemoryUseCase`` port/use-case pair was an unused second dialect and
has been removed.
"""
