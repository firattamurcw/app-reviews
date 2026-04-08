"""Google Play Developer API authentication via service account.

Self-implemented JWT exchange using cryptography + urllib — no google-auth dependency.
"""

from __future__ import annotations

import json
import time
import urllib.parse

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from app_reviews.errors import AuthError
from app_reviews.models.auth import ServiceAccountCredentials
from app_reviews.utils.http import http_post
from app_reviews.utils.jwt import encode_base64url, encode_jwt_segment

_SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]
_DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"


class GoogleAuth:
    """Manages Google service account authentication via self-signed JWT.

    Args:
        service_account_path: Path to the Google service account JSON key file.
    """

    def __init__(self, service_account_path: str) -> None:
        with open(service_account_path) as f:
            sa = json.load(f)
        self._credentials = ServiceAccountCredentials(
            client_email=sa.get("client_email", ""),
            private_key_pem=sa.get("private_key", ""),
            token_uri=sa.get("token_uri", _DEFAULT_TOKEN_URI),
        )

    def _build_jwt(self) -> str:
        """Build and sign a JWT assertion for the token exchange.

        Returns:
            Encoded JWT string in ``<header>.<payload>.<signature>`` format.
        """
        now = int(time.time())

        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": self._credentials.client_email,
            "scope": " ".join(_SCOPES),
            "aud": self._credentials.token_uri,
            "iat": now,
            "exp": now + 3600,
        }

        header_b64 = encode_jwt_segment(header)
        payload_b64 = encode_jwt_segment(payload)
        signing_input = f"{header_b64}.{payload_b64}".encode()

        # Load RSA private key and sign
        key = serialization.load_pem_private_key(
            self._credentials.private_key_pem.encode(), password=None
        )
        if not isinstance(key, RSAPrivateKey):
            raise TypeError("Service account key must be an RSA key.")
        signature = key.sign(
            signing_input,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        signature_b64 = encode_base64url(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def authorization_header(self) -> str:
        """Exchange a self-signed JWT for an access token.

        Returns:
            String in ``Bearer <token>`` format, ready for HTTP headers.

        Raises:
            AuthError: If the token exchange request fails.
        """
        jwt = self._build_jwt()
        body = urllib.parse.urlencode(
            {
                "grant_type": _GRANT_TYPE,
                "assertion": jwt,
            }
        )
        resp = http_post(
            self._credentials.token_uri,
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status != 200:
            raise AuthError(
                f"Google token exchange failed (HTTP {resp.status}): {resp.body}"
            )
        data = json.loads(resp.body)
        return f"Bearer {data['access_token']}"
