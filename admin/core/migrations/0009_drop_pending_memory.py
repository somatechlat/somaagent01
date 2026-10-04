"""Drop the PendingMemory table — it was a second replay authority.

The live memory-write queue is ``OutboxMessage`` on the ``memory.wal`` topic:
the MemoryGateway seam accepts every write durably before its hop (T-6), the
outbox drain publishes it, and memory-replicator replays it into SomaBrain
until acked. ``PendingMemory`` had no writer on the agent lane and a second
driver (``manage.py sync_memories``), so two replay authorities could both
redeliver one failed write. This removes the orphan.
"""

from django.db import migrations


class Migration(migrations.Migration):
    """Drop the orphan PendingMemory queue."""

    dependencies = [
        ("core", "0008_asset_delegationtask_executionrecord_modelprofile_and_more"),
    ]

    operations = [
        migrations.DeleteModel(name="PendingMemory"),
    ]
