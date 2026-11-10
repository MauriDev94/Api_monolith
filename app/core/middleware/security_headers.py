from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint

# Headers aplicados a TODAS las respuestas. X-XSS-Protection se omite a propósito:
# está deprecado y puede introducir vulnerabilidades en navegadores antiguos.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}

# CSP estricta para respuestas de API (JSON), incluido /openapi.json. Se aplica a toda
# respuesta que aún no traiga su propia CSP: /docs (Scalar) carga su bundle desde un CDN
# y define la suya (con hash del script inline) en app/core/docs/scalar_setup.py. Decidir
# por respuesta y no por ruta evita que un /docs deshabilitado (404) quede sin CSP.
_API_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


async def attach_security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Middleware que inyecta headers de seguridad en todas las respuestas."""
    response = await call_next(request)
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers[header_name] = header_value
    if "Content-Security-Policy" not in response.headers:
        response.headers["Content-Security-Policy"] = _API_CONTENT_SECURITY_POLICY
    return response
