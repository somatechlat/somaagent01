"""Message preprocessing for conversation worker.

This module extracts the ConversationPreprocessor and AnalysisResult
from main.py to reduce file size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class AnalysisResult:
    """Result of message analysis."""

    intent: str
    sentiment: str
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Execute to dict.
            """

        return {
            "intent": self.intent,
            "sentiment": self.sentiment,
            "tags": self.tags,
        }


class ConversationPreprocessor:
    """Preprocess conversation messages for analysis."""

    def analyze(self, message: str) -> AnalysisResult:
        """Analyze a message for intent, sentiment, and tags.

        Args:
            message: The message text to analyze

        Returns:
            AnalysisResult with intent, sentiment, and tags
        """
        text = message.strip()
        lower = text.lower()

        # Determine intent
        if not text:
            intent = "empty"
        elif lower.startswith(("how", "what", "why", "when", "where", "who")) or text.endswith("?"):
            intent = "question"
        elif any(keyword in lower for keyword in ["create", "build", "implement", "write"]):
            intent = "action_request"
        elif any(keyword in lower for keyword in ["fix", "bug", "issue", "error"]):
            intent = "problem_report"
        else:
            intent = "statement"

        # Extract tags
        tags: List[str] = []
        if any(word in lower for word in ["code", "python", "function", "class"]):
            tags.append("code")
        if any(word in lower for word in ["deploy", "docker", "kubernetes", "infra"]):
            tags.append("infrastructure")
        if any(word in lower for word in ["test", "validate", "qa"]):
            tags.append("testing")

        # Determine sentiment
        negatives = {"fail", "broken", "crash", "error", "issue"}
        positives = {"great", "thanks", "awesome", "good"}
        sentiment = "neutral"
        if any(word in lower for word in negatives):
            sentiment = "negative"
        elif any(word in lower for word in positives):
            sentiment = "positive"

        return AnalysisResult(intent=intent, sentiment=sentiment, tags=tags)