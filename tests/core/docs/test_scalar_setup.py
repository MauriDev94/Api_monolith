import base64
import hashlib
import re
from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from httpx import Response
from loguru import logger

from app.core.docs import scalar_setup
from app.core.docs.scalar_setup import setup_scalar_docs

_VALID_PAGE = (
    "<html><body>"
    f'<script src="{scalar_setup._SCALAR_JS_URL}"></script>'
    "<script>Scalar.createApiReference('#app', {})</script>"
    "</body></html>"
)


def _app() -> FastAPI:
    return FastAPI(docs_url=None, redoc_url=None)


def _docs_response(monkeypatch: pytest.MonkeyPatch) -> Response:
    monkeypatch.setenv("SCALAR_DOCS_ENABLED", "true")
    app = _app()
    assert setup_scalar_docs(app, title="Test API") is True
    return TestClient(app).get("/docs")


@pytest.fixture
def error_logs() -> Iterator[list[str]]:
    """Captura mensajes de loguru (caplog no los ve por defecto)."""
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(str(m)), level="ERROR")
    yield messages
    logger.remove(sink_id)


# Tipo de test: Unit
def test_docs_script_tag_has_pinned_url_and_sri_when_docs_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """/docs carga el bundle fijado con integrity y crossorigin anonymous."""
    response = _docs_response(monkeypatch)

    assert response.status_code == 200
    expected = (
        f'<script src="{scalar_setup._SCALAR_JS_URL}" '
        f'integrity="{scalar_setup._SCALAR_JS_INTEGRITY}" crossorigin="anonymous"></script>'
    )
    assert expected in response.text


# Tipo de test: Unit
def test_docs_html_has_no_proxy_nor_persisted_auth_when_docs_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """/docs no usa proxy de terceros ni persiste el token en localStorage."""
    html = _docs_response(monkeypatch).text

    assert "Scalar.createApiReference" in html
    assert "proxyUrl" not in html
    assert "proxy.scalar.com" not in html
    assert "persistAuth" not in html


# Tipo de test: Unit
def test_docs_html_disables_agent_developer_tools_and_telemetry_when_docs_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La config emitida apaga Agent Scalar, developer tools y telemetría."""
    html = _docs_response(monkeypatch).text

    assert '"agent": {"disabled": true}' in html
    assert '"showDeveloperTools": "never"' in html
    assert '"telemetry": false' in html


# Tipo de test: Unit
def test_docs_csp_pins_bundle_and_has_no_unsafe_sources_when_docs_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """/docs lleva su CSP con el bundle fijado y un hash sha256, sin unsafe-eval ni strict-dynamic."""
    csp = _docs_response(monkeypatch).headers["Content-Security-Policy"]

    assert scalar_setup._SCALAR_JS_URL in csp
    assert "'sha256-" in csp
    assert "unsafe-eval" not in csp
    assert "strict-dynamic" not in csp
    assert "connect-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


# Tipo de test: Unit
def test_docs_csp_hash_matches_inline_script_when_docs_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El hash de la CSP corresponde al script inline realmente servido."""
    response = _docs_response(monkeypatch)

    inline = re.findall(r"<script>(.*?)</script>", response.text, re.DOTALL)
    assert len(inline) == 1
    digest = base64.b64encode(hashlib.sha256(inline[0].encode("utf-8")).digest()).decode()
    assert f"'sha256-{digest}'" in response.headers["Content-Security-Policy"]


# Tipo de test: Unit
def test_docs_route_not_registered_when_docs_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Con SCALAR_DOCS_ENABLED=false no se registra /docs."""
    monkeypatch.setenv("SCALAR_DOCS_ENABLED", "false")
    app = _app()

    registered = setup_scalar_docs(app, title="Test API")

    assert registered is False
    assert TestClient(app).get("/docs").status_code == 404


_BAD_PAGES: dict[str, str] = {
    "missing_pinned_tag": "<html><script src='other.js'></script><script>Scalar.createApiReference()</script></html>",
    "extra_external_script": _VALID_PAGE.replace(
        "</body>", '<script src="https://evil.example/x.js"></script></body>'
    ),
    "no_inline_init": f'<html><script src="{scalar_setup._SCALAR_JS_URL}"></script></html>',
    "extra_module_script": _VALID_PAGE.replace(
        "</body>", '<script type="module">alert(1)</script></body>'
    ),
    "extra_uppercase_script": _VALID_PAGE.replace("</body>", "<SCRIPT>alert(1)</SCRIPT></body>"),
    "extra_inline_script": _VALID_PAGE.replace("</body>", "<script>alert(1)</script></body>"),
}


# Tipo de test: Unit
@pytest.mark.parametrize("page", list(_BAD_PAGES.values()), ids=list(_BAD_PAGES))
def test_docs_not_registered_and_error_logged_when_template_is_unexpected(
    monkeypatch: pytest.MonkeyPatch, error_logs: list[str], page: str
) -> None:
    """Si la plantilla cambia, /docs no se registra, se loguea el error y la API sigue arriba."""
    monkeypatch.setenv("SCALAR_DOCS_ENABLED", "true")
    fake: Callable[..., HTMLResponse] = lambda **_: HTMLResponse(page)  # noqa: E731
    monkeypatch.setattr(scalar_setup, "get_scalar_api_reference", fake)
    app = _app()

    registered = setup_scalar_docs(app, title="Test API")

    assert registered is False
    assert TestClient(app).get("/docs").status_code == 404
    assert any("Scalar docs not registered" in m for m in error_logs)
