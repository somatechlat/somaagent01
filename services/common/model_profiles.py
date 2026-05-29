"""Model Profiles — per-role deployment configuration store.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """A model profile maps a role + deployment mode to an LLM config."""

    role: str
    deployment_mode: str
    config: Dict[str, Any]


class ModelProfileStore(BaseStore[ModelProfile]):
    """Django ORM-backed store for model profiles."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    @classmethod
    def from_env(cls) -> "ModelProfileStore":
        """Create a store from the environment."""
        return cls()

    async def get(
        self, role: str, deployment_mode: str = "standard"
    ) -> Optional[ModelProfile]:
        """Get profile for role + deployment_mode."""
        from admin.core.models import ModelProfile as ModelProfileModel

        profile = await ModelProfileModel.objects.filter(
            role=role, deployment_mode=deployment_mode
        ).afirst()
        if not profile:
            return None
        return ModelProfile(
            role=profile.role,
            deployment_mode=profile.deployment_mode,
            config=profile.config,
        )

    async def list(self, role: Optional[str] = None) -> List[ModelProfile]:
        """List model profiles."""
        from admin.core.models import ModelProfile as ModelProfileModel

        qs = ModelProfileModel.objects.all()
        if role:
            qs = qs.filter(role=role)
        results = []
        async for profile in qs:
            results.append(
                ModelProfile(
                    role=profile.role,
                    deployment_mode=profile.deployment_mode,
                    config=profile.config,
                )
            )
        return results

    async def create(self, record: ModelProfile) -> ModelProfile:
        """Persist a model profile."""
        from admin.core.models import ModelProfile as ModelProfileModel

        obj, _ = await ModelProfileModel.objects.aupdate_or_create(
            role=record.role,
            deployment_mode=record.deployment_mode,
            defaults={"config": record.config},
        )
        return ModelProfile(
            role=obj.role,
            deployment_mode=obj.deployment_mode,
            config=obj.config,
        )

    async def update(
        self, identifier: str, changes: Dict[str, Any]
    ) -> Optional[ModelProfile]:
        """Update a model profile."""
        from admin.core.models import ModelProfile as ModelProfileModel

        profile = await ModelProfileModel.objects.filter(role=identifier).afirst()
        if not profile:
            return None
        if "config" in changes:
            profile.config = changes["config"]
        if "deployment_mode" in changes:
            profile.deployment_mode = changes["deployment_mode"]
        await profile.asave()
        return ModelProfile(
            role=profile.role,
            deployment_mode=profile.deployment_mode,
            config=profile.config,
        )

    async def delete(self, identifier: str) -> bool:
        """Remove a model profile."""
        from admin.core.models import ModelProfile as ModelProfileModel

        deleted, _ = await ModelProfileModel.objects.filter(role=identifier).adelete()
        return deleted > 0
