"""JWT encoding and ES256 signing utilities."""

from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils


def encode_base64url(data: bytes) -> str:
    """Encode bytes to an unpadded Base64-URL string (RFC 7515).

    Args:
        data: Raw bytes to encode.

    Returns:
        URL-safe Base64 string with padding stripped.
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def encode_jwt_segment(claims: dict[str, Any]) -> str:
    """Serialize a claims dict into a Base64-URL-encoded JWT segment.

    Args:
        claims: JWT header or payload as a dictionary.

    Returns:
        Compact-JSON-encoded, Base64-URL-encoded string.
    """
    compact_json = json.dumps(claims, separators=(",", ":")).encode()
    return encode_base64url(compact_json)


def convert_der_to_raw_signature(der_signature: bytes, key_size: int) -> bytes:
    """Convert a DER-encoded ECDSA signature to fixed-width raw (r || s) format.

    Args:
        der_signature: DER-encoded signature from ``cryptography``.
        key_size: EC key size in bits (e.g. 256 for P-256).

    Returns:
        Raw signature bytes (r and s concatenated, each zero-padded to key size).
    """
    r, s = utils.decode_dss_signature(der_signature)
    byte_length = (key_size + 7) // 8
    return r.to_bytes(byte_length, "big") + s.to_bytes(byte_length, "big")


def load_ec_private_key_from_pem(pem: str) -> ec.EllipticCurvePrivateKey:
    """Load and validate an EC private key from a PEM string.

    Args:
        pem: PEM-encoded private key string.

    Returns:
        Parsed EC private key ready for signing.

    Raises:
        TypeError: If the key is not an elliptic-curve key (e.g. RSA).
    """
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey):
        raise TypeError("Private key must be an EC key.")
    return key
