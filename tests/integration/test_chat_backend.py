import pytest
import asyncio
import json
import os
import uuid
from channels.db import database_sync_to_async
from tests.e2e.helpers.auth import get_auth_token
# VIBE: Modern websockets API (v14.0+)
from websockets.asyncio.client import connect

from admin.chat.models import Message
from admin.core.models import Session

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_full_flow():
    """
    Verifies the full Chat Architecture Flow:
    1. Authenticate (Keycloak)
    2. Connect (WebSocket)
    3. Send Message (SomaBrain)
    4. Verify Persistence (Postgres Bookkeeper)
    """
    # 1. Authenticte (Targeting Realm: 'somaagent')
    print("\n🔐 Authenticating against realm 'somaagent'...")
    # Override helper defaults for this specific test to match Server Config
    # We must use the 'somaagent' realm because settings.py expects it.
    os.environ["KEYCLOAK_REALM"] = "somaagent"
    
    # Check if admin credentials for somaagent realm need adjustment
    # Assuming standard admin/admin works or env vars are set correctly
    try:
        token = get_auth_token()
    except Exception as e:
        print(f"⚠️ Auth failed in somaagent realm: {e}")
        pytest.fail("Failed to authenticate in 'somaagent' realm.")
        
    assert token, "Failed to get auth token"
    
    # 1.5. Setup Data (Manual DB Management for Process Visibility)
    print("🛠️ Setting up test data (Committing to Real DB)...")
    agent_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    
    # Decode token to get real User ID (sub)
    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    user_id = decoded.get("sub")
    tenant_id = str(uuid.uuid4())
    
    print(f"👤 User ID: {user_id}")
    
    # Explicitly import models
    from admin.chat.models import Conversation, Message
    
    @database_sync_to_async
    def setup_data_manual():
        # Clean up any previous collision (unlikely with UUIDs)
        Conversation.objects.filter(id=conversation_id).delete()
        
        # Create and SAVE (Commit)
        c = Conversation(
            id=conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            user_id=user_id,
            title="Integration Test Real DB"
        )
        c.save()
        print(f"✅ Created Conversation {conversation_id} in Real DB")
        return c
    
    await setup_data_manual()
    
    try:
        # 2. Connect
        uri = f"ws://127.0.0.1:8020/ws/chat/{agent_id}"
        
        headers = {
            "Cookie": f"access_token={token}",
            "Origin": "http://localhost:20173"
        }
        
        print(f"🔌 Connecting to {uri}...")
        async with connect(uri, additional_headers=headers) as websocket:
            # Expect 'connected' message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ Received: {data['type']}")
            assert data['type'] == 'connected'
            
            # 3. Send Message
            test_content = f"VIBE_VERIFICATION_MESSAGE_{os.urandom(4).hex()}"
            print(f"📨 Sending: {test_content}")
            
            await websocket.send(json.dumps({
                "type": "chat.message",
                "payload": {
                    "content": test_content,
                    "conversation_id": conversation_id 
                }
            }))
            
            # 4. Wait for LLM Response (Full Agent Chain)
            print("⏳ Waiting for LLM response (SomaBrain)...")
            
            # We expect a series of 'chat.delta' followed by 'chat.done'
            try:
                 while True:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(msg)
                    print(f"🔄 Received: {data['type']}")
                    
                    if data['type'] == 'chat.done':
                         print("✅ Received 'chat.done' - LLM Flow Complete.")
                         break
                         
                    elif data['type'] == 'error':
                         print(f"❌ Received Error: {data['payload']}")
                         pytest.fail(f"Agent Infra Error: {data['payload']}")

            except asyncio.TimeoutError:
                 pytest.fail("❌ Timeout waiting for LLM response (SomaBrain might be unreachable)")

            # 5. Verify Persistence (PostgreSQL)
            print("📚 Verifying Persistence Layer...")
            
            @database_sync_to_async
            def check_db():
                return Message.objects.filter(content=test_content).exists()
            
            exists = await check_db()
            
            if exists:
                print("✅ STRICT SUCCESS: Message found in Postgres 'Message' table.")
            else:
                pytest.fail("❌ FAILURE: Message NOT found in Postgres Persistence Layer.")

    finally:
        # Cleanup
        print("🧹 Cleaning up test data...")
        @database_sync_to_async
        def cleanup():
            Conversation.objects.filter(id=conversation_id).delete()
        await cleanup()

if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])
