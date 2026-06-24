from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger
from pydantic import BaseModel, Field

from app.core.exceptions.error_handling import register_exception_handlers


class _SecretPayload(BaseModel):
    password: str = Field(min_length=20)


# Tipo de test: Integration
def test_validation_error_does_not_log_submitted_input() -> None:
    """S4: el handler de validación no debe loguear el `input` enviado (OWASP A09).

    Antes se logueaba `exc.errors()` crudo, que incluye el valor enviado (p.ej. una
    password) en texto plano.
    """
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/secret")
    def _endpoint(payload: _SecretPayload) -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)

    captured: list[str] = []
    sink_id = logger.add(captured.append, level="WARNING")
    try:
        response = client.post("/secret", json={"password": "leaky-secret-value"})
    finally:
        logger.remove(sink_id)

    assert response.status_code == 400
    assert "leaky-secret-value" not in "".join(captured)
