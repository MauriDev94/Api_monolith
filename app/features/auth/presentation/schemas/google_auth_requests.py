"""Google OAuth request schemas."""

from __future__ import annotations

from pydantic import BaseModel


class GoogleInitResponse(BaseModel):
    """Response for initiating Google OAuth flow."""

    authorization_url: str


class GoogleCallbackRequest(BaseModel):
    """Request with OAuth callback code and state."""

    code: str
    state: str | None = None


class GoogleLinkAccountRequest(BaseModel):
    """Request to link a Google account to existing user."""

    google_id: str
    password: str


class GoogleLinkAccountResponse(BaseModel):
    """Response after linking Google account."""

    success: bool
    message: str
