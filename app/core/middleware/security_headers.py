from fastapi import Request

# Headers aplicados a TODAS las respuestas. X-XSS-Protection se omite a propósito:
# está deprecado y puede introducir vulnerabilidades en navegadores antiguos.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}

# CSP estricta para respuestas de API (JSON). Se omite en las páginas de docs
# (Swagger/ReDoc) porque cargan JS/CSS desde un CDN y una CSP 'none' las rompería.
_API_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}


async def attach_security_headers(request: Request, call_next):
    """Middleware que inyecta headers de seguridad en todas las respuestas."""
    response = await call_next(request)
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers[header_name] = header_value
    if request.url.path not in _DOCS_PATHS:
        response.headers["Content-Security-Policy"] = _API_CONTENT_SECURITY_POLICY
    return response
