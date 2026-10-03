from django.db import migrations, models


class Migration(migrations.Migration):
    """Add Message.content — the conversation transcript text column.

    ``coordinate`` keeps the seam coordinate (memory_contract.make_coord);
    it is NOT the message text. ARCH-INVARIANTS §3: Message rows are the
    conversation transcript.
    """

    dependencies = [
        ("chat", "0003_coordinate_to_textfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="content",
            field=models.TextField(default=""),
        ),
    ]
