from dataclasses import dataclass


@dataclass(slots=True)
class LogoutParams:
    """Input DTO for the logout flow.

    The refresh token is taken raw (string or None); the use case owns JWT
    decoding and subject extraction so the presentation layer stays free of
    token-payload knowledge.
    """

    refresh_token: str | None
