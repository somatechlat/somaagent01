"""Error handling for agent operations."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from python.helpers.errors import RepairableException
from python.helpers.print_style import PrintStyle


class InterventionException(Exception):
    """Exception raised when user intervention interrupts agent processing."""
    pass


class HandledException(Exception):
    """Exception that has been handled and should terminate the message loop."""
    pass


def handle_critical_exception(agent: "Agent", exception: Exception) -> None:
    """Handle critical exceptions during agent processing.
    
    Args:
        agent: The agent instance
        exception: The exception that occurred
        
    Raises:
        HandledException: Always raised to terminate the loop
    """
    if isinstance(exception, HandledException):
        raise exception
    
    if isinstance(exception, InterventionException):
        # Intervention is not an error, just a control flow mechanism
        PrintStyle(font_color="yellow", padding=True).print(f"Intervention: {exception}")
        raise HandledException(exception)
    
    if isinstance(exception, RepairableException):
        # Log repairable exceptions but don't crash
        PrintStyle(font_color="orange", padding=True).print(f"Repairable error: {exception}")
        agent.context.log.log(
            type="warning",
            heading="Repairable Error",
            content=str(exception),
        )
        raise HandledException(exception)
    
    # Log unexpected exceptions
    PrintStyle(font_color="red", padding=True).print(f"Critical error: {exception}")
    agent.context.log.log(
        type="error",
        heading="Critical Error",
        content=str(exception),
    )
    
    raise HandledException(exception)


def is_recoverable_error(exception: Exception) -> bool:
    """Check if an exception is recoverable.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the error can be recovered from
    """
    if isinstance(exception, (InterventionException, HandledException)):
        return False
    
    if isinstance(exception, RepairableException):
        return True
    
    # Network errors, timeouts, etc. might be recoverable
    recoverable_types = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    
    return isinstance(exception, recoverable_types)


def format_error_for_llm(exception: Exception) -> str:
    """Format an exception for inclusion in LLM context.
    
    Args:
        exception: The exception to format
        
    Returns:
        Formatted error string
    """
    error_type = type(exception).__name__
    error_msg = str(exception)
    
    return f"Error ({error_type}): {error_msg}"
