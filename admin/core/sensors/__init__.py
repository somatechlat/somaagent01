"""Core Sensors Package.


Sensors capture ALL agent data and queue for sync.

6 Sensors:
1. ConversationSensor - Every message in/out
2. MemorySensor - Every remember/recall
3. LLMSensor - Every completion
4. ToolSensor - Every execution
5. VoiceSensor - Every voice interaction
6. UploadSensor - Every file upload
"""

from admin.core.sensors.base import BaseSensor, SensorEvent
from admin.core.sensors.conversation import ConversationSensor
from admin.core.sensors.llm import LLMSensor
from admin.core.sensors.memory import MemorySensor
from admin.core.sensors.outbox import OutboxEventType, SensorOutbox
from admin.core.sensors.tool import ToolSensor
from admin.core.sensors.upload import UploadSensor
from admin.core.sensors.voice import VoiceSensor

__all__ = [
    "BaseSensor",
    "SensorEvent",
    "SensorOutbox",
    "OutboxEventType",
    "ConversationSensor",
    "MemorySensor",
    "LLMSensor",
    "ToolSensor",
    "VoiceSensor",
    "UploadSensor",
]