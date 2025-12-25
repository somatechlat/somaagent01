"""Core Sensors Package.

VIBE COMPLIANT - Django ORM + ZDL pattern.
Sensors capture ALL agent data and queue for sync.

4 Core Sensors:
1. ConversationSensor - Every message in/out
2. MemorySensor - Every remember/recall
3. LLMSensor - Every completion
4. ToolSensor - Every execution
"""

from admin.core.sensors.base import BaseSensor, SensorEvent
from admin.core.sensors.outbox import SensorOutbox, OutboxEventType
from admin.core.sensors.conversation import ConversationSensor
from admin.core.sensors.memory import MemorySensor
from admin.core.sensors.llm import LLMSensor
from admin.core.sensors.tool import ToolSensor

__all__ = [
    "BaseSensor",
    "SensorEvent",
    "SensorOutbox",
    "OutboxEventType",
    "ConversationSensor",
    "MemorySensor",
    "LLMSensor",
    "ToolSensor",
]
