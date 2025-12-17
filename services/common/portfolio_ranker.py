
"""Portfolio Ranker Service - The "Learning" Loop.

Scores and ranks multimodal providers based on historical execution outcomes (success rate, quality, cost).
Implements the Learning & Ranking logic from SRS Section 16.8.
"""

import logging
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome

logger = logging.getLogger(__name__)


@dataclass
class ProviderScore:
    """Score components for a provider."""
    provider: str
    model: str
    total_score: float
    success_rate: float
    avg_quality: float
    norm_cost: float
    sample_size: int


class PortfolioRanker:
    """Ranks multimodal providers based on historical performance.
    
    The ranker fetches recent outcomes from SomaBrain (via client) and calculates
    a weighted score for each provider/model combination using:
    Score = (Success * W_s) + (Quality * W_q) + (1 - CostNorm * W_c)
    """

    # Weights for scoring
    WEIGHT_SUCCESS = 0.5
    WEIGHT_QUALITY = 0.3
    WEIGHT_COST = 0.2
    
    # Min samples to be confident in ranking (cold start threshold)
    MIN_SAMPLES = 3

    def __init__(self, brain_client: SomaBrainClient) -> None:
        self.brain_client = brain_client

    def rank_providers(
        self,
        candidates: List[Tuple[str, str]], # [(provider, model), ...]
        step_type: str
    ) -> List[Tuple[str, str]]:
        """Rank a list of candidate (provider, model) tuples.
        
        Args:
            candidates: List of available (provider, model) tuples.
            step_type: The type of step being executed (e.g., 'generate_image').
            
        Returns:
            The candidates list sorted by rank (best first).
        """
        if not candidates:
            return []
            
        # Fetch history
        outcomes = self.brain_client.fetch_outcomes(step_type=step_type, limit=100)
        
        # If no history, return random shuffle specific to this request to load balance cold starts
        # (Or just return original order if preference is implied by order)
        if not outcomes:
            return list(candidates) # Keep original order as default preference

        # Aggregate stats
        stats = self._aggregate_stats(outcomes)
        
        # Calculate max cost for normalization
        max_cost = max((s["avg_cost"] for s in stats.values()), default=1.0)
        if max_cost == 0: max_cost = 1.0

        # Score candidates
        scored_candidates = []
        for provider, model in candidates:
            key = f"{provider}:{model}"
            stat = stats.get(key)
            
            if not stat or stat["count"] < self.MIN_SAMPLES:
                # Cold start / exploration boost
                # We give it a decent default score to ensure it gets tried
                score = 0.6 
                sample_size = 0
                success_rate = 0.0
                avg_quality = 0.0
                norm_cost = 0.0
            else:
                success_rate = stat["successes"] / stat["count"]
                
                # Quality: default to 0.5 (neutral) if null
                total_quality = stat["total_quality"]
                quality_count = stat["quality_count"]
                avg_quality = (total_quality / quality_count) if quality_count > 0 else 0.5
                
                avg_cost = stat["avg_cost"]
                norm_cost = min(avg_cost / max_cost, 1.0)
                
                # Score Formula
                score = (
                    (success_rate * self.WEIGHT_SUCCESS) +
                    (avg_quality * self.WEIGHT_QUALITY) +
                    ((1.0 - norm_cost) * self.WEIGHT_COST)
                )
                sample_size = stat["count"]

            scored_candidates.append({
                "candidate": (provider, model),
                "score": score,
                "details": {
                    "success": success_rate,
                    "quality": avg_quality,
                    "cost": norm_cost,
                    "samples": sample_size
                }
            })
            
        # Sort by score desc
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # Log decision (debug)
        if scored_candidates:
            top = scored_candidates[0]
            logger.info(
                "Portfolio Ranker selected %s/%s score=%.2f (samples=%d)",
                top["candidate"][0], top["candidate"][1], top["score"], top["details"]["samples"]
            )
            
        return [item["candidate"] for item in scored_candidates]

    def _aggregate_stats(self, outcomes: List[MultimodalOutcome]) -> Dict[str, Dict]:
        """Aggregate outcomes by provider:model key."""
        stats = {} # key -> {count, successes, total_quality, quality_count, total_cost}
        
        for o in outcomes:
            key = f"{o.provider}:{o.model}"
            if key not in stats:
                stats[key] = {
                    "count": 0,
                    "successes": 0,
                    "total_quality": 0.0,
                    "quality_count": 0,
                    "total_cost": 0.0,
                    "avg_cost": 0.0
                }
            
            s = stats[key]
            s["count"] += 1
            if o.success:
                s["successes"] += 1
            
            if o.quality_score is not None:
                s["total_quality"] += o.quality_score
                s["quality_count"] += 1
                
            s["total_cost"] += o.cost_cents
            s["avg_cost"] = s["total_cost"] / s["count"]
            
        return stats
