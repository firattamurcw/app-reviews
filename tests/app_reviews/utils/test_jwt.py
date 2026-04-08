"""Tests for JWT encoding and signing utilities."""

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app_reviews.utils.jwt import (
    convert_der_to_raw_signature,
    encode_base64url,
    encode_jwt_segment,
    load_ec_private_key_from_pem,
)

# EC P-256 test key — for testing only.
_TEST_EC_KEY_PEM = """\
-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgmyZUU2SlJ3toFzmc
KjNRLWVEsavmMY1Hj7b1ZrzLLw2hRANCAARRL8UbpZS8HUhpOGIGGtjoeF37luMJ
M7B/Gtt1xwTbLmdGUAZtvYMSMhCVBMel1av5EYUWK24HE7Aj3J+O1AAq
-----END PRIVATE KEY-----
"""

# RSA key in PKCS8 format — should be rejected by load_ec_private_key_from_pem.
_TEST_RSA_KEY_PEM = """\
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCsfsIYt4li+qCP
ItkaZbm3f6siEa0ItRF98Il4dwdwn1ahSTZNKiY6IVpdkEJSjancWKSrTkRm8RM4
lCSvuxWhYgAfrNtc5cmFbidxBZOlfCtK+uvzNdPKUGALPSorp5BUWALt64T9i2Sb
nNFZy4uDXzcnry0/+Ktacss9JfUzKX8r8sDa20YRvCBftpwJK/nQeNQXT2IbI2IG
f4r2b4UDcrTusA/CGrC8kzV795R0F1rs+ZZf/Q4xZOButuyjm9JUIyP0gPRoOFnN
v8PhbM4l+InKalbSpgJ4poIpnzoCLtTrPly1wzjuDLVbC1vqTkQN66a/ifu3hkET
bMQ9eEw/AgMBAAECggEACmR+tDeGnwCDoOwUEXuUg2I9QMm415/1JFXUKn5dY+Mt
uHztORvzfqgYxi9VV5zyYXSzwyBtjZgztMJ0LWRDqtv5Lu9erguoJxJabPxNh3hi
MVvJ0HbrQjKyfqraOhQX5YUB9Cyu8Amwb5G0qUjSqIEZlRoAS2zjggkNhqsdSU46
5E6ogKXhkpTrAa7KSNOom5llqk8eAkbpbCxWko7Hh/2RGzBrXvPjEe0fIp4JmL9J
n8fvTP8QCndDhyOB3R4DsKckHyvRECZ5bX89zTuCZEHoACRNfl5X4M3ie+WdV0MU
UGiVl7cDRx67NSX/sfgy2G0NKZxFXQQ3ZOFVd2VAgQKBgQDap7KPQSqzdwl/8+hF
geGrKp0hUZjQOZF2SFxamHYxZiSXFWUspqNgGToARAxR92DE+rrQazw8ikFiIXti
3O8i0AmQEgYoJefLyWRdDPDnwBPhZ/udALarE8VobnzFnj7IRGWddZ6jO3WkXp/9
hxyLuCDxGFKV1+BiIrTZbpmbgQKBgQDJ9Mz2WpzyJASzo1mjOGwnuvYqioh78QF9
EHXvP1ETHmrMuVPMSzM8rluinJBQquIQ1gnMSCwFUwc5z2LT8F8GrOyhH4aM2lE6
/3vEa7Dcp8+R2e+LMVmOn6rY+alLplVp4oices+/u/2UzYfPEoOmmEEPRtgHGVh/
E2wzPvzHvwKBgQDH3xFO9+/TmxV4+/kvSFmDwHFf2pnIhUcdi2m4erNX1pnN7YXN
egnPt1+YjJuCdZHknZkVGWE3qd24mQiTx4dlGCwVoRQ1sOihFNgEYub3wVGq8wVC
cDuKSIlkO9McRdn38OW+OJ0pcxnHhaPT+aSzZz3dhTFAvdPjgPw14W7SgQKBgQDF
osqd38ktcbAkOBx1jbbSHrXepdmxKQZi5KP1MQpfYmnz1P27tG/810iX1w2n08MN
5NiL0Kk7wKgWm+xEKjxkZP/hId/joZbS3Mi7TQQ0vAh23Eb++ZmB6KEiWxihDrMR
vv4f3FPId+lOIODh9WVeuCsbDyJDuDsRiOlfMSnhMwKBgDh3v+7dI2E9pIWDzW6R
BGvqX5FnWN4OCbyl98cSo99qXFnLqifFpVfJjhdxk5uDsD5mqwl9GbhNhDFrSVst
OZyyCpMAriwhjl+6B6UT9xwDaqIq+8wxl4zjn4ekjZuT5q19kNC5kWqBKxZs61hG
sFAt2f21YJ6sthPw/SAGgy8t
-----END PRIVATE KEY-----
"""


class TestEncodeBase64url:
    def test_empty_bytes(self):
        assert encode_base64url(b"") == ""

    def test_strips_padding(self):
        result = encode_base64url(b"a")
        assert "=" not in result

    def test_url_safe_characters(self):
        # Bytes that produce + and / in standard base64
        data = b"\xfb\xff\xfe"
        result = encode_base64url(data)
        assert "+" not in result
        assert "/" not in result

    def test_round_trip(self):
        data = b"hello world"
        encoded = encode_base64url(data)
        padded = encoded + "=" * (4 - len(encoded) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        assert decoded == data


class TestEncodeJwtSegment:
    def test_produces_valid_base64url_json(self):
        claims = {"alg": "ES256", "typ": "JWT"}
        result = encode_jwt_segment(claims)
        padded = result + "=" * (4 - len(result) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        assert decoded == claims

    def test_compact_json_no_spaces(self):
        claims = {"key": "value", "num": 42}
        result = encode_jwt_segment(claims)
        padded = result + "=" * (4 - len(result) % 4)
        raw_json = base64.urlsafe_b64decode(padded).decode()
        assert " " not in raw_json


class TestConvertDerToRawSignature:
    def test_p256_signature_is_64_bytes(self):
        key = ec.generate_private_key(ec.SECP256R1())
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec as ec_mod

        der_sig = key.sign(b"test", ec_mod.ECDSA(hashes.SHA256()))
        raw = convert_der_to_raw_signature(der_sig, 256)
        assert len(raw) == 64

    def test_p384_signature_is_96_bytes(self):
        key = ec.generate_private_key(ec.SECP384R1())
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec as ec_mod

        der_sig = key.sign(b"test", ec_mod.ECDSA(hashes.SHA384()))
        raw = convert_der_to_raw_signature(der_sig, 384)
        assert len(raw) == 96


class TestLoadEcPrivateKeyFromPem:
    def test_loads_valid_ec_key(self):
        key = load_ec_private_key_from_pem(_TEST_EC_KEY_PEM)
        assert isinstance(key, ec.EllipticCurvePrivateKey)

    def test_rejects_rsa_key(self):
        with pytest.raises(TypeError, match="EC key"):
            load_ec_private_key_from_pem(_TEST_RSA_KEY_PEM)
