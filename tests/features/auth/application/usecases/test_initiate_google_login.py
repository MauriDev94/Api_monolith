"""Tests for InitiateGoogleLoginUseCase."""

from __future__ import annotations

from app.features.auth.application.usecases.initiate_google_login import (
    InitiateGoogleLoginParams,
    InitiateGoogleLoginUseCase,
)
from app.features.auth.infrastructure.providers.stub_google_oauth_provider import (
    StubGoogleOAuthProvider,
)


class TestInitiateGoogleLoginUseCase:
    """Unit tests for InitiateGoogleLoginUseCase."""

    def test_should_return_authorization_url_and_state(self) -> None:
        """Test that the use case returns a valid authorization URL and state."""
        stub_provider = StubGoogleOAuthProvider()
        use_case = InitiateGoogleLoginUseCase(oauth_provider=stub_provider)

        params = InitiateGoogleLoginParams()
        result = use_case.execute(params)

        assert result.authorization_url is not None
        assert result.authorization_url.startswith("https://accounts.google.com")
        assert result.state is not None
        assert len(result.state) > 10  # State should be reasonably long

    def test_should_generate_different_states_for_different_calls(self) -> None:
        """Test that each call generates a different state."""
        stub_provider = StubGoogleOAuthProvider()
        use_case = InitiateGoogleLoginUseCase(oauth_provider=stub_provider)

        params = InitiateGoogleLoginParams()
        result1 = use_case.execute(params)
        result2 = use_case.execute(params)

        assert result1.state != result2.state

    def test_should_include_state_in_authorization_url(self) -> None:
        """Test that the authorization URL contains the state parameter."""
        stub_provider = StubGoogleOAuthProvider()
        use_case = InitiateGoogleLoginUseCase(oauth_provider=stub_provider)

        params = InitiateGoogleLoginParams()
        result = use_case.execute(params)

        assert f"state={result.state}" in result.authorization_url
