"""Mermaid diagram provider.

Generates diagrams using Mermaid CLI (mmdc) for SVG/PNG output.
Runs locally without external API calls.

SRS Reference: Section 16.6.1 (Diagram Providers)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from services.multimodal.base_provider import (
    GenerationRequest,
    GenerationResult,
    MultimodalProvider,
    ProviderCapability,
)

__all__ = ["MermaidProvider"]

logger = logging.getLogger(__name__)


class MermaidProvider(MultimodalProvider):
    """Provider for Mermaid diagram generation.

    Uses the Mermaid CLI (mmdc) to render diagrams from Mermaid
    syntax to SVG or PNG format. Runs locally with no API costs.

    Requirements:
        - Node.js installed
        - @mermaid-js/mermaid-cli installed globally or locally

    Usage:
        provider = MermaidProvider()
        result = await provider.generate(GenerationRequest(
            tenant_id="acme",
            session_id="s1",
            modality="diagram",
            prompt="graph TD\\n  A-->B",
            format="svg",
        ))
    """

    # Mermaid CLI executable name
    CLI_NAME = "mmdc"

    # Supported diagram types
    DIAGRAM_TYPES = [
        "flowchart",
        "graph",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "journey",
        "gantt",
        "pie",
        "requirementDiagram",
        "gitGraph",
        "c4Context",
        "mindmap",
        "timeline",
    ]

    def __init__(
        self,
        cli_path: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> None:
        """Initialize Mermaid provider.

        Args:
            cli_path: Path to mmdc executable. Auto-detected if None.
            timeout_seconds: Timeout for CLI execution.
        """
        self._cli_path = cli_path
        self._timeout = timeout_seconds
        self._cli_available: Optional[bool] = None

    @property
    def name(self) -> str:
        """Execute name.
            """

        return "mermaid_diagram"

    @property
    def provider_id(self) -> str:
        """Execute provider id.
            """

        return "local"

    @property
    def capabilities(self) -> List[ProviderCapability]:
        """Execute capabilities.
            """

        return [ProviderCapability.DIAGRAM]

    @property
    def supported_formats(self) -> List[str]:
        """Execute supported formats.
            """

        return ["svg", "png", "pdf"]

    @property
    def max_dimensions(self) -> Optional[Dict[str, int]]:
        """Execute max dimensions.
            """

        return {"width": 4096, "height": 4096}

    def _find_cli(self) -> Optional[str]:
        """Find the mmdc CLI executable."""
        if self._cli_path:
            return self._cli_path

        # Check common locations
        cli = shutil.which(self.CLI_NAME)
        if cli:
            return cli

        # Check npx
        npx = shutil.which("npx")
        if npx:
            return "npx -y @mermaid-js/mermaid-cli"

        return None

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a Mermaid diagram.

        Args:
            request: Generation request with Mermaid code in prompt

        Returns:
            GenerationResult with SVG/PNG content
        """
        import time

        start_time = time.time()

        # Validate first
        errors = self.validate(request)
        if errors:
            return GenerationResult(
                success=False,
                error_code="VALIDATION_ERROR",
                error_message="; ".join(errors),
                provider=self.provider_id,
            )

        cli = self._find_cli()
        if not cli:
            return GenerationResult(
                success=False,
                error_code="CLI_NOT_FOUND",
                error_message="Mermaid CLI (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli",
                provider=self.provider_id,
            )

        output_format = request.format or "svg"

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                input_file = Path(tmpdir) / "diagram.mmd"
                output_file = Path(tmpdir) / f"diagram.{output_format}"

                # Write Mermaid code to input file
                input_file.write_text(request.prompt)

                # Build command
                if cli.startswith("npx"):
                    cmd_parts = cli.split() + ["-i", str(input_file), "-o", str(output_file)]
                else:
                    cmd_parts = [cli, "-i", str(input_file), "-o", str(output_file)]

                # Add dimension options if specified
                if request.dimensions:
                    if "width" in request.dimensions:
                        cmd_parts.extend(["-w", str(request.dimensions["width"])])
                    if "height" in request.dimensions:
                        cmd_parts.extend(["-H", str(request.dimensions["height"])])

                # Execute CLI
                logger.info("Executing Mermaid CLI: %s", " ".join(cmd_parts))
                process = await asyncio.create_subprocess_exec(
                    *cmd_parts,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self._timeout,
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    return GenerationResult(
                        success=False,
                        error_code="TIMEOUT",
                        error_message=f"Mermaid CLI timed out after {self._timeout}s",
                        provider=self.provider_id,
                    )

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error("Mermaid CLI failed: %s", error_msg)
                    return GenerationResult(
                        success=False,
                        error_code="CLI_ERROR",
                        error_message=f"Mermaid CLI failed: {error_msg}",
                        provider=self.provider_id,
                    )

                # Read output
                if not output_file.exists():
                    return GenerationResult(
                        success=False,
                        error_code="OUTPUT_MISSING",
                        error_message="Mermaid CLI did not produce output file",
                        provider=self.provider_id,
                    )

                content = output_file.read_bytes()
                latency_ms = int((time.time() - start_time) * 1000)

                # Determine content type
                content_type = {
                    "svg": "image/svg+xml",
                    "png": "image/png",
                    "pdf": "application/pdf",
                }.get(output_format, "application/octet-stream")

                logger.info("Generated Mermaid diagram: %d bytes in %dms", len(content), latency_ms)

                return GenerationResult(
                    success=True,
                    content=content,
                    content_type=content_type,
                    format=output_format,
                    latency_ms=latency_ms,
                    cost_cents=0,  # Local execution is free
                    provider=self.provider_id,
                    model_version=await self._get_version(),
                    quality_hints={"diagram_type": self._detect_diagram_type(request.prompt)},
                )

        except Exception as exc:
            logger.exception("Mermaid generation failed: %s", exc)
            return GenerationResult(
                success=False,
                error_code="INTERNAL_ERROR",
                error_message=str(exc),
                provider=self.provider_id,
            )

    def validate(self, request: GenerationRequest) -> List[str]:
        """Validate Mermaid generation request."""
        errors: List[str] = []

        if not request.prompt:
            errors.append("Mermaid code is required in prompt")
            return errors

        # Check for diagram type keyword
        if not any(
            dt in request.prompt.lower()
            for dt in [
                "graph",
                "flowchart",
                "sequence",
                "class",
                "state",
                "er",
                "journey",
                "gantt",
                "pie",
                "requirement",
                "git",
                "c4",
                "mindmap",
                "timeline",
            ]
        ):
            # Not a hard error, but worth noting
            logger.debug("No recognized diagram type keyword in Mermaid code")

        # Validate format
        if request.format and request.format not in self.supported_formats:
            errors.append(
                f"Unsupported format: {request.format}. Supported: {self.supported_formats}"
            )

        # Validate dimensions
        max_dims = self.max_dimensions
        if request.dimensions and max_dims:
            if request.dimensions.get("width", 0) > max_dims["width"]:
                errors.append(f"Width exceeds maximum: {max_dims['width']}")
            if request.dimensions.get("height", 0) > max_dims["height"]:
                errors.append(f"Height exceeds maximum: {max_dims['height']}")

        return errors

    def estimate_cost(self, request: GenerationRequest) -> int:
        """Estimate cost for Mermaid diagram (always free)."""
        return 0

    async def health_check(self) -> bool:
        """Check if Mermaid CLI is available."""
        if self._cli_available is not None:
            return self._cli_available

        cli = self._find_cli()
        if not cli:
            self._cli_available = False
            return False

        try:
            if cli.startswith("npx"):
                cmd_parts = cli.split() + ["--version"]
            else:
                cmd_parts = [cli, "--version"]

            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.communicate(), timeout=10)
            self._cli_available = process.returncode == 0
            return self._cli_available
        except Exception:
            self._cli_available = False
            return False

    async def _get_version(self) -> Optional[str]:
        """Get Mermaid CLI version."""
        cli = self._find_cli()
        if not cli:
            return None

        try:
            if cli.startswith("npx"):
                cmd_parts = cli.split() + ["--version"]
            else:
                cmd_parts = [cli, "--version"]

            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=5)
            if process.returncode == 0:
                return stdout.decode().strip()
        except Exception:
            # Ignore version check failures
            return None

    def _detect_diagram_type(self, code: str) -> str:
        """Detect the type of Mermaid diagram from code."""
        code_lower = code.lower().strip()

        type_keywords = [
            ("flowchart", "flowchart"),
            ("graph", "flowchart"),
            ("sequencediagram", "sequence"),
            ("classdiagram", "class"),
            ("statediagram", "state"),
            ("erdiagram", "er"),
            ("journey", "journey"),
            ("gantt", "gantt"),
            ("pie", "pie"),
            ("requirementdiagram", "requirement"),
            ("gitgraph", "git"),
            ("c4context", "c4"),
            ("mindmap", "mindmap"),
            ("timeline", "timeline"),
        ]

        for keyword, dtype in type_keywords:
            if code_lower.startswith(keyword):
                return dtype

        return "unknown"

    def get_model_version(self) -> Optional[str]:
        """Get cached model version."""
        return None  # Version retrieved dynamically