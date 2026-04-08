"""Tests for App Store Connect authentication."""

import pytest

from app_reviews.auth.appstore.connect import ConnectAuth
from app_reviews.models.auth import ConnectCredentials

# A valid EC P-256 (PKCS8) private key for testing only — not real credentials.
_TEST_PRIVATE_KEY = """\
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgmyZUU2SlJ3toFzmc
KjNRLWVEsavmMY1Hj7b1ZrzLLw2hRANCAARRL8UbpZS8HUhpOGIGGtjoeF37luMJ
M7B/Gtt1xwTbLmdGUAZtvYMSMhCVBMel1av5EYUWK24HE7Aj3J+O1AAq
-----END PRIVATE KEY-----
"""


def _make_credentials(**overrides: str) -> ConnectCredentials:
    defaults = {
        "key_id": "KEY123",
        "issuer_id": "ISSUER456",
        "private_key": _TEST_PRIVATE_KEY,
    }
    return ConnectCredentials(**(defaults | overrides))


class TestConnectCredentials:
    def test_missing_key_id_raises(self) -> None:
        with pytest.raises(ValueError, match="key_id"):
            _make_credentials(key_id="")

    def test_missing_issuer_id_raises(self) -> None:
        with pytest.raises(ValueError, match="issuer_id"):
            _make_credentials(issuer_id="")

    def test_missing_private_key_raises(self) -> None:
        with pytest.raises(ValueError, match="private_key"):
            _make_credentials(private_key="")

    def test_non_pem_private_key_raises(self) -> None:
        with pytest.raises(ValueError, match="PEM"):
            _make_credentials(private_key="not-a-pem-key")

    def test_valid_credentials(self) -> None:
        creds = _make_credentials()
        assert creds.key_id == "KEY123"
        assert creds.issuer_id == "ISSUER456"


class TestConnectAuth:
    def test_authorization_header_has_bearer_prefix(self) -> None:
        auth = ConnectAuth(_make_credentials())
        header = auth.authorization_header()
        assert header.startswith("Bearer ")
        token = header.removeprefix("Bearer ")
        assert len(token.split(".")) == 3

    def test_generate_token_returns_jwt_string(self) -> None:
        auth = ConnectAuth(_make_credentials())
        token = auth.generate_token()
        assert isinstance(token, str)
        assert len(token.split(".")) == 3
