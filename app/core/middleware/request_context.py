from uuid import uuid4

from fastapi import Request
from fastapi.responses import Response
from loguru import logger
from starlette.middleware.base import RequestResponseEndpoint


async def attach_request_id_middleware(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """Attach and propagate request id for tracing across logs and responses."""
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id

    request_logger = logger.bind(request_id=request_id)
    request_logger.info(f"Incoming request {request.method} {request.url.path}")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    request_logger.info(
        f"Completed request {request.method} {request.url.path} with status {response.status_code}"
    )
    return response
