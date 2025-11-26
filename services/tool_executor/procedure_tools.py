import uuid
from typing import List, Type

from pydantic import BaseModel, Field

from python.integrations.soma_client import SomaClient
from services.tool_executor.tools import BaseTool
from src.core.config import cfg


class SaveProcedureInput(BaseModel):
    title: str = Field(..., description="Unique title of the procedure")
    description: str = Field(..., description="Brief description of what the procedure achieves")
    steps: List[str] = Field(..., description="Ordered list of steps to execute")
    tags: List[str] = Field(default_factory=list, description="Tags for searchability")


class SaveProcedureTool(BaseTool):
    name = "save_procedure"
    description = "Save a reusable procedure (how-to knowledge) to memory."
    args_schema: Type[BaseModel] = SaveProcedureInput

    async def run(
        self, title: str, description: str, steps: List[str], tags: List[str] = []
    ) -> str:
        client = SomaClient(cfg.soma_base_url, api_key=cfg.soma_api_key)
        proc_id = str(uuid.uuid4())

        # Ensure 'procedure' tag is present
        if "procedure" not in tags:
            tags.append("procedure")

        procedure_data = {
            "id": proc_id,
            "title": title,
            "description": description,
            "steps": steps,
            "tags": tags,
            "fact": "procedure",
        }

        # Store in SomaBrain
        # We use a random ID to ensure uniqueness.
        # Future improvement: Check for title uniqueness before saving.

        await client.remember(
            key=f"proc:{proc_id}", value=procedure_data, namespace="procedures", tags=tags
        )
        return f"Procedure '{title}' saved with ID: {proc_id}"


class SearchProceduresInput(BaseModel):
    query: str = Field(..., description="Search query (e.g., 'how to deploy')")


class SearchProceduresTool(BaseTool):
    name = "search_procedures"
    description = "Search for procedures in memory."
    args_schema: Type[BaseModel] = SearchProceduresInput

    async def run(self, query: str) -> str:
        client = SomaClient(cfg.soma_base_url, api_key=cfg.soma_api_key)

        # Use recall with the query.
        # We rely on semantic search to find relevant procedures.
        # The semantic match "how to X" naturally surfaces procedures.

        results = await client.recall(query=query, top_k=5)

        found = []
        if "results" in results:
            for item in results["results"]:
                payload = item.get("payload", {})
                if payload.get("fact") == "procedure":
                    found.append(
                        f"ID: {payload.get('id')}\nTitle: {payload.get('title')}\nDescription: {payload.get('description')}"
                    )

        if not found:
            return "No relevant procedures found."
        return "\n---\n".join(found)


class GetProcedureInput(BaseModel):
    procedure_id: str = Field(..., description="ID of the procedure to retrieve")


class GetProcedureTool(BaseTool):
    name = "get_procedure"
    description = "Retrieve the full steps of a specific procedure."
    args_schema: Type[BaseModel] = GetProcedureInput

    async def run(self, procedure_id: str) -> str:
        client = SomaClient(cfg.soma_base_url, api_key=cfg.soma_api_key)

        # Retrieve the procedure by searching for its ID.
        # This acts as a lookup mechanism until a direct key-based GET is exposed.

        # Let's try to search by ID.
        results = await client.recall(query=f"procedure id {procedure_id}", top_k=1)

        if "results" in results:
            for item in results["results"]:
                payload = item.get("payload", {})
                if payload.get("id") == procedure_id:
                    steps = payload.get("steps", [])
                    formatted_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                    return f"Title: {payload.get('title')}\n\nSteps:\n{formatted_steps}"

        return f"Procedure {procedure_id} not found."
