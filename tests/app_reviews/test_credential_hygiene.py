"""Key material must not survive in a traceback.

``ConnectCredentials.private_key`` and ``ServiceAccountCredentials.private_key_pem``
are ``field(repr=False)`` so the PEM cannot reach a log line, but ``repr`` is only
half of it. An error reporter that captures frame locals (Sentry does, by default,
and it walks ``__cause__``) reads the *locals* of every frame in the traceback, not
the repr of the exception. A loader that binds the raw key to a local and then
raises hands the key to that reporter.

These tests assert the invariant directly rather than any one implementation of
it: no frame reachable from the raised error holds the secret.
"""

from __future__ import annotations

import json

import pytest

from app_reviews.appstore.reviews import AppStoreReviews
from app_reviews.core.jwt import load_ec_private_key_from_pem
from app_reviews.errors import AuthError
from app_reviews.googleplay.auth import GoogleAuth
from app_reviews.models.config import AppStoreAuth

SECRET = "SUPER-SECRET-KEY-MATERIAL-DO-NOT-LEAK"


def _frames_holding(exc: BaseException, needle: str) -> list[str]:
    """Every frame reachable from ``exc`` whose locals contain ``needle``.

    Follows ``__cause__`` and ``__context__``, because both keep the frames of
    the original failure alive and a reporter walks them.
    """
    seen: set[int] = set()
    holding: list[str] = []
    stack: list[BaseException | None] = [exc]
    while stack:
        current = stack.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        tb = current.__traceback__
        while tb is not None:
            if needle in repr(tb.tb_frame.f_locals):
                holding.append(
                    f"{type(current).__name__} -> {tb.tb_frame.f_code.co_name}"
                )
            tb = tb.tb_next
        stack += [current.__cause__, current.__context__]
    return holding


class TestTheAppStoreKeyDoesNotReachATraceback:
    def test_an_unusable_p8_fails_without_carrying_the_key(self, tmp_path):
        """A readable file that is not a usable key: the caller sees ``AuthError``,
        the reporter sees no PEM."""
        key_path = tmp_path / "key.p8"
        key_path.write_text(SECRET, encoding="utf-8")

        with pytest.raises(AuthError) as caught:
            AppStoreReviews()._credentials(
                AppStoreAuth(key_id="k", issuer_id="i", key_path=str(key_path))
            )

        assert _frames_holding(caught.value, SECRET) == []

    def test_an_empty_key_id_does_not_carry_the_key_either(self, tmp_path):
        """The key is valid-shaped here; a *different* field is what fails, and the
        key must still not travel."""
        key_path = tmp_path / "key.p8"
        key_path.write_text(
            f"-----BEGIN PRIVATE KEY-----\n{SECRET}\n", encoding="utf-8"
        )

        with pytest.raises(AuthError) as caught:
            AppStoreReviews()._credentials(
                AppStoreAuth(key_id="", issuer_id="i", key_path=str(key_path))
            )

        assert _frames_holding(caught.value, SECRET) == []


class TestTheGoogleKeyDoesNotReachATraceback:
    def test_an_unusable_service_account_fails_without_carrying_it(self, tmp_path):
        """``_load`` binds the whole parsed document, so a leak here is the entire
        service-account file, not just the key."""
        path = tmp_path / "sa.json"
        path.write_text(
            json.dumps({"client_email": "", "private_key": SECRET}), encoding="utf-8"
        )

        with pytest.raises(AuthError) as caught:
            GoogleAuth(str(path))._load(str(path))

        assert _frames_holding(caught.value, SECRET) == []

    def test_a_non_google_token_uri_does_not_carry_the_key(self, tmp_path):
        """The rejected value is the ``token_uri``; the key is incidental and must
        not ride along."""
        path = tmp_path / "sa.json"
        path.write_text(
            json.dumps(
                {
                    "client_email": "a@b.iam.gserviceaccount.com",
                    "private_key": f"-----BEGIN PRIVATE KEY-----\n{SECRET}\n",
                    "token_uri": "https://evil.test/token",
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(AuthError) as caught:
            GoogleAuth(str(path))._load(str(path))

        assert _frames_holding(caught.value, SECRET) == []


class TestTheJwtLoaderDoesNotReachATraceback:
    def test_an_unreadable_pem_does_not_carry_it(self):
        """``load_pem_private_key`` raises ``ValueError`` from a frame below, but
        this function's own frame still binds ``pem``."""
        with pytest.raises(ValueError) as caught:
            load_ec_private_key_from_pem(SECRET)

        assert _frames_holding(caught.value, SECRET) == []

    def test_a_wrong_algorithm_key_does_not_carry_it(self):
        """The documented trap: an RSA key saved as a .p8 parses fine and fails the
        type check, so ``pem`` is live in the frame that raises."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        rsa_pem = (
            rsa.generate_private_key(public_exponent=65537, key_size=2048)
            .private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            .decode()
        )

        with pytest.raises(TypeError) as caught:
            load_ec_private_key_from_pem(rsa_pem)

        assert _frames_holding(caught.value, rsa_pem) == []
