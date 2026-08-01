"""What a provider needs from a credential."""

from __future__ import annotations

from typing import Protocol


class TokenSource(Protocol):
    """Supplies an ``Authorization`` header value, refreshing it as it expires.

    A provider asks per request rather than holding a string, because tokens
    expire: a Connect JWT lasts 20 minutes and a Google access token about an
    hour, both shorter than a client's useful life. Caching belongs to the
    implementation, which is the only side that knows the expiry.
    """

    def authorization_header(self) -> str: ...

    async def aauthorization_header(self) -> str: ...
