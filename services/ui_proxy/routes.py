from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from services.ui_proxy.client import GatewayClient
from services.ui_proxy.service import PollAggregator, UiMessageService

LOGGER = logging.getLogger(__name__)


def get_gateway_client() -> GatewayClient:
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
