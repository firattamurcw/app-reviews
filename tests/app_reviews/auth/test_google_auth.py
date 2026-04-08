"""Tests for Google Play service account authentication."""

import json
from unittest.mock import mock_open, patch

import pytest

from app_reviews.auth.googleplay.service_account import GoogleAuth
from app_reviews.errors import AuthError
from app_reviews.utils.http import HttpResponse

# RSA 2048 test key in PKCS8 format — generated for testing only, not real credentials.
_TEST_RSA_KEY = """\
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

_SERVICE_ACCOUNT_JSON = {
    "client_email": "test@test.iam.gserviceaccount.com",
    "private_key": _TEST_RSA_KEY,
    "token_uri": "https://oauth2.googleapis.com/token",
}


class TestGoogleAuthInit:
    def test_loads_service_account_from_file(self):
        data = json.dumps(_SERVICE_ACCOUNT_JSON)
        with patch("builtins.open", mock_open(read_data=data)):
            auth = GoogleAuth("/fake/path.json")
        assert auth._credentials.client_email == "test@test.iam.gserviceaccount.com"

    def test_missing_fields_use_defaults(self):
        data = json.dumps({"private_key": _TEST_RSA_KEY})
        with (
            patch("builtins.open", mock_open(read_data=data)),
            pytest.raises(ValueError, match="client_email"),
        ):
            GoogleAuth("/fake/path.json")


class TestGoogleAuthBuildJwt:
    def _make_auth(self):
        data = json.dumps(_SERVICE_ACCOUNT_JSON)
        with patch("builtins.open", mock_open(read_data=data)):
            return GoogleAuth("/fake/path.json")

    def test_jwt_has_three_parts(self):
        auth = self._make_auth()
        jwt = auth._build_jwt()
        parts = jwt.split(".")
        assert len(parts) == 3

    def test_jwt_header_contains_rs256(self):
        import base64

        auth = self._make_auth()
        jwt = auth._build_jwt()
        header_b64 = jwt.split(".")[0]
        # Re-pad base64
        padded = header_b64 + "=" * (4 - len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(padded))
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"

    def test_jwt_payload_contains_expected_claims(self):
        import base64

        auth = self._make_auth()
        jwt = auth._build_jwt()
        payload_b64 = jwt.split(".")[1]
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        assert payload["iss"] == "test@test.iam.gserviceaccount.com"
        assert "androidpublisher" in payload["scope"]
        assert payload["exp"] == payload["iat"] + 3600


class TestGoogleAuthAuthorizationHeader:
    def _make_auth(self):
        data = json.dumps(_SERVICE_ACCOUNT_JSON)
        with patch("builtins.open", mock_open(read_data=data)):
            return GoogleAuth("/fake/path.json")

    @patch("app_reviews.auth.googleplay.service_account.http_post")
    def test_returns_bearer_token(self, mock_post):
        mock_post.return_value = HttpResponse(
            status=200,
            body=json.dumps({"access_token": "ya29.test-token"}),
        )
        auth = self._make_auth()
        header = auth.authorization_header()
        assert header == "Bearer ya29.test-token"

    @patch("app_reviews.auth.googleplay.service_account.http_post")
    def test_sends_jwt_assertion_in_body(self, mock_post):
        mock_post.return_value = HttpResponse(
            status=200,
            body=json.dumps({"access_token": "tok"}),
        )
        auth = self._make_auth()
        auth.authorization_header()
        call_kwargs = mock_post.call_args[1]
        assert "assertion=" in call_kwargs["body"]
        assert "grant_type=" in call_kwargs["body"]

    @patch("app_reviews.auth.googleplay.service_account.http_post")
    def test_non_200_raises_auth_error(self, mock_post):
        mock_post.return_value = HttpResponse(status=401, body="unauthorized")
        auth = self._make_auth()
        with pytest.raises(AuthError, match="401"):
            auth.authorization_header()
