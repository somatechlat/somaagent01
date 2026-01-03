"""Portfolio Ranker for optimizing multimodal provider selection.

Uses historical execution data from SomaBrain to rank provider candidates.
Currently operates in Shadow Mode for data collection and validation.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from services.common.soma_brain_outcomes import SomaBrainOutcomesStore, MultimodalOutcome

logger = logging.getLogger(__name__)


@dataclass
class CandidateScore:
    provider_name: str
    score: float
    metrics: Dict[str, float]


class PortfolioRanker:
    """Ranks provider candidates based on historical performance."""

    def __init__(self, soma_client: SomaBrainOutcomesStore) -> None:
        self.client = soma_client

    async def rank(
        self,
        candidates: List[Tuple[str, str]],
        step_type: str,
        context: Optional[Dict] = None,
    ) -> List[Tuple[str, str]]:
        """Rank candidates by performance score.

        Args:
            candidates: List of (provider_name, model_name) tuples.
            step_type: The type of step (e.g., 'generate_image').
            context: Additional context (optional).

        Returns:
            Reordered list of candidates (best first).
        """
        if not candidates:
            return []

        # Fetch history for this step type
        # In a real heavy-load system, this would be cached or aggregated asynchronously.
        history = await self.client.fetch_outcomes(step_type=step_type, limit=100)

        scores: List[Tuple[Tuple[str, str], float]] = []

        for prov, model in candidates:
            prov_key = prov  # Providers are identified by unique name in capabilities
            stats = self._aggregate_stats(history, prov_key)
            score = self._calculate_score(stats)
            scores.append(((prov, model), score))

            # Log shadow mode details
            logger.info(
                f"ShadowRanker: {prov} Score={score:.3f} "
                f"(Success={stats['success_rate']:.2f}, "
                f"Lat={stats['avg_latency']:.0f}ms, "
                f"Qual={stats['avg_quality']:.2f})"
            )

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return [item[0] for item in scores]

    def _aggregate_stats(self, history: List[MultimodalOutcome], provider: str) -> Dict[str, float]:
        """Calculate aggregate stats for a provider."""
        relevant = [h for h in history if h.provider == provider]
        count = len(relevant)

        if count == 0:
            # Cold start: Give a neutral baseline
            return {"success_rate": 0.8, "avg_quality": 0.7, "avg_latency": 2000.0, "avg_cost": 0.0}

        successes = [1 for h in relevant if h.success]
        success_rate = sum(successes) / count

        latencies = [h.latency_ms for h in relevant if h.success]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        qualities = [h.quality_score or 0.5 for h in relevant if h.success]
        avg_quality = sum(qualities) / len(qualities) if qualities else 0.5

        costs = [h.cost_cents for h in relevant]
        avg_cost = sum(costs) / count

        return {
            "success_rate": success_rate,
            "avg_quality": avg_quality,
            "avg_latency": avg_latency,
            "avg_cost": avg_cost,
        }

    def _calculate_score(self, stats: Dict[str, float]) -> float:
        """Apply scoring formula.

        Score = 0.4*Success + 0.3*Quality + 0.2*(1-NormLatency) + 0.1*(1-NormCost)
        """
        # Normalize latency (soft cap at 10s = 10000ms)
        norm_latency = min(stats["avg_latency"] / 10000.0, 1.0)

        # Normalize cost (soft cap at 10 cents)
        norm_cost = min(stats["avg_cost"] / 10.0, 1.0)

        score = (
            0.4 * stats["success_rate"]
            + 0.3 * stats["avg_quality"]
            + 0.2 * (1.0 - norm_latency)
            + 0.1 * (1.0 - norm_cost)
        )
        return score
