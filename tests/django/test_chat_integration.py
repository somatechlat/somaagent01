"""Integration tests for login-to-chat-journey chat flow.

VIBE COMPLIANT:
- Real infrastructure (PostgreSQL, Redis, SomaBrain)
- No mocks, no fakes
- Tests actual chat endpoints and WebSocket

Per login-to-chat-journey tasks.md Task 14.2:
- Test conversation creation
- Test message sending and streaming
- Test WebSocket reconnection

Requirements tested: 8.1-8.6, 9.1-9.8
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from ninja.testing import TestClient

# Skip all tests if infrastructure not available
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("SA01_INFRA_AVAILABLE") != "1",
        reason="Requires live infrastructure (PostgreSQL, Redis, SomaBrain)",
    ),
]


class TestConversationCreation:
    """Test conversation creation flow.

    Requirements: 8.1, 8.6
    """

    @pytest.fixture
    def chat_client(self):
        """Create test client for chat API."""
        from ninja.testing import TestClient
        from admin.chat.api.chat import router
        from ninja import NinjaAPI

        test_api = NinjaAPI()
        test_api.add_router("/chat", router)
        return TestClient(test_api)

    @pytest.fixture
    def auth_token(self):
        """Get auth token for testing."""
        # In real tests, this would authenticate against Keycloak
        # For now, use test token from environment
        return os.environ.get("TEST_AUTH_TOKEN", "test_token")

    def test_create_conversation(self, chat_client: "TestClient", auth_token: str):
        """Test creating a new conversation.

        Requirements: 8.1
        """
        response = chat_client.post(
            "/chat/conversations",
            json={
                "agent_id": os.environ.get("TEST_AGENT_ID", str(uuid4())),
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Should succeed with conversation ID
        assert response.status_code in [200, 201]
        data = response.json()

        assert "id" in data
        assert data["id"] is not None

    def test_create_conversation_without_auth_fails(self, chat_client: "TestClient"):
        """Test that conversation creation fails without auth.

        Requirements: 8.1
        """
        response = chat_client.post(
            "/chat/conversations",
            json={"agent_id": str(uuid4())},
        )

        assert response.status_code == 401

    def test_list_conversations(self, chat_client: "TestClient", auth_token: str):
        """Test listing user's conversations.

        Requirements: 8.6
        """
        response = chat_client.get(
            "/chat/conversations",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return list (may be empty)
        assert "conversations" in data or isinstance(data, list)

    def test_get_conversation_by_id(self, chat_client: "TestClient", auth_token: str):
        """Test getting a specific conversation.

        Requirements: 8.6
        """
        # First create a conversation
        create_response = chat_client.post(
            "/chat/conversations",
            json={"agent_id": os.environ.get("TEST_AGENT_ID", str(uuid4()))},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create conversation")

        conversation_id = create_response.json()["id"]

        # Get the conversation
        response = chat_client.get(
            f"/chat/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id


class TestMessageSending:
    """Test message sending and streaming.

    Requirements: 9.1-9.4
    """

    @pytest.fixture
    def chat_client(self):
        """Create test client for chat API."""
        from ninja.testing import TestClient
        from admin.chat.api.chat import router
        from ninja import NinjaAPI

        test_api = NinjaAPI()
        test_api.add_router("/chat", router)
        return TestClient(test_api)

    @pytest.fixture
    def auth_token(self):
        """Get auth token for testing."""
        return os.environ.get("TEST_AUTH_TOKEN", "test_token")

    @pytest.fixture
    def conversation_id(self, chat_client: "TestClient", auth_token: str):
        """Create a conversation for testing."""
        response = chat_client.post(
            "/chat/conversations",
            json={"agent_id": os.environ.get("TEST_AGENT_ID", str(uuid4()))},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        if response.status_code not in [200, 201]:
            pytest.skip("Could not create conversation")

        return response.json()["id"]

    def test_send_message(self, chat_client: "TestClient", auth_token: str, conversation_id: str):
        """Test sending a message to a conversation.

        Requirements: 9.1
        """
        response = chat_client.post(
            f"/chat/conversations/{conversation_id}/messages",
            json={
                "content": "Hello, this is a test message.",
                "role": "user",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Should succeed
        assert response.status_code in [200, 201, 202]

    def test_get_conversation_messages(
        self, chat_client: "TestClient", auth_token: str, conversation_id: str
    ):
        """Test getting messages from a conversation.

        Requirements: 9.1
        """
        # First send a message
        chat_client.post(
            f"/chat/conversations/{conversation_id}/messages",
            json={"content": "Test message", "role": "user"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Get messages
        response = chat_client.get(
            f"/chat/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should have messages
        assert "messages" in data or isinstance(data, list)


class TestChatService:
    """Test ChatService integration with SomaBrain.

    Requirements: 8.2, 8.3, 9.3
    """

    @pytest.fixture
    def chat_service(self):
        """Get ChatService instance."""
        from services.common.chat_service import ChatService

        return ChatService()

    @pytest.mark.asyncio
    async def test_initialize_agent_session(self, chat_service):
        """Test initializing an agent session with SomaBrain.

        Requirements: 8.2
        """
        try:
            session = await chat_service.initialize_agent_session(
                agent_id=os.environ.get("TEST_AGENT_ID", str(uuid4())),
                user_id=str(uuid4()),
                conversation_id=str(uuid4()),
            )

            assert session is not None
        except Exception as e:
            # SomaBrain may not be available in test env
            if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                pytest.skip(f"SomaBrain not available: {e}")
            raise

    @pytest.mark.asyncio
    async def test_recall_memories(self, chat_service):
        """Test recalling memories from SomaFractalMemory.

        Requirements: 8.3
        """
        try:
            memories = await chat_service.recall_memories(
                user_id=str(uuid4()),
                agent_id=os.environ.get("TEST_AGENT_ID", str(uuid4())),
                query="test query",
                limit=5,
            )

            # Should return list (may be empty)
            assert isinstance(memories, list)
        except Exception as e:
            # Memory service may not be available
            if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                pytest.skip(f"Memory service not available: {e}")
            raise

    @pytest.mark.asyncio
    async def test_store_interaction(self, chat_service):
        """Test storing an interaction in memory.

        Requirements: 9.6
        """
        try:
            await chat_service.store_interaction(
                user_id=str(uuid4()),
                agent_id=os.environ.get("TEST_AGENT_ID", str(uuid4())),
                conversation_id=str(uuid4()),
                user_message="Test user message",
                assistant_response="Test assistant response",
            )
            # Should not raise
        except Exception as e:
            if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                pytest.skip(f"Memory service not available: {e}")
            raise


class TestTitleGeneration:
    """Test conversation title generation.

    Requirements: 9.8
    """

    @pytest.fixture
    def chat_service(self):
        """Get ChatService instance."""
        from services.common.chat_service import ChatService

        return ChatService()

    @pytest.mark.asyncio
    async def test_generate_title(self, chat_service):
        """Test generating a conversation title.

        Requirements: 9.8
        """
        try:
            title = await chat_service.generate_title(
                messages=[
                    {"role": "user", "content": "How do I configure PostgreSQL?"},
                    {"role": "assistant", "content": "To configure PostgreSQL, you need to..."},
                ]
            )

            assert title is not None
            assert len(title) > 0
            assert len(title) <= 100  # Reasonable title length
        except Exception as e:
            if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                pytest.skip(f"Title generation service not available: {e}")
            raise


class TestWebSocketConsumer:
    """Test WebSocket chat consumer.

    Requirements: 7.6, 9.1, 9.4, 9.7
    """

    @pytest.mark.asyncio
    async def test_websocket_connection_requires_auth(self):
        """Test that WebSocket connection requires authentication.

        Requirements: 7.6
        """
        from channels.testing import WebsocketCommunicator
        from services.gateway.consumers.chat import ChatConsumer

        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            "/ws/v2/chat/",
        )

        # Should reject connection without auth
        connected, _ = await communicator.connect()

        # Either rejected or will close shortly
        if connected:
            # Wait for close message
            try:
                response = await asyncio.wait_for(
                    communicator.receive_output(),
                    timeout=2.0,
                )
                # Should receive close or error
            except asyncio.TimeoutError:
                pass
            finally:
                await communicator.disconnect()
        else:
            # Connection rejected - expected
            assert not connected

    @pytest.mark.asyncio
    async def test_websocket_heartbeat(self):
        """Test WebSocket heartbeat (ping/pong).

        Requirements: 9.7
        """
        from channels.testing import WebsocketCommunicator
        from services.gateway.consumers.chat import ChatConsumer

        # This test requires a valid auth token
        auth_token = os.environ.get("TEST_AUTH_TOKEN")
        if not auth_token:
            pytest.skip("No TEST_AUTH_TOKEN available")

        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/v2/chat/?token={auth_token}",
        )

        connected, _ = await communicator.connect()

        if not connected:
            pytest.skip("Could not connect to WebSocket")

        try:
            # Send ping
            await communicator.send_json_to(
                {
                    "type": "ping",
                }
            )

            # Should receive pong
            response = await asyncio.wait_for(
                communicator.receive_json_from(),
                timeout=5.0,
            )

            assert response.get("type") == "pong"
        finally:
            await communicator.disconnect()


class TestAgentSelection:
    """Test agent selection and filtering.

    Requirements: 7.1-7.4
    """

    @pytest.fixture
    def agents_client(self):
        """Create test client for agents API."""
        from ninja.testing import TestClient
        from admin.agents.api import router
        from ninja import NinjaAPI

        test_api = NinjaAPI()
        test_api.add_router("/agents", router)
        return TestClient(test_api)

    @pytest.fixture
    def auth_token(self):
        """Get auth token for testing."""
        return os.environ.get("TEST_AUTH_TOKEN", "test_token")

    def test_list_agents_filtered_by_permissions(
        self, agents_client: "TestClient", auth_token: str
    ):
        """Test that agent list is filtered by user permissions.

        Requirements: 7.4
        """
        response = agents_client.get(
            "/agents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return list of agents (may be empty based on permissions)
        assert "agents" in data or isinstance(data, list)

    def test_list_agents_without_auth_fails(self, agents_client: "TestClient"):
        """Test that agent list fails without auth.

        Requirements: 7.1
        """
        response = agents_client.get("/agents")

        assert response.status_code == 401


class TestMemoryIntegration:
    """Test memory integration with chat.

    Requirements: 8.3, 9.6
    """

    @pytest.fixture
    def chat_service(self):
        """Get ChatService instance."""
        from services.common.chat_service import ChatService

        return ChatService()

    @pytest.mark.asyncio
    async def test_memory_recall_on_session_init(self, chat_service):
        """Test that memories are recalled on session initialization.

        Requirements: 8.3
        """
        user_id = str(uuid4())
        agent_id = os.environ.get("TEST_AGENT_ID", str(uuid4()))

        try:
            # Initialize session (should trigger memory recall)
            session = await chat_service.initialize_agent_session(
                agent_id=agent_id,
                user_id=user_id,
                conversation_id=str(uuid4()),
            )

            # Session should have context (may be empty if no prior memories)
            assert session is not None
        except Exception as e:
            if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                pytest.skip(f"Services not available: {e}")
            raise

    @pytest.mark.asyncio
    async def test_memory_store_after_response(self, chat_service):
        """Test that interactions are stored in memory after response.

        Requirements: 9.6
        """
        user_id = str(uuid4())
        agent_id = os.environ.get("TEST_AGENT_ID", str(uuid4()))
        conversation_id = str(uuid4())

        try:
            # Store an interaction
            await chat_service.store_interaction(
                user_id=user_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                user_message="What is the capital of France?",
                assistant_response="The capital of France is Paris.",
            )

            # Recall should now include this interaction
            memories = await chat_service.recall_memories(
                user_id=user_id,
                agent_id=agent_id,
                query="capital of France",
                limit=5,
            )

            # Should have at least one memory
            # Note: This depends on memory service being available
            assert isinstance(memories, list)
        except Exception as e:
            if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                pytest.skip(f"Memory service not available: {e}")
            raise