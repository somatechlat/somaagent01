from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from services.ui_proxy.client import GatewayClient
from services.ui_proxy.service import PollAggregator, UiMessageService

LOGGER = logging.getLogger(__name__)


def get_gateway_client(request: Request) -> GatewayClient:
	"""Construct a GatewayClient for intra-gateway calls.

	Precedence:
	1) Respect explicit GATEWAY_BASE_URL if set (works in any environment).
	2) If UI_PROXY_USE_REQUEST_BASE=true, use the incoming request.base_url.
	3) Otherwise fall back to the internal default (e.g., http://gateway:8010).

	Rationale: Inside Docker, request.base_url often points at the host‑mapped
	port (e.g., 127.0.0.1:21016) which is not reachable from within the
	container. Using the internal service DNS avoids connection errors.
	"""
	import os

	# 1) Explicit override via env
	if os.getenv("GATEWAY_BASE_URL"):
		return GatewayClient()

	# 2) Opt-in to using request.base_url (useful for single-process local runs)
	if os.getenv("UI_PROXY_USE_REQUEST_BASE", "false").lower() in {"true", "1", "yes", "on"}:
		try:
			base = str(request.base_url).rstrip("/")
			return GatewayClient(base_url=base)
		except Exception:
			pass

	# 3) Safe default: internal service DNS or default constructed URL
	return GatewayClient()


router = APIRouter()


@router.get("/health")
async def health() -> Dict[str, str]:
	return {"status": "ok"}


@router.post("/v1/ui/message")
async def send_message(
	request: Request,
	client: GatewayClient = Depends(get_gateway_client),
) -> JSONResponse:
	service = UiMessageService()
	# Be tolerant to invalid/missing JSON and unexpected content-types
	try:
		payload = await service.handle_request(request, client)
	except Exception as exc:
		# Try to read raw body as text and fallback to empty message payload
		try:
			_ = await request.body()
		except Exception:
			pass
		# Return a consistent 400 for bad requests instead of a 500
		from fastapi import HTTPException
		raise HTTPException(status_code=400, detail=f"Invalid request payload: {type(exc).__name__}")
	return JSONResponse(payload)


@router.post("/v1/ui/poll")
async def poll(
	request: Request,
	client: GatewayClient = Depends(get_gateway_client),
) -> JSONResponse:
	# Accept empty bodies and invalid JSON by defaulting to an empty object
	try:
		body: Dict[str, Any] = await request.json()
		if not isinstance(body, dict):
			body = {}
	except Exception:
		body = {}
	aggregator = PollAggregator(client)
	payload = await aggregator.poll(body)
	return JSONResponse(payload)
