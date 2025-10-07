import secrets
from flask import jsonify, session

from python.helpers.api import (
    ApiHandler,
    Input,
    Output,
    Request,
)
from python.helpers import runtime


class GetCsrfToken(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        token = session["csrf_token"]
        runtime_id = runtime.get_runtime_id()
        response = jsonify(
            {
                "token": token,
                "runtime_id": runtime_id,
            }
        )
        secure = request.is_secure if hasattr(request, "is_secure") else False
        response.set_cookie(
            f"csrf_token_{runtime_id}",
            token,
            samesite="Strict",
            secure=secure,
            path="/",
        )
        return response
