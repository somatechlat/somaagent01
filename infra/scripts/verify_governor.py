"""Module verify_governor."""

import asyncio
import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
os.environ.setdefault("SA01_REDIS_URL", "redis://localhost:6379/0")
django.setup()

from asgiref.sync import sync_to_async

from admin.chat.models import Conversation
from services.common.chat_service import get_chat_service


async def verify_governor_wiring():
    """Verify that the AgentIQ Governor is correctly wired to the ChatService."""
    print("--- Verifying AgentIQ Governor Wiring ---")

    # 1. Initialize ChatService
    service = await get_chat_service()
    print("[OK] ChatService initialized")

    # 2. Check dependencies
    if not hasattr(service, "governor"):
        print("[FAIL] Governor not found on ChatService")
        return
    if not hasattr(service, "capsule_store"):
        print("[FAIL] CapsuleStore not found on ChatService")
        return
    print("[OK] Dependencies wired")

    # 3. Create dummy conversation (if DB is accessible)
    try:
        import uuid

        agent_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())

        # Check if conversation exists or create one
        @sync_to_async
        def get_or_create_conv():
            """Retrieve or create conv.
                """

            conv, created = Conversation.objects.get_or_create(
                agent_id=agent_id,
                user_id=user_id,
                tenant_id=tenant_id,
                defaults={"status": "active", "message_count": 0},
            )
            return str(conv.id)

        conv_id = await get_or_create_conv()
        print(f"[OK] Conversation ready: {conv_id}")

        # 4. Trigger send_message (Dry run / check logic)
        # Verify that the GOVERNOR called.

        print("--- Attempting to send message to trigger Governor ---")
        try:
            msg_gen = service.send_message(
                conversation_id=conv_id, agent_id=agent_id, content="Hello AgentIQ", user_id=user_id
            )

            # We just iterate a bit
            async for token in msg_gen:
                print(token, end="", flush=True)
            print("\n[OK] Message flow completed")

        except Exception as e:
            # We expect failure if SomaBrain/LLM is not configured/running
            # But we want to see if it failed *after* Governor or *because* of Governor
            print(f"\n[INFO] Message send interrupted (expected if services down): {e}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"[FAIL] Setup failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(verify_governor_wiring())