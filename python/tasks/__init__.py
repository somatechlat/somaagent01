"""
Celery tasks for SomaAgent01 with FastA2A integration.
Provides asynchronous task processing for agent communication.
"""

from .a2a_chat_task import a2a_chat_task

__all__ = [
    "a2a_chat_task"
]