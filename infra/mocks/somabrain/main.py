"""
Minimal mock SomaBrain service for standalone development.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock SomaBrain", version="1.0.0")


@app.get("/api/health/")
def health():
    return {"status": "ok", "service": "somabrain"}


@app.post("/api/v1/agents/{agent_id}/sessions")
def create_session(agent_id: str):
    return {
        "session_id": f"sess_{agent_id}_001",
        "agent_id": agent_id,
        "status": "active",
        "message": "Session created (mock)",
    }


@app.post("/api/v1/agents/{agent_id}/chat")
def chat(agent_id: str):
    return {
        "agent_id": agent_id,
        "response": "This is a mock response from SomaBrain.",
        "status": "completed",
        "message": "Chat processed (mock)",
    }
