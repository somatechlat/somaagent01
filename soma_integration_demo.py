import asyncio
import logging
from typing import Any, Mapping

from python.integrations.soma_client import SomaClient, SomaClientError
from services.gateway.degradation_monitor import degradation_monitor, DegradationMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_soma_brain() -> Mapping[str, Any]:
    client = SomaClient.get()
    payload = {"id": "demo-1", "content": "example memory", "metadata": {"source": "demo"}}
    remember_res = await client.remember(payload)
    recall_res = await client.recall(query="example memory")
    health_res = await client.health()
    return {"remember": remember_res, "recall": recall_res, "health": health_res}


async def demo_degradation_monitor() -> None:
    monitor: DegradationMonitor = degradation_monitor
    await monitor.initialize()
    await monitor.start_monitoring()
    await monitor.record_component_success("somabrain", response_time=0.12)
    await monitor.record_component_failure("somabrain", Exception("simulated failure"))
    await asyncio.sleep(2)
    status = await monitor.get_degradation_status()
    logger.info("Degradation status: %s", status)
    await monitor.stop_monitoring()


async def main() -> None:
    try:
        soma = await demo_soma_brain()
        logger.info("SomaBrain results: %s", soma)
    except SomaClientError as e:
        logger.error("SomaBrain error: %s", e)
    await demo_degradation_monitor()


if __name__ == "__main__":
    asyncio.run(main())
