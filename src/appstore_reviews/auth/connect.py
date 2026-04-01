"""App Store Connect JWT authentication."""

from __future__ import annotations

import base64
import json
import time
from typing import Any


class ConnectAuth:
    """Generates JWT bearer tokens for the App Store Connect API."""

    def __init__(
        self,
        *,
        key_id: str,
        issuer_id: str,
        private_key: str,
    ) -> None:
        if not key_id:
            raise ValueError("key_id must not be empty.")
        if not issuer_id:
            raise ValueError("issuer_id must not be empty.")
        if not private_key:
            raise ValueError("private_key must not be empty.")
        self.key_id = key_id
        self.issuer_id = issuer_id
        self._private_key = private_key

    def generate_token(self) -> str:
        """Generate a signed ES256 JWT for App Store Connect."""
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec, utils

        now = int(time.time())
        header = {"alg": "ES256", "kid": self.key_id, "typ": "JWT"}
        payload: dict[str, Any] = {
            "iss": self.issuer_id,
            "iat": now,
            "exp": now + 20 * 60,
            "aud": "appstoreconnect-v1",
        }

        def _b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

        header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{header_b64}.{payload_b64}".encode()

        key = serialization.load_pem_private_key(
            self._private_key.encode(), password=None
        )
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            raise TypeError("Private key must be an EC key.")

        der_sig = key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
        # Decode DER signature to raw (r || s) for JWT
        r, s = utils.decode_dss_signature(der_sig)
        key_size = key.key_size
        byte_len = (key_size + 7) // 8
        sig_bytes = r.to_bytes(byte_len, "big") + s.to_bytes(byte_len, "big")
        sig_b64 = _b64url(sig_bytes)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def authorization_header(self) -> str:
        """Return a full 'Bearer <token>' string."""
        return f"Bearer {self.generate_token()}"
