import os

os.getenv(os.getenv(""))
from __future__ import annotations

from typing import Any, Dict, List

import httpx

from python.integrations.soma_client import SomaClient, SomaClientError
from src.core.config import cfg


class SomaBrainClient(SomaClient):
    os.getenv(os.getenv(""))


def _base_url() -> str:
    os.getenv(os.getenv(""))
    url = cfg.env(os.getenv(os.getenv("")))
    if url:
        return url
    return cfg.settings().external.somabrain_base_url


def _handle_response(resp: httpx.Response) -> Any:
    os.getenv(os.getenv(""))
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise SomaClientError(str(exc)) from exc
    return resp.json()


def get_weights() -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    resp = httpx.get(f"{_base_url()}/v1/weights")
    return _handle_response(resp)


def update_weights(payload: Dict[str, Any]) -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    resp = httpx.post(f"{_base_url()}/v1/weights/update", json=payload)
    return _handle_response(resp)


def build_context(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    os.getenv(os.getenv(""))
    resp = httpx.post(f"{_base_url()}/v1/context/build", json=payload)
    return _handle_response(resp)


def get_tenant_flag(tenant: str, flag: str) -> bool:
    os.getenv(os.getenv(""))
    resp = httpx.get(f"{_base_url()}/v1/flags/{tenant}/{flag}")
    data = _handle_response(resp)
    return bool(data.get(os.getenv(os.getenv(""))))


def get_persona(persona_id: str) -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    resp = httpx.get(f"{_base_url()}/persona/{persona_id}")
    return _handle_response(resp)


def put_persona(persona_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    resp = httpx.put(f"{_base_url()}/persona/{persona_id}", json=payload)
    return _handle_response(resp)


async def get_weights_async() -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_base_url()}/v1/weights")
    return _handle_response(resp)


async def build_context_async(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_base_url()}/v1/context/build", json=payload)
    return _handle_response(resp)


async def publish_reward_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{_base_url()}/v1/learning/reward", json=payload)
    return _handle_response(resp)


async def get_tenant_flag_async(tenant: str, flag: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_base_url()}/v1/flags/{tenant}/{flag}")
    data = _handle_response(resp)
    return bool(data.get(os.getenv(os.getenv(""))))


__all__ = [
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
    os.getenv(os.getenv("")),
]
