from starlette.requests import Request

from app.core.http_utils import get_client_ip


def _make_request(forwarded: str | None = None, peer: str | None = "10.0.0.1") -> Request:
    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
    scope: dict = {"type": "http", "headers": headers}
    if peer is not None:
        scope["client"] = (peer, 12345)
    return Request(scope)


# Tipo de test: Unit
def test_uses_rightmost_forwarded_for() -> None:
    """El valor más a la derecha lo añade el edge de confianza; el izquierdo es spoofable."""
    request = _make_request("1.1.1.1, 2.2.2.2, 3.3.3.3")

    assert get_client_ip(request) == "3.3.3.3"


# Tipo de test: Unit
def test_falls_back_to_peer_without_forwarded_for() -> None:
    request = _make_request(peer="203.0.113.5")

    assert get_client_ip(request) == "203.0.113.5"


# Tipo de test: Unit
def test_returns_unknown_without_peer_or_forwarded_for() -> None:
    request = _make_request(peer=None)

    assert get_client_ip(request) == "unknown"
