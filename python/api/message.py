import os
import json
from typing import Any, Dict

import httpx

from werkzeug.utils import secure_filename

from agent import AgentContext, UserMessage
from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.defer import DeferredTask
from python.helpers.print_style import PrintStyle


class Message(ApiHandler):
    async def _use_gateway(self) -> bool:
        flag = os.getenv("UI_USE_GATEWAY", "false").strip().lower()
        return flag in {"1", "true", "yes", "on"}

    def _gateway_base(self) -> str:
        # When running inside docker-compose, the gateway hostname resolves to "gateway:8010"
        return os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")

    def _gateway_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"
        # Optional persona/universe hints forwarded via headers
        if (universe := os.getenv("UI_UNIVERSE_ID")):
            headers["X-Universe-Id"] = universe
        if (persona := os.getenv("UI_PERSONA_ID")):
            headers["X-Persona-Id"] = persona
        if (agent_profile := os.getenv("UI_AGENT_PROFILE_ID")):
            headers["X-Agent-Profile"] = agent_profile
        return headers

    async def process(self, input: dict, request: Request) -> dict | Response:
        # When UI_USE_GATEWAY=true, forward the message to the Gateway instead of executing locally.
        if await self._use_gateway():
            try:
                text = input.get("text", "")
                metadata = input.get("metadata") or {}
                # Allow tenant override via UI_TENANT_ID env for dev convenience
                if os.getenv("UI_TENANT_ID") and not metadata.get("tenant"):
                    metadata["tenant"] = os.getenv("UI_TENANT_ID")
                payload: Dict[str, Any] = {"message": text, "attachments": [], "metadata": metadata}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{self._gateway_base()}/v1/session/message",
                        headers=self._gateway_headers(),
                        content=json.dumps(payload),
                    )
                resp.raise_for_status()
                body = resp.json()
                # Return an accepted-style response for the UI; immediate assistant message is produced asynchronously via SSE.
                return {
                    "accepted": True,
                    "session_id": body.get("session_id"),
                    "event_id": body.get("event_id"),
                }
            except Exception as exc:
                # Fall back to local pipeline if gateway path fails
                PrintStyle().print(f"Gateway path failed ({type(exc).__name__}): falling back to local agent")
                task, context = await self.communicate(input=input, request=request)
                return await self.respond(task, context)

        # Default: run through the local Agent pipeline
        task, context = await self.communicate(input=input, request=request)
        return await self.respond(task, context)

    async def respond(self, task: DeferredTask, context: AgentContext):
        result = await task.result()  # type: ignore
        return {
            "message": result,
            "context": context.id,
        }

    async def communicate(self, input: dict, request: Request):
        # Handle both JSON and multipart/form-data
        if request.content_type.startswith("multipart/form-data"):
            text = request.form.get("text", "")
            ctxid = request.form.get("context", "")
            message_id = request.form.get("message_id", None)
            attachments = request.files.getlist("attachments")
            attachment_paths = []

            upload_folder_int = "/git/agent-zero/tmp/uploads"
            upload_folder_ext = files.get_abs_path("tmp/uploads")  # for development environment

            if attachments:
                os.makedirs(upload_folder_ext, exist_ok=True)
                for attachment in attachments:
                    if attachment.filename is None:
                        continue
                    filename = secure_filename(attachment.filename)
                    save_path = files.get_abs_path(upload_folder_ext, filename)
                    attachment.save(save_path)
                    attachment_paths.append(os.path.join(upload_folder_int, filename))
        else:
            # Handle JSON request as before
            input_data = request.get_json()
            text = input_data.get("text", "")
            ctxid = input_data.get("context", "")
            message_id = input_data.get("message_id", None)
            attachment_paths = []

        # Now process the message
        message = text

        # Obtain agent context
        context = self.get_context(ctxid)

        # Store attachments in agent data
        # context.agent0.set_data("attachments", attachment_paths)

        # Prepare attachment filenames for logging
        attachment_filenames = (
            [os.path.basename(path) for path in attachment_paths] if attachment_paths else []
        )

        # Print to console and log
        PrintStyle(background_color="#6C3483", font_color="white", bold=True, padding=True).print(
            "User message:"
        )
        PrintStyle(font_color="white", padding=False).print(f"> {message}")
        if attachment_filenames:
            PrintStyle(font_color="white", padding=False).print("Attachments:")
            for filename in attachment_filenames:
                PrintStyle(font_color="white", padding=False).print(f"- {filename}")

        # Log the message with message_id and attachments
        context.log.log(
            type="user",
            heading="User message",
            content=message,
            kvps={"attachments": attachment_filenames},
            id=message_id,
        )

        return context.communicate(UserMessage(message, attachment_paths)), context
