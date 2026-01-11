"""Playwright screenshot provider.

Captures screenshots of web pages using Playwright browser automation.
Runs locally with configurable browser and viewport options.

SRS Reference: Section 16.6.1 (Screenshot Providers)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from services.multimodal.base_provider import (
    GenerationRequest,
    GenerationResult,
    MultimodalProvider,
    ProviderCapability,
    ProviderError,
)

__all__ = ["PlaywrightProvider"]

logger = logging.getLogger(__name__)


class PlaywrightProvider(MultimodalProvider):
    """Provider for Playwright screenshot capture.

    Uses Playwright to capture full-page or viewport screenshots
    of web pages in PNG or JPEG format.

    Requirements:
        - playwright package installed
        - Browser binaries installed (playwright install)

    Usage:
        provider = PlaywrightProvider()
        result = await provider.generate(GenerationRequest(
            tenant_id="acme",
            session_id="s1",
            modality="screenshot",
            prompt="https://example.com",
            parameters={"full_page": True, "viewport": {"width": 1280, "height": 720}},
        ))
    """

    # Default viewport size
    DEFAULT_VIEWPORT = {"width": 1280, "height": 720}

    # Maximum viewport dimensions
    MAX_VIEWPORT = {"width": 3840, "height": 2160}

    # Supported browsers
    BROWSERS = ["chromium", "firefox", "webkit"]

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        timeout_ms: int = 30000,
    ) -> None:
        """Initialize Playwright provider.

        Args:
            browser_type: Browser to use (chromium, firefox, webkit).
            headless: Run browser in headless mode.
            timeout_ms: Page load timeout in milliseconds.
        """
        self._browser_type = browser_type
        self._headless = headless
        self._timeout_ms = timeout_ms
        self._playwright = None
        self._browser = None

    @property
    def name(self) -> str:
        """Execute name."""

        return "playwright_screenshot"

    @property
    def provider_id(self) -> str:
        """Execute provider id."""

        return "local"

    @property
    def capabilities(self) -> List[ProviderCapability]:
        """Execute capabilities."""

        return [ProviderCapability.SCREENSHOT]

    @property
    def supported_formats(self) -> List[str]:
        """Execute supported formats."""

        return ["png", "jpeg"]

    @property
    def max_dimensions(self) -> Optional[Dict[str, int]]:
        """Execute max dimensions."""

        return self.MAX_VIEWPORT

    async def _ensure_browser(self):
        """Ensure browser is started."""
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                raise ProviderError(
                    "Playwright not installed. Install with: pip install playwright && playwright install",
                    self.provider_id,
                    error_code="DEPENDENCY_MISSING",
                )

            self._playwright = await async_playwright().start()

            if self._browser_type == "chromium":
                self._browser = await self._playwright.chromium.launch(headless=self._headless)
            elif self._browser_type == "firefox":
                self._browser = await self._playwright.firefox.launch(headless=self._headless)
            elif self._browser_type == "webkit":
                self._browser = await self._playwright.webkit.launch(headless=self._headless)
            else:
                self._browser = await self._playwright.chromium.launch(headless=self._headless)

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Capture a screenshot of a web page.

        Args:
            request: Generation request with URL in prompt

        Returns:
            GenerationResult with screenshot image data
        """
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

        url = request.prompt.strip()
        output_format = request.format or "png"
        full_page = request.parameters.get("full_page", False)
        viewport = request.parameters.get("viewport", self.DEFAULT_VIEWPORT)
        wait_for = request.parameters.get("wait_for", "networkidle")

        page = None
        try:
            await self._ensure_browser()

            # Create new context with viewport
            context = await self._browser.new_context(
                viewport=viewport,
                device_scale_factor=request.parameters.get("device_scale_factor", 1),
            )

            page = await context.new_page()

            # Navigate to URL
            logger.info("Navigating to: %s", url)
            await page.goto(url, wait_until=wait_for, timeout=self._timeout_ms)

            # Wait for additional selector if specified
            wait_selector = request.parameters.get("wait_for_selector")
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=self._timeout_ms // 2)

            # Capture screenshot
            screenshot_options = {
                "type": output_format,
                "full_page": full_page,
            }

            if output_format == "jpeg":
                screenshot_options["quality"] = request.parameters.get("quality", 80)

            content = await page.screenshot(**screenshot_options)

            latency_ms = int((time.time() - start_time) * 1000)

            # Get actual page dimensions
            dimensions = viewport.copy()
            if full_page:
                dimensions = await page.evaluate(
                    """
                    () => ({
                        width: document.documentElement.scrollWidth,
                        height: document.documentElement.scrollHeight
                    })
                """
                )

            content_type = f"image/{output_format}"

            logger.info(
                "Captured screenshot: %d bytes, %dx%d, %dms",
                len(content),
                dimensions["width"],
                dimensions["height"],
                latency_ms,
            )

            return GenerationResult(
                success=True,
                content=content,
                content_type=content_type,
                format=output_format,
                dimensions=dimensions,
                latency_ms=latency_ms,
                cost_cents=0,  # Local execution is free
                provider=self.provider_id,
                model_version=f"playwright-{self._browser_type}",
                quality_hints={"url": url, "full_page": full_page},
            )

        except Exception as exc:
            error_msg = str(exc)
            error_code = "INTERNAL_ERROR"

            if "Timeout" in error_msg:
                error_code = "TIMEOUT"
            elif "net::ERR" in error_msg:
                error_code = "NETWORK_ERROR"
            elif "Navigation" in error_msg:
                error_code = "NAVIGATION_ERROR"

            logger.exception("Screenshot capture failed: %s", exc)
            return GenerationResult(
                success=False,
                error_code=error_code,
                error_message=error_msg,
                provider=self.provider_id,
            )
        finally:
            if page:
                await page.close()

    def validate(self, request: GenerationRequest) -> List[str]:
        """Validate screenshot request."""
        errors: List[str] = []

        if not request.prompt:
            errors.append("URL is required in prompt")
            return errors

        url = request.prompt.strip()

        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")

        # Validate format
        if request.format and request.format not in self.supported_formats:
            errors.append(
                f"Unsupported format: {request.format}. Supported: {self.supported_formats}"
            )

        # Validate viewport dimensions
        viewport = request.parameters.get("viewport", {})
        max_dims = self.max_dimensions
        if max_dims:
            if viewport.get("width", 0) > max_dims["width"]:
                errors.append(f"Viewport width exceeds maximum: {max_dims['width']}")
            if viewport.get("height", 0) > max_dims["height"]:
                errors.append(f"Viewport height exceeds maximum: {max_dims['height']}")

        return errors

    def estimate_cost(self, request: GenerationRequest) -> int:
        """Estimate cost for screenshot (always free)."""
        return 0

    async def health_check(self) -> bool:
        """Check if Playwright is available."""
        try:
            from playwright.async_api import async_playwright

            return True
        except ImportError:
            return False

    def get_model_version(self) -> Optional[str]:
        """Get browser type as version."""
        return f"playwright-{self._browser_type}"

    async def close(self) -> None:
        """Close browser and Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
