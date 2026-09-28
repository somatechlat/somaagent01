"""Seam invariant: agent-side embedding dim is 768 everywhere.

MEM_EMBED_DIM == SOMABRAIN_EMBED_DIM == SOMA_VECTOR_DIM == 768 (ARCHITECTURE-INVARIANTS §2).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


class TestAgentDimDefaults:
    def test_settings_mem_embed_dim_default_768(self):
        src = _read("config/settings.py")
        assert re.search(r'MEM_EMBED_DIM\s*=\s*int\(os\.environ\.get\(\s*["\']MEM_EMBED_DIM["\']\s*,\s*["\']768["\']\s*\)\)', src)

    def test_gateway_settings_mem_embed_dim_default_768(self):
        src = _read("services/gateway/settings.py")
        assert re.search(r'MEM_EMBED_DIM\s*=\s*int\(os\.environ\.get\(\s*["\']MEM_EMBED_DIM["\']\s*,\s*["\']768["\']\s*\)\)', src)

    def test_unified_settings_vector_dim_default_768(self):
        src = _read("infra/aaas/unified_settings.py")
        assert re.search(r'SOMA_VECTOR_DIM\s*=\s*int\(os\.environ\.get\(\s*["\']SOMA_VECTOR_DIM["\']\s*,\s*["\']768["\']\s*\)\)', src)

    def test_aaas_env_uses_768(self):
        env = _read("infra/aaas/aaas/.env")
        assert "SOMA_VECTOR_DIM=1536" not in env
        assert re.search(r"^SOMA_VECTOR_DIM=768\s*$", env, re.M)

    def test_aaas_env_example_uses_768(self):
        env = _read("infra/aaas/aaas/.env.example")
        assert "1536" not in env.split("SFM_VECTOR_DIM")[-1][:20] if "SFM_VECTOR_DIM" in env else True
        assert re.search(r"^(SFM_VECTOR_DIM|SOMA_VECTOR_DIM)=768\s*$", env, re.M)

    def test_memory_contract_default_is_768(self):
        src = _read("services/common/memory_contract.py")
        assert "DEFAULT_MEM_EMBED_DIM = 768" in src


class TestEmbeddingCatalog:
    """Catalog dims are settings-driven — the agent settings layer owns the value."""

    def test_catalog_dims_come_from_settings_helper(self):
        src = _read("admin/embeddings/api.py")
        # No hardcoded dimension literals in the catalog — every entry reads config.
        literals = re.findall(r'"dimensions"\s*:\s*(\d+)', src)
        assert not literals, f"catalog hardcodes dimensions: {literals}"
        assert src.count('"dimensions": get_mem_embed_dim()') >= 5
        assert "from services.common.memory_contract import get_mem_embed_dim" in src

    def test_catalog_dims_match_configured_dim(self):
        from services.common.memory_contract import get_mem_embed_dim
        import importlib

        import admin.embeddings.api as api

        importlib.reload(api)  # re-stamp catalog with current settings
        configured = get_mem_embed_dim()
        assert configured == 768
        for model_id, info in api.EMBEDDING_MODELS.items():
            assert info["dimensions"] == configured, (
                f"{model_id} exposes dim {info['dimensions']} != configured {configured}"
            )
