"""Tests for App Store Connect authentication."""

import pytest

from appstore_reviews.auth.connect import ConnectAuth

# A valid EC P-256 (PKCS8) private key for testing only — not real credentials.
_TEST_PRIVATE_KEY = """\
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgmyZUU2SlJ3toFzmc
KjNRLWVEsavmMY1Hj7b1ZrzLLw2hRANCAARRL8UbpZS8HUhpOGIGGtjoeF37luMJ
M7B/Gtt1xwTbLmdGUAZtvYMSMhCVBMel1av5EYUWK24HE7Aj3J+O1AAq
-----END PRIVATE KEY-----
"""


class TestConnectAuth:
    def test_missing_key_id_raises(self) -> None:
        with pytest.raises(ValueError, match="key_id"):
            ConnectAuth(key_id="", issuer_id="abc", private_key=_TEST_PRIVATE_KEY)

    def test_missing_issuer_id_raises(self) -> None:
        with pytest.raises(ValueError, match="issuer_id"):
            ConnectAuth(key_id="ABC123", issuer_id="", private_key=_TEST_PRIVATE_KEY)

    def test_missing_private_key_raises(self) -> None:
        with pytest.raises(ValueError, match="private_key"):
            ConnectAuth(key_id="ABC123", issuer_id="abc", private_key="")

    def test_valid_credentials_create_instance(self) -> None:
        auth = ConnectAuth(
            key_id="KEY123",
            issuer_id="ISSUER456",
            private_key=_TEST_PRIVATE_KEY,
        )
        assert auth.key_id == "KEY123"
        assert auth.issuer_id == "ISSUER456"

    def test_authorization_header_has_bearer_prefix(self) -> None:
        auth = ConnectAuth(
            key_id="KEY123",
            issuer_id="ISSUER456",
            private_key=_TEST_PRIVATE_KEY,
        )
        header = auth.authorization_header()
        assert header.startswith("Bearer ")
        # Token is a JWT with 3 dot-separated parts
        token = header.removeprefix("Bearer ")
        assert len(token.split(".")) == 3

    def test_generate_token_returns_jwt_string(self) -> None:
        auth = ConnectAuth(
            key_id="KEY123",
            issuer_id="ISSUER456",
            private_key=_TEST_PRIVATE_KEY,
        )
        token = auth.generate_token()
        assert isinstance(token, str)
        assert len(token.split(".")) == 3
