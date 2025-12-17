
import logging
from unittest.mock import MagicMock

import pytest

from services.common.portfolio_ranker import PortfolioRanker
from services.common.soma_brain_client import MultimodalOutcome

@pytest.fixture
def mock_brain_client():
    client = MagicMock()
    return client

@pytest.fixture
def ranker(mock_brain_client):
    return PortfolioRanker(mock_brain_client)

def test_rank_providers_cold_start(ranker, mock_brain_client):
    """Test ranking with no historical data (cold start)."""
    mock_brain_client.fetch_outcomes.return_value = []
    
    candidates = [("provider_a", "model_x"), ("provider_b", "model_y")]
    ranked = ranker.rank_providers(candidates, "generate_image")
    
    # Should maintain order or shuffle, but here we expect original order
    # based on implementation detail for stability
    assert ranked == candidates

def test_rank_providers_with_history(ranker, mock_brain_client):
    """Test ranking favors high performance providers."""
    # Data: A is awesome, B is terrible
    outcomes = []
    # Provider A: 10 successes, high quality, low cost
    for _ in range(10):
        outcomes.append(MultimodalOutcome(
            plan_id="p1", task_id="t1", step_type="generate_image",
            provider="provider_a", model="model_x",
            success=True, latency_ms=100, cost_cents=1.0, quality_score=0.9
        ))
    
    # Provider B: 10 failures or low quality
    for _ in range(10):
        outcomes.append(MultimodalOutcome(
            plan_id="p2", task_id="t2", step_type="generate_image",
            provider="provider_b", model="model_y",
            success=True, latency_ms=100, cost_cents=5.0, quality_score=0.1
        ))

    mock_brain_client.fetch_outcomes.return_value = outcomes
    
    candidates = [("provider_b", "model_y"), ("provider_a", "model_x")]
    ranked = ranker.rank_providers(candidates, "generate_image")
    
    # A should be ranked first despite input order
    assert ranked[0] == ("provider_a", "model_x")
    assert ranked[1] == ("provider_b", "model_y")

def test_rank_providers_cost_sensitive(ranker, mock_brain_client):
    """Test that significantly lower cost can influence rank if performance is similar."""
    outcomes = []
    # A: Success, Q=0.9, Cost=10.0
    for _ in range(5):
        outcomes.append(MultimodalOutcome(
            plan_id="p1", task_id="t1", step_type="generate_image",
            provider="provider_expensive", model="model_x",
            success=True, latency_ms=100, cost_cents=10.0, quality_score=0.9
        ))
        
    # B: Success, Q=0.85, Cost=0.1 (Way cheaper, slightly less quality)
    # Score A ~= 0.5*1 + 0.3*0.9 + 0.2*(1 - 10/10=0) = 0.5 + 0.27 + 0 = 0.77
    # Score B ~= 0.5*1 + 0.3*0.85 + 0.2*(1 - 0.1/10=0.99) = 0.5 + 0.255 + 0.198 = 0.953
    # B should win due to massive cost savings
    for _ in range(5):
        outcomes.append(MultimodalOutcome(
            plan_id="p2", task_id="t2", step_type="generate_image",
            provider="provider_cheap", model="model_y",
            success=True, latency_ms=100, cost_cents=0.1, quality_score=0.85
        ))
        
    mock_brain_client.fetch_outcomes.return_value = outcomes
    
    candidates = [("provider_expensive", "model_x"), ("provider_cheap", "model_y")]
    ranked = ranker.rank_providers(candidates, "generate_image")
    
    assert ranked[0] == ("provider_cheap", "model_y")
