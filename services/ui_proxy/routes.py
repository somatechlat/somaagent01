from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from services.ui_proxy.client import GatewayClient
from services.ui_proxy.service import PollAggregator, UiMessageService

LOGGER = logging.getLogger(__name__)


def get_gateway_client(request: Request) -> GatewayClient:
	"""Construct a GatewayClient pointing at this same server's base URL.

	Fallbacks:
	- If GATEWAY_BASE_URL is set, GatewayClient will already honor it.
	- Otherwise, prefer the incoming request's base_url to avoid hardcoded
	  container DNS names like http://gateway:8010 that aren't resolvable in
	  single-process or host-local runs.
	"""
	try:
		base = str(request.base_url).rstrip("/")
		return GatewayClient(base_url=base)
	except Exception:
		# Final fallback to default behavior
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
	payload = await service.handle_request(request, client)
	return JSONResponse(payload)


@router.post("/v1/ui/poll")
async def poll(
	request: Request,
	client: GatewayClient = Depends(get_gateway_client),
) -> JSONResponse:
	body: Dict[str, Any] = await request.json()
	aggregator = PollAggregator(client)
	payload = await aggregator.poll(body)
	return JSONResponse(payload)
