"""Request ID middleware.

Assigns a unique ID to every request for tracing across logs.
Accepts an incoming X-Request-ID header if provided by the client.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID to every request."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        clear_contextvars()

        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        # Make request_id available throughout the request lifecycle
        request.state.request_id = request_id
        bind_contextvars(request_id=request_id)

        response = await call_next(request)

        # Echo the request ID back in the response header
        response.headers["X-Request-ID"] = request_id

        return response
