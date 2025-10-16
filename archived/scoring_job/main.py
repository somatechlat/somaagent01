"""Model scoring job for SomaAgent 01."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta

from services.common.logging_config import setup_logging
from services.common.model_profiles import ModelProfileStore
from services.common.settings_sa01 import SA01Settings
from services.common.telemetry_store import TelemetryStore
from services.common.tracing import setup_tracing

setup_logging()
LOGGER = logging.getLogger(__name__)

JOB_SETTINGS = SA01Settings.from_env()
setup_tracing("scoring-job", endpoint=JOB_SETTINGS.otlp_endpoint)


class ScoringJob:
    def __init__(self) -> None:
        self.telemetry = TelemetryStore.from_settings(JOB_SETTINGS)
        self.profiles = ModelProfileStore.from_settings(JOB_SETTINGS)
        default_window = JOB_SETTINGS.extra.get("scoring_window_hours", 6)
        self.window_hours = int(os.getenv("SCORING_WINDOW_HOURS", str(default_window)))

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
                deployment_mode=os.getenv("SOMA_AGENT_MODE", JOB_SETTINGS.deployment_mode).upper(),
                window_start=window_start,
                window_end=window_end,
                avg_latency=avg_latency,
                avg_tokens=avg_tokens,
                score=score,
                extra={"window_hours": self.window_hours},
            )
            LOGGER.info(
                "Updated model score",
                extra={"model": model, "score": score, "latency": avg_latency},
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
        default_interval = JOB_SETTINGS.extra.get("scoring_interval_seconds", 3600)
        await asyncio.sleep(int(os.getenv("SCORING_INTERVAL_SECONDS", str(default_interval))))


if __name__ == "__main__":
    asyncio.run(main())
