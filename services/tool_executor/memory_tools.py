"""Memory management tools for SomaAgent 01."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.tool_executor.tools import AVAILABLE_TOOLS, BaseTool, ToolExecutionError
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError

LOGGER = logging.getLogger(__name__)


class MemorySaveTool(BaseTool):
    name = "memory_save"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        content = args.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ToolExecutionError("'content' is required")
        
        fact_type = args.get("fact_type", "episodic")
        tags = args.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
            
        # Ensure fact_type is valid
        valid_types = {"episodic", "semantic", "goal", "reflection", "procedural"}
        if fact_type not in valid_types:
            # Soft fallback instead of error, tag it
            tags.append(f"type:{fact_type}")
            fact_type = "episodic"

        client = SomaBrainClient.get()
        try:
            # We use the 'remember' method which handles the API call
            # Note: The client wrapper handles tenant/namespace resolution
            result = await client.remember(
                payload={
                    "content": content,
                    "fact": fact_type,
                    "tags": tags,
                    "metadata": args.get("metadata") or {},
                },
                tenant=args.get("tenant_id"),  # Optional, client will resolve
                importance=args.get("importance"),  # Optional float
            )
            return {
                "status": "success",
                "memory_id": result.get("key") or result.get("id"),
                "fact_type": fact_type
            }
        except SomaClientError as exc:
            LOGGER.error("SomaBrain memory save failed", extra={"error": str(exc)})
            raise ToolExecutionError(f"Failed to save memory: {exc}")
        except Exception as exc:
            LOGGER.exception("Unexpected error in memory_save")
            raise ToolExecutionError("Internal error saving memory")

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory content to save"
                },
                "fact_type": {
                    "type": "string",
                    "enum": ["episodic", "semantic", "goal", "reflection", "procedural"],
                    "description": "Type of memory (default: episodic)",
                    "default": "episodic"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for categorization"
                },
                "importance": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Optional importance score (0.0-1.0)"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional structured metadata"
                }
            },
            "required": ["content"],
            "additionalProperties": False,
        }


class UpdateBehaviorTool(BaseTool):
    name = "update_behavior"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        behavior = args.get("behavior_description")
        if not isinstance(behavior, str) or not behavior.strip():
            raise ToolExecutionError("'behavior_description' is required")
            
        action = args.get("action", "add")
        if action not in {"add", "modify", "delete"}:
            raise ToolExecutionError("Action must be 'add', 'modify', or 'delete'")

        client = SomaBrainClient.get()
        try:
            # Behavior rules are just memories with fact="behavior_rule" and tag="behavior_rule"
            # The action (add/modify/delete) is semantic for now, as we append new rules.
            # Real deletion would require searching first, which is complex for a single tool call.
            # For "delete", we add a rule that explicitly negates the previous one.
            
            content = behavior
            if action == "delete":
                content = f"IGNORE PREVIOUS RULE: {behavior}"
            elif action == "modify":
                content = f"UPDATED RULE: {behavior}"

            result = await client.remember(
                payload={
                    "content": content,
                    "fact": "behavior_rule",
                    "tags": ["behavior_rule", f"action:{action}"],
                    "metadata": {"original_action": action},
                },
                tenant=args.get("tenant_id"),
                importance=1.0,  # Behavior rules are always important
            )
            return {
                "status": "success",
                "memory_id": result.get("key") or result.get("id"),
                "action": action,
                "note": "Behavior rule updated. It will be active in the next turn."
            }
        except SomaClientError as exc:
            LOGGER.error("SomaBrain behavior update failed", extra={"error": str(exc)})
            raise ToolExecutionError(f"Failed to update behavior: {exc}")

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "behavior_description": {
                    "type": "string",
                    "description": "Description of the behavior rule to add/modify/delete"
                },
                "action": {
                    "type": "string",
                    "enum": ["add", "modify", "delete"],
                    "description": "Action to perform (default: add)",
                    "default": "add"
                }
            },
            "required": ["behavior_description"],
            "additionalProperties": False,
        }


class RequestPlanTool(BaseTool):
    name = "request_plan"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        goal = args.get("goal")
        if not isinstance(goal, str) or not goal.strip():
            raise ToolExecutionError("'goal' is required")
        
        max_steps = args.get("max_steps", 5)
        if not isinstance(max_steps, int) or max_steps < 1 or max_steps > 20:
            max_steps = 5

        client = SomaBrainClient.get()
        try:
            # 1. Search for goal in Memory (fact="goal")
            recall_result = await client.recall(
                payload={
                    "query": goal,
                    "tags": ["goal"],
                    "top_k": 1
                },
                tenant=args.get("tenant_id")
            )
            
            results = recall_result.get("results", [])
            if not results:
                return {
                    "status": "error",
                    "error": "Goal not found in memory. Please save it first using memory_save with fact_type='goal'."
                }
            
            # Extract memory key from the first result
            goal_payload = results[0].get("payload", {})
            goal_key = goal_payload.get("key") or goal_payload.get("id")
            
            if not goal_key:
                LOGGER.warning("Goal memory found but no key present")
                return {
                    "status": "error",
                    "error": "Goal memory found but could not extract key"
                }
            
            # 2. Request plan from SomaBrain via /plan/suggest
            plan_response = await client.plan_suggest(
                payload={
                    "task_key": goal_key,
                    "max_steps": max_steps,
                    "rel_types": ["causes", "requires", "follows"],
                    "universe": args.get("universe")
                }
            )
            
            plan_keys = plan_response.get("plan", [])
            
            if not plan_keys:
                return {
                    "status": "success",
                    "plan": [],
                    "message": f"No plan steps found for goal: {goal}"
                }
            
            # 3. Retrieve details for each plan step
            steps = []
            for idx, key in enumerate(plan_keys):
                step_recall = await client.recall(
                    payload={
                        "query": key,
                        "top_k": 1
                    },
                    tenant=args.get("tenant_id")
                )
                
                step_results = step_recall.get("results", [])
                if step_results:
                    step_payload = step_results[0].get("payload", {})
                    steps.append({
                        "step_number": idx + 1,
                        "key": key,
                        "content": step_payload.get("value") or step_payload.get("content"),
                        "metadata": step_payload.get("metadata", {})
                    })
            
            return {
                "status": "success",
                "plan": steps,
                "total_steps": len(steps),
                "goal": goal,
                "message": f"Generated {len(steps)}-step plan for: {goal}"
            }
            
        except SomaClientError as exc:
            LOGGER.error("SomaBrain plan_suggest failed", extra={"error": str(exc)})
            raise ToolExecutionError(f"Failed to request plan: {exc}")
        except Exception as exc:
            LOGGER.exception("Unexpected error in request_plan")
            raise ToolExecutionError("Internal error requesting plan")

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The goal description to plan for"
                },
                "max_steps": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "description": "Maximum number of plan steps (default: 5)",
                    "default": 5
                }
            },
            "required": ["goal"],
            "additionalProperties": False,
        }


# Register tools
AVAILABLE_TOOLS[MemorySaveTool.name] = MemorySaveTool()
AVAILABLE_TOOLS[UpdateBehaviorTool.name] = UpdateBehaviorTool()
AVAILABLE_TOOLS[RequestPlanTool.name] = RequestPlanTool()
