from fastapi import APIRouter, Depends
from typing import List
from services.common.ui_settings_store import UiSettingsStore

async def get_settings_repo():
    """Get settings repository for backwards compatibility."""
    return UiSettingsStore()

router = APIRouter(prefix="/v1/tools", tags=["tools"])

@router.get("/")
async def list_tools(repo=Depends(get_settings_repo)) -> List[dict]:
    """Return canonical tool descriptors from central catalog."""
    rows = await repo.fetch_all("SELECT * FROM tool_catalog WHERE enabled = TRUE")
    return [
        {
            "name": r["name"],
            "description": r["description"],
            "parameters": r["parameters_schema"],
            "enabled": r["enabled"],
            "cost_impact": r["cost_impact"],
            "profiles": r["profiles"]
        }
        for r in rows
    ]