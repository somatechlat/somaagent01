import json
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Any, Optional

import nest_asyncio

from agent import Agent, AgentConfig, AgentContext, AgentContextType
from initialize import initialize_agent
from python.helpers import files, history
from python.helpers.log import Log, LogItem
from services.common.session_repository import PostgresSessionStore

# Apply nest_asyncio to allow running async code in synchronous contexts if needed
nest_asyncio.apply()

# Global store instance
_store: Optional[PostgresSessionStore] = None

def get_store() -> PostgresSessionStore:
    global _store
    if _store is None:
        _store = PostgresSessionStore()
    return _store

CHATS_FOLDER = "tmp/chats"
LOG_SIZE = 1000

def get_chat_folder_path(ctxid: str):
    """
    Get the folder path for any context (chat or task) temporary files.
    """
    return files.get_abs_path(CHATS_FOLDER, ctxid)

def get_chat_msg_files_folder(ctxid: str):
    return files.get_abs_path(get_chat_folder_path(ctxid), "messages")

async def save_tmp_chat(context: AgentContext):
    """Save context to the database"""
    # Skip saving BACKGROUND contexts as they should be ephemeral
    if context.type == AgentContextType.BACKGROUND:
        return

    data = _serialize_context(context)
    store = get_store()
    await store.save_session_state(context.id, data)

async def save_tmp_chats():
    """Save all contexts to the database"""
    for _, context in AgentContext._contexts.items():
        # Skip BACKGROUND contexts as they should be ephemeral
        if context.type == AgentContextType.BACKGROUND:
            continue
        await save_tmp_chat(context)

async def load_tmp_chats() -> list[str]:
    """Load all contexts from the database"""
    store = get_store()
    # Ensure schema exists
    from services.common.session_repository import ensure_schema
    await ensure_schema(store)

    envelopes = await store.list_sessions(limit=1000)
    ctxids = []
    for env in envelopes:
        if env.state:
            try:
                # _deserialize_context registers the context in AgentContext._contexts
                ctx = _deserialize_context(env.state)
                ctxids.append(ctx.id)
            except Exception as e:
                print(f"Error loading chat {env.session_id}: {e}")
    return ctxids

async def load_json_chats(jsons: list[str]):
    """Load contexts from JSON strings"""
    ctxids = []
    for js in jsons:
        data = json.loads(js)
        if "id" in data:
            del data["id"]  # remove id to get new
        ctx = _deserialize_context(data)
        ctxids.append(ctx.id)
    return ctxids

def export_json_chat(context: AgentContext):
    """Export context as JSON string"""
    data = _serialize_context(context)
    js = _safe_json_serialize(data, ensure_ascii=False)
    return js

async def remove_chat(ctxid: str):
    """Remove a chat or task context from database"""
    store = get_store()
    await store.delete_session(ctxid)
    # Also clean up tmp files
    path = get_chat_folder_path(ctxid)
    files.delete_dir(path)

async def remove_msg_files(ctxid: str):
    """Remove all message files for a chat or task context"""
    path = get_chat_msg_files_folder(ctxid)
    files.delete_dir(path)

# Serialization logic (copied from persist_chat.py)

def _serialize_context(context: AgentContext):
    # serialize agents
    agents = []
    agent = context.agent0
    while agent:
        agents.append(_serialize_agent(agent))
        agent = agent.data.get(Agent.DATA_NAME_SUBORDINATE, None)

    return {
        "id": context.id,
        "name": context.name,
        "created_at": (
            context.created_at.isoformat()
            if context.created_at
            else datetime.fromtimestamp(0).isoformat()
        ),
        "type": context.type.value,
        "last_message": (
            context.last_message.isoformat()
            if context.last_message
            else datetime.fromtimestamp(0).isoformat()
        ),
        "agents": agents,
        "streaming_agent": (context.streaming_agent.number if context.streaming_agent else 0),
        "log": _serialize_log(context.log),
    }


def _serialize_agent(agent: Agent):
    data = {k: v for k, v in agent.data.items() if not k.startswith("_")}

    history = agent.history.serialize()

    return {
        "number": agent.number,
        "data": data,
        "history": history,
    }


def _serialize_log(log: Log):
    return {
        "guid": log.guid,
        "logs": [item.output() for item in log.logs[-LOG_SIZE:]],  # serialize LogItem objects
        "progress": log.progress,
        "progress_no": log.progress_no,
    }


def _deserialize_context(data):
    config = initialize_agent()
    log = _deserialize_log(data.get("log", None))

    context = AgentContext(
        config=config,
        id=data.get("id", None),  # get new id
        name=data.get("name", None),
        created_at=(
            datetime.fromisoformat(
                # older chats may not have created_at - backcompat
                data.get("created_at", datetime.fromtimestamp(0).isoformat())
            )
        ),
        type=AgentContextType(data.get("type", AgentContextType.USER.value)),
        last_message=(
            datetime.fromisoformat(data.get("last_message", datetime.fromtimestamp(0).isoformat()))
        ),
        log=log,
        paused=False,
        # agent0=agent0,
        # streaming_agent=straming_agent,
    )

    agents = data.get("agents", [])
    agent0 = _deserialize_agents(agents, config, context)
    streaming_agent = agent0
    while streaming_agent and streaming_agent.number != data.get("streaming_agent", 0):
        streaming_agent = streaming_agent.data.get(Agent.DATA_NAME_SUBORDINATE, None)

    context.agent0 = agent0
    context.streaming_agent = streaming_agent

    return context


def _deserialize_agents(
    agents: list[dict[str, Any]], config: AgentConfig, context: AgentContext
) -> Agent:
    prev: Agent | None = None
    zero: Agent | None = None

    for ag in agents:
        current = Agent(
            number=ag["number"],
            config=config,
            context=context,
        )
        current.data = ag.get("data", {})
        current.history = history.deserialize_history(ag.get("history", ""), agent=current)
        if not zero:
            zero = current

        if prev:
            prev.set_data(Agent.DATA_NAME_SUBORDINATE, current)
            current.set_data(Agent.DATA_NAME_SUPERIOR, prev)
        prev = current

    return zero or Agent(0, config, context)


def _deserialize_log(data: dict[str, Any]) -> "Log":
    log = Log()
    log.guid = data.get("guid", str(uuid.uuid4()))
    log.set_initial_progress()

    # Deserialize the list of LogItem objects
    i = 0
    for item_data in data.get("logs", []):
        log.logs.append(
            LogItem(
                log=log,  # restore the log reference
                no=i,  # item_data["no"],
                type=item_data["type"],
                heading=item_data.get("heading", ""),
                content=item_data.get("content", ""),
                kvps=OrderedDict(item_data["kvps"]) if item_data["kvps"] else None,
                temp=item_data.get("temp", False),
            )
        )
        log.updates.append(i)
        i += 1

    return log


def _safe_json_serialize(obj, **kwargs):
    def serializer(o):
        if isinstance(o, dict):
            return {k: v for k, v in o.items() if is_json_serializable(v)}
        elif isinstance(o, (list, tuple)):
            return [item for item in o if is_json_serializable(item)]
        elif is_json_serializable(o):
            return o
        else:
            return None  # Skip this property

    def is_json_serializable(item):
        try:
            json.dumps(item)
            return True
        except (TypeError, OverflowError):
            return False

    return json.dumps(obj, default=serializer, **kwargs)
