from unittest.mock import patch

from fastapi.testclient import TestClient


def test_should_return_health_status_when_root_is_called():
    """Verifica que el endpoint raíz devuelve el status correcto."""
    with patch("app.main.setup_logger"):
        with patch("app.main.register_exception_handlers"):
            from app.main import app

            client = TestClient(app)
            response = client.get("/")

            assert response.status_code == 200
            assert response.json() == {"status": "success", "message": "API is running"}


def test_should_return_openapi_schema_with_bearer_auth():
    """Verifica que custom_openapi agrega BearerAuth scheme."""
    with patch("app.main.setup_logger"):
        with patch("app.main.register_exception_handlers"):
            from app.main import app

            # Force openapi generation
            schema = app.openapi()

            assert schema is not None
            assert "components" in schema
            assert "securitySchemes" in schema["components"]
            assert "BearerAuth" in schema["components"]["securitySchemes"]
            assert schema["components"]["securitySchemes"]["BearerAuth"]["type"] == "http"
            assert schema["components"]["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"


def test_should_apply_bearer_auth_to_all_paths():
    """Verifica que BearerAuth se aplica a todas las paths sin security."""
    with patch("app.main.setup_logger"):
        with patch("app.main.register_exception_handlers"):
            from app.main import app

            schema = app.openapi()

            # Check that auth endpoints have BearerAuth
            paths = schema.get("paths", {})
            for path, methods in paths.items():
                for method, operation in methods.items():
                    if isinstance(operation, dict):
                        security = operation.get("security", [])
                        has_bearer = any("BearerAuth" in s for s in security)
                        assert has_bearer is True, f"Path {path} {method} missing BearerAuth"


def test_should_cache_openapi_schema():
    """Verifica que el schema se cachea correctamente."""
    with patch("app.main.setup_logger"):
        with patch("app.main.register_exception_handlers"):
            from app.main import app

            # Call twice
            schema1 = app.openapi()
            schema2 = app.openapi()

            assert schema1 is schema2


def test_should_include_all_routers():
    """Verifica que todos los routers están incluidos."""
    with patch("app.main.setup_logger"):
        with patch("app.main.register_exception_handlers"):
            from app.main import app

            routes = [route.path for route in app.routes]

            assert any("/auth" in r for r in routes)
            assert any("/users" in r for r in routes)
            assert any("/todos" in r for r in routes)
            assert "/" in routes
