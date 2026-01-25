"""Module seed_aaas."""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from admin.aaas.models.choices import (
    FeatureCategory,
)
from admin.aaas.models.features import FeatureProvider, AaasFeature, TierFeature
from admin.aaas.models.tiers import SubscriptionTier

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command class implementation."""

    help = "Seeds the AAAS Admin database with default Tiers, Features, and Providers."

    def handle(self, *args, **options):
        """Execute handle."""

        self.stdout.write(self.style.SUCCESS("Starting AAAS Admin seeding..."))

        try:
            with transaction.atomic():
                self.seed_features()
                self.seed_providers()
                self.seed_tiers()
                self.assign_features_to_tiers()

            self.stdout.write(self.style.SUCCESS("Successfully seeded AAAS Admin database."))
        except Exception as e:
            logger.exception("Seeding failed")
            self.stdout.write(self.style.ERROR(f"Seeding failed: {str(e)}"))

    def seed_features(self):
        """Create core platform features."""
        self.stdout.write("  Creating Features...")
        features_data = [
            {
                "code": "voice",
                "name": "Voice Interaction",
                "category": FeatureCategory.VOICE,
                "icon": "mic",
                "description": "Real-time voice conversation capabilities",
            },
            {
                "code": "memory",
                "name": "Long-term Memory",
                "category": FeatureCategory.MEMORY,
                "icon": "memory",
                "description": "Vector-based semantic memory storage",
            },
            {
                "code": "mcp",
                "name": "MCP Server Integration",
                "category": FeatureCategory.MCP,
                "icon": "hub",
                "description": "Connect to external Model Context Protocol servers",
            },
            {
                "code": "vision",
                "name": "Computer Vision",
                "category": FeatureCategory.VISION,
                "icon": "visibility",
                "description": "Image analysis and screen understanding",
            },
            {
                "code": "tools",
                "name": "Custom Tools",
                "category": FeatureCategory.TOOLS,
                "icon": "build",
                "description": "Define custom Python/Bash tools for agents",
            },
        ]

        for data in features_data:
            AaasFeature.objects.get_or_create(code=data["code"], defaults=data)

    def seed_providers(self):
        """Create feature providers."""
        self.stdout.write("  Creating Feature Providers...")

        voice = AaasFeature.objects.get(code="voice")
        FeatureProvider.objects.get_or_create(
            feature=voice,
            code="elevenlabs",
            defaults={"name": "ElevenLabs", "is_default": True},
        )
        FeatureProvider.objects.get_or_create(
            feature=voice,
            code="openai_tts",
            defaults={"name": "OpenAI TTS", "is_default": False},
        )

        memory = AaasFeature.objects.get(code="memory")
        FeatureProvider.objects.get_or_create(
            feature=memory,
            code="milvus",
            defaults={"name": "Milvus Vector DB", "is_default": True},
        )

    def seed_tiers(self):
        """Create subscription tiers."""
        self.stdout.write("  Creating Subscription Tiers...")
        tiers_data = [
            {
                "name": "Free",
                "slug": "free",
                "base_price_cents": 0,
                "description": "For hobbyists and testing.",
                "max_agents": 1,
            },
            {
                "name": "Starter",
                "slug": "starter",
                "base_price_cents": 2900,
                "description": "For individuals and small pros.",
                "max_agents": 3,
            },
            {
                "name": "Team",
                "slug": "team",
                "base_price_cents": 9900,
                "description": "For small teams and startups.",
                "max_agents": 10,
            },
        ]

        for data in tiers_data:
            SubscriptionTier.objects.get_or_create(slug=data["slug"], defaults=data)

    def assign_features_to_tiers(self):
        """Link features to tiers."""
        self.stdout.write("  Assigning Features to Tiers...")

        free_tier = SubscriptionTier.objects.get(slug="free")
        starter_tier = SubscriptionTier.objects.get(slug="starter")

        voice = AaasFeature.objects.get(code="voice")
        memory = AaasFeature.objects.get(code="memory")

        # Free Tier: Basic Voice, Limited Memory
        TierFeature.objects.get_or_create(
            tier=free_tier,
            feature=voice,
            defaults={"is_enabled": True, "quota_limit": 10},
        )
        TierFeature.objects.get_or_create(
            tier=free_tier,
            feature=memory,
            defaults={"is_enabled": False},  # Disabled on Free
        )

        # Starter Tier: Enhanced Voice, Enabled Memory
        TierFeature.objects.get_or_create(
            tier=starter_tier,
            feature=voice,
            defaults={"is_enabled": True, "quota_limit": 100},
        )
        TierFeature.objects.get_or_create(
            tier=starter_tier,
            feature=memory,
            defaults={"is_enabled": True, "quota_limit": 500},
        )
