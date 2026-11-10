from collections.abc import Iterable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_FETCH_METADATA_PREFIX = "sec-fetch-"


class OriginCheckMiddleware(BaseHTTPMiddleware):
    """Rechaza (403) requests de escritura que no provienen de un origen de confianza.

    En producción la cookie de refresh es `SameSite=None; Secure` (Vercel <-> Render son
    cross-site), así que cualquier página de terceros puede enviar un POST "simple" sin
    preflight CORS y el navegador adjunta la cookie (login CSRF, logout forzado, disparar
    la detección de reuso de /refresh). Esta defensa valida el origen del request.

    Aplica a todo método que no sea seguro (POST, PUT, PATCH, DELETE y cualquier otro), en
    todas las rutas; solo GET, HEAD y OPTIONS (incluido el preflight CORS) pasan sin tocar.
    Reglas, en orden:

    1. `Sec-Fetch-Site: same-origin` -> permitir (los navegadores lo fijan y las páginas
       no pueden falsificar headers `Sec-*`).
    2. Si hay `Origin` -> permitir solo si coincide exactamente con la lista permitida
       (`Origin: null` se rechaza).
    3. Sin `Origin` pero con algún header `Sec-Fetch-*` -> rechazar (navegador que omitió
       `Origin`).
    4. En otro caso -> permitir (cliente no-navegador: curl, mobile, tests).

    El rechazo ocurre antes del ruteo: ningún endpoint corre ni emite `Set-Cookie`.
    """

    def __init__(self, app: ASGIApp, allowed_origins: Iterable[str]) -> None:
        super().__init__(app)
        self.allowed_origins = frozenset(allowed_origins)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Fail closed: only the explicit safe methods skip the check; anything else
        # (including odd or lowercase methods) goes through the rules below.
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        sec_fetch_site = request.headers.get("sec-fetch-site")
        if sec_fetch_site is not None and sec_fetch_site.strip().lower() == "same-origin":
            return await call_next(request)

        origins = request.headers.getlist("origin")
        if len(origins) > 1:
            # Fail closed: duplicate Origin headers are never legitimate.
            return self._reject(request, f"multiple Origin headers ({len(origins)})")
        if origins:
            origin = origins[0]
            if origin in self.allowed_origins:
                return await call_next(request)
            # Truncate + repr: the value is attacker-controlled (log injection, huge values).
            return self._reject(request, f"origin={origin[:200]!r}")

        if any(name.lower().startswith(_FETCH_METADATA_PREFIX) for name in request.headers):
            return self._reject(
                request, f"sec-fetch-site={(sec_fetch_site or '')[:200]!r} (no Origin header)"
            )

        return await call_next(request)

    @staticmethod
    def _reject(request: Request, detail: str) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        logger.bind(request_id=request_id).warning(
            f"Origin check rejected {request.method!r} {request.url.path!r}: {detail}"
        )
        return JSONResponse(
            status_code=403,
            content={"message": "Forbidden: origin not allowed"},
        )
