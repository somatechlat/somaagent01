"""Model scoring job for SomaAgent 01."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta

from services.common.model_profiles import ModelProfileStore
from services.common.telemetry_store import TelemetryStore

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


class ScoringJob:
    def __init__(self) -> None:
        self.telemetry = TelemetryStore()
        self.profiles = ModelProfileStore()
        self.window_hours = int(os.getenv("SCORING_WINDOW_HOURS", "6"))

    async def run_once(self) -> None:
        pool = await self.telemetry._ensure_pool()
        window_end = datetime.utcnow()
        window_start = window_end - timedelta(hours=self.window_hours)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT model, avg(latency_seconds) AS avg_latency,
                       avg(input_tokens + output_tokens) AS avg_tokens
                FROM slm_metrics
                WHERE occurred_at BETWEEN $1 AND $2
                GROUP BY model
                """,
                window_start,
                window_end,
            )
        for row in rows:
            model = row["model"]
            avg_latency = float(row["avg_latency"] or 0)
            avg_tokens = float(row["avg_tokens"] or 0)
            score = self._score_model(avg_latency, avg_tokens)
            await self.telemetry.save_model_score(
                model=model,
                deployment_mode=os.getenv("SOMA_AGENT_MODE", "LOCAL"),
                window_start=window_start,
                window_end=window_end,
                avg_latency=avg_latency,
                avg_tokens=avg_tokens,
                score=score,
                extra={"window_hours": self.window_hours},
            )
            LOGGER.info(
                "Updated model score", extra={"model": model, "score": score, "latency": avg_latency}
            )

    def _score_model(self, latency: float, tokens: float) -> float:
        return max(0.0, 1.0 / (1.0 + latency + (tokens / 1000.0)))


async def main() -> None:
    job = ScoringJob()
    while True:
        try:
            await job.run_once()
        except Exception as exc:  # pragma: no cover - background job
            LOGGER.exception("Scoring job failed", extra={"error": str(exc)})
        await asyncio.sleep(int(os.getenv("SCORING_INTERVAL_SECONDS", "3600")))


if __name__ == "__main__":
    asyncio.run(main())
