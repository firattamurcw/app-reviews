"""Credential problems must arrive as ``AuthError``, not as stdlib exceptions.

Reading the .p8 and validating the PEM happen while building the provider, so a
typo'd ``key_path`` used to surface as ``FileNotFoundError``, bypassing the whole
typed-error hierarchy. ``AuthError``'s own docstring names this case as the reason
it does not subclass ``HttpError``.
"""

import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app_reviews import AppReviewsError, AppStoreAuth, AppStoreReviews, AuthError


def _client(key_path: str) -> AppStoreReviews:
    return AppStoreReviews(
        auth=AppStoreAuth(key_id="K", issuer_id="I", key_path=key_path)
    )


def _write(contents: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".p8", delete=False) as f:
        f.write(contents)
        return f.name


def _rsa_p8() -> str:
    """A valid RSA key saved as a .p8: well-formed PEM, wrong algorithm.

    Easy to do by accident when an account has several keys. Apple signs Connect
    tokens with ES256, so this key parses and then cannot be used.
    """
    return _write(
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        .private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        .decode()
    )


class TestUnusableKeyFile:
    @pytest.mark.parametrize(
        ("label", "path_factory"),
        [
            ("missing", lambda: "/nope/definitely-missing.p8"),
            ("a directory", lambda: tempfile.mkdtemp()),
            ("empty", lambda: _write("")),
            ("not a PEM", lambda: _write("not a pem at all\n")),
            (
                "PEM header, unusable body",
                lambda: _write(
                    "-----BEGIN PRIVATE KEY-----\n"
                    "notbase64\n"
                    "-----END PRIVATE KEY-----\n"
                ),
            ),
            ("an RSA key rather than EC", _rsa_p8),
        ],
    )
    def test_it_raises_auth_error(self, label, path_factory):
        with pytest.raises(AuthError):
            _client(path_factory()).fetch("123")

    def test_the_wrong_key_algorithm_says_so(self):
        """``load_ec_private_key_from_pem`` raises ``TypeError`` for a non-EC key,
        which is not a ``ValueError``, so it escaped the error hierarchy."""
        with pytest.raises(AuthError, match="EC"):
            _client(_rsa_p8()).fetch("123")

    def test_auth_error_is_catchable_as_the_base(self):
        with pytest.raises(AppReviewsError):
            _client("/nope/missing.p8").fetch("123")

    def test_the_message_names_the_path(self):
        with pytest.raises(AuthError, match=r"missing-key\.p8"):
            _client("/nope/missing-key.p8").fetch("123")

    def test_the_original_cause_is_preserved(self):
        with pytest.raises(AuthError) as exc:
            _client("/nope/missing.p8").fetch("123")

        assert isinstance(exc.value.__cause__, OSError)

    async def test_the_async_path_raises_the_same(self):
        with pytest.raises(AuthError):
            await _client("/nope/missing.p8").afetch("123")


class TestUsableKeyFile:
    def test_a_real_key_builds_the_official_provider(self):
        from tests.app_reviews.appstore.test_auth import _TEST_PRIVATE_KEY

        client = _client(_write(_TEST_PRIVATE_KEY))

        assert client.source == "appstore_official"

    def test_no_auth_needs_no_key_and_uses_the_scraper(self):
        assert AppStoreReviews().source == "appstore_scraper"

    def test_the_key_is_read_once_per_client(self):
        """Provider construction is cached, so the file is not re-read per call."""
        from tests.app_reviews.appstore.test_auth import _TEST_PRIVATE_KEY

        path = Path(_write(_TEST_PRIVATE_KEY))
        client = _client(str(path))
        assert client.source == "appstore_official"
        path.unlink()  # gone now; a second read would fail

        assert client.source == "appstore_official"
