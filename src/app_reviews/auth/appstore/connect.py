"""App Store Connect JWT authentication."""

from __future__ import annotations

import time
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from app_reviews.models.auth import ConnectCredentials
from app_reviews.utils.jwt import (
    convert_der_to_raw_signature,
    encode_base64url,
    encode_jwt_segment,
    load_ec_private_key_from_pem,
)

TOKEN_EXPIRY_SECONDS = 20 * 60


class ConnectAuth:
    """JWT token generator for the App Store Connect API.

    Args:
        credentials: Validated App Store Connect credentials.
    """

    def __init__(self, credentials: ConnectCredentials) -> None:
        self._credentials = credentials

    def _build_header(self) -> dict[str, str]:
        """Build the JWT header claims.

        Returns:
            Dict with algorithm, key ID, and token type.
        """
        return {"alg": "ES256", "kid": self._credentials.key_id, "typ": "JWT"}

    def _build_payload(self) -> dict[str, Any]:
        """Build the JWT payload claims.

        Returns:
            Dict with issuer, issued-at, expiry, and audience.
        """
        now = int(time.time())
        return {
            "iss": self._credentials.issuer_id,
            "iat": now,
            "exp": now + TOKEN_EXPIRY_SECONDS,
            "aud": "appstoreconnect-v1",
        }

    def _sign(self, message: bytes) -> bytes:
        """Sign a message with the EC private key using ES256.

        Args:
            message: The raw bytes to sign (typically the JWT signing input).

        Returns:
            Raw ECDSA signature bytes in (r || s) format.
        """
        key = load_ec_private_key_from_pem(self._credentials.private_key)
        der_signature = key.sign(message, ec.ECDSA(hashes.SHA256()))
        return convert_der_to_raw_signature(der_signature, key.key_size)

    def generate_token(self) -> str:
        """Generate a signed ES256 JWT for App Store Connect.

        Returns:
            Encoded JWT string in ``<header>.<payload>.<signature>`` format.
        """
        header_b64 = encode_jwt_segment(self._build_header())
        payload_b64 = encode_jwt_segment(self._build_payload())

        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature_b64 = encode_base64url(self._sign(signing_input))

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def authorization_header(self) -> str:
        """Generate a Bearer authorization header value.

        Returns:
            String in ``Bearer <token>`` format, ready for HTTP headers.
        """
        return f"Bearer {self.generate_token()}"
