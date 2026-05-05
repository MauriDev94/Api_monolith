"""Params for creating a Google user."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateGoogleUserParams:
    """Params to create a user via Google OAuth."""

    google_id: str
    email: str
    name: str
    lastname: str
    google_email_verified: bool = False
