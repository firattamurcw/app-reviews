"""Tests for ServiceAccountCredentials validation."""

import pytest

from app_reviews.models.auth import ServiceAccountCredentials

_VALID_PEM = "-----BEGIN PRIVATE KEY-----\nfake\n-----END PRIVATE KEY-----"


def _make_creds(**overrides):
    defaults = {
        "client_email": "test@test.iam.gserviceaccount.com",
        "private_key_pem": _VALID_PEM,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return ServiceAccountCredentials(**(defaults | overrides))


class TestServiceAccountCredentialsValidation:
    def test_valid_credentials(self):
        creds = _make_creds()
        assert creds.client_email == "test@test.iam.gserviceaccount.com"

    def test_empty_client_email_raises(self):
        with pytest.raises(ValueError, match="client_email"):
            _make_creds(client_email="")

    def test_empty_private_key_raises(self):
        with pytest.raises(ValueError, match="private_key_pem"):
            _make_creds(private_key_pem="")

    def test_non_pem_private_key_raises(self):
        with pytest.raises(ValueError, match="PEM"):
            _make_creds(private_key_pem="not-a-pem-key")

    def test_empty_token_uri_raises(self):
        with pytest.raises(ValueError, match="token_uri"):
            _make_creds(token_uri="")
