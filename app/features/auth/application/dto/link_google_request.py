"""Request to link a Google account to an existing user."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LinkGoogleAccountRequest:
    """Request body for linking a Google account."""

    google_id: str
    password: str
