"""Tools for managing agent goals."""

import uuid
from typing import Type

from pydantic import BaseModel, Field

from python.integrations.soma_client import SomaClient
from services.tool_executor.tools import BaseTool
from src.core.config import cfg


class CreateGoalInput(BaseModel):
    description: str = Field(..., description="Description of the goal to create")
    priority: int = Field(1, description="Priority of the goal (1-5)")


class CreateGoalTool(BaseTool):
    name = "create_goal"
    description = "Create a new goal for the agent."
    args_schema: Type[BaseModel] = CreateGoalInput

    async def run(self, description: str, priority: int = 1) -> str:
        client = SomaClient(cfg.soma_base_url, api_key=cfg.soma_api_key)
        goal_id = str(uuid.uuid4())
        goal_data = {
            "id": goal_id,
            "description": description,
            "priority": priority,
            "status": "active",
            "fact": "goal",
        }

        # Store in SomaBrain with specific namespace and fact tag
        await client.remember(
            key=f"goal:{goal_id}", value=goal_data, namespace="goals", tags=["goal", "active"]
        )
        return f"Goal created with ID: {goal_id}"


class UpdateGoalInput(BaseModel):
    goal_id: str = Field(..., description="ID of the goal to update")
    status: str = Field(..., description="New status (active, completed, abandoned)")


class UpdateGoalTool(BaseTool):
    name = "update_goal"
    description = "Update the status of an existing goal."
    args_schema: Type[BaseModel] = UpdateGoalInput

    async def run(self, goal_id: str, status: str) -> str:
        client = SomaClient(cfg.soma_base_url, api_key=cfg.soma_api_key)

        # Update the goal status.
        # We write a new version of the goal object with the updated status.
        # SomaBrain handles key-based upserts, so this will update the current state.

        update_data = {"id": goal_id, "status": status, "fact": "goal_update"}

        await client.remember(
            key=f"goal:{goal_id}",  # Re-using key to hopefully update/version it
            value=update_data,
            namespace="goals",
            tags=["goal", status],
        )
        return f"Goal {goal_id} updated to {status}"


class ListGoalsTool(BaseTool):
    name = "list_goals"
    description = "List all active goals."
    args_schema: Type[BaseModel] = BaseModel

    async def run(self) -> str:
        client = SomaClient(cfg.soma_base_url, api_key=cfg.soma_api_key)
        # Recall memories with tag "goal" and "active".
        # We use a semantic query to retrieve relevant goals.
        results = await client.recall(query="current active goals", top_k=10)
        results = await client.recall(query="current active goals", top_k=10)

        goals = []
        if "results" in results:
            for item in results["results"]:
                # Filter client-side for now if needed, or trust the semantic search
                payload = item.get("payload", {})
                if payload.get("fact") == "goal" and payload.get("status") == "active":
                    goals.append(
                        f"{payload.get('id')}: {payload.get('description')} (Priority: {payload.get('priority')})"
                    )

        if not goals:
            return "No active goals found."
        return "\n".join(goals)
