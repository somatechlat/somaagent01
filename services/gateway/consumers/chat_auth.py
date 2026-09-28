"""Authentication helpers for the WebSocket chat consumer."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs

from admin.common.auth import decode_token
from admin.common.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)


class ChatAuthMixin:
    """Authentication mixin for ChatConsumer."""

    async def _authenticate(self) -> bool:
        """Authenticate user from JWT subprotocol or cookie.

        Per design.md Section 7.1 & P3-04:
        - Extract JWT from Sec-WebSocket-Protocol subprotocol (preferred)
        - Fallback to query string, Authorization header, cookie
        - Validate token
        - Extract user context
        """

        # Token sources: subprotocol (P3-04), query string, Authorization header, cookie
        token = None
        cookies = {}

        # 1. Subprotocol auth (P3-04 preferred)
        for proto in self.scope.get("subprotocols", []):
            if proto.startswith("soma-auth."):
                token = proto[len("soma-auth.") :]
                break

        # 2. Query string fallback
        if not token:
            query_string = self.scope.get("query_string", b"").decode("utf-8")
            if query_string:
                params = parse_qs(query_string)
                token_list = params.get("token")
                if token_list:
                    token = token_list[0]

        # 3. Authorization header fallback
        if not token:
            for header_name, header_value in self.scope.get("headers", []):
                if header_name == b"authorization":
                    auth_value = header_value.decode("utf-8")
                    if auth_value.lower().startswith("bearer "):
                        token = auth_value[7:].strip()
                        break

        # Parse cookies regardless (needed for session_id)
        for header_name, header_value in self.scope.get("headers", []):
            if header_name == b"cookie":
                cookie_str = header_value.decode("utf-8")
                for cookie in cookie_str.split(";"):
                    if "=" in cookie:
                        key, value = cookie.strip().split("=", 1)
                        cookies[key] = value
                break

        # 4. Cookie fallback
        if not token:
            token = cookies.get("access_token")

        if not token:
            logger.warning("WebSocket auth failed: No access token provided")
            return False

        try:
            # Decode and validate JWT
            payload = await decode_token(token)

            self.user_id = payload.sub
            self.tenant_id = payload.tenant_id
            self.session_id = cookies.get("session_id")

            logger.debug("WebSocket authenticated: user=%s", self.user_id)
            return True

        except UnauthorizedError as e:
            logger.warning("WebSocket auth failed: %s", e)
            return False
        except Exception:
            logger.exception("WebSocket auth failed: unexpected exception")
            return False
