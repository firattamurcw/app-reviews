"""Auth-related models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppStoreAuth:
    """Apple App Store Connect API credentials."""

    key_id: str
    issuer_id: str
    key_path: str


@dataclass(frozen=True, slots=True)
class GooglePlayAuth:
    """Google Play Developer API credentials."""

    service_account_path: str


@dataclass(frozen=True, slots=True)
class ConnectCredentials:
    """Validated credentials for App Store Connect API authentication."""

    key_id: str
    issuer_id: str
    private_key: str

    def __post_init__(self) -> None:
        if not self.key_id:
            raise ValueError("key_id must not be empty.")
        if not self.issuer_id:
            raise ValueError("issuer_id must not be empty.")
        if not self.private_key:
            raise ValueError("private_key must not be empty.")
        if "-----BEGIN" not in self.private_key:
            raise ValueError("private_key must be a PEM-encoded key.")


@dataclass(frozen=True, slots=True)
class ServiceAccountCredentials:
    """Validated credentials for Google Play service account authentication."""

    client_email: str
    private_key_pem: str
    token_uri: str

    def __post_init__(self) -> None:
        if not self.client_email:
            raise ValueError("client_email must not be empty.")
        if not self.private_key_pem:
            raise ValueError("private_key_pem must not be empty.")
        if "-----BEGIN" not in self.private_key_pem:
            raise ValueError("private_key_pem must be a PEM-encoded key.")
        if not self.token_uri:
            raise ValueError("token_uri must not be empty.")
