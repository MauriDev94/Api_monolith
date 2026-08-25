from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

# 1 MB: suficiente para cualquier payload JSON legítimo de esta API.
DEFAULT_MAX_BODY_BYTES = 1_000_000


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Rechaza requests con body excesivo (413) antes de parsearlo.

    Starlette/uvicorn no limitan el tamaño del body por defecto; sin esto, un payload
    enorme se cargaría en memoria antes de que Pydantic aplique sus límites — un DoS
    barato, especialmente en el free tier de Render.
    """

    def __init__(self, app: ASGIApp, max_body_bytes: int = DEFAULT_MAX_BODY_BYTES) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared = int(content_length)
            except ValueError:
                declared = 0
            if declared > self.max_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"message": "Request body too large"},
                )
        return await call_next(request)
