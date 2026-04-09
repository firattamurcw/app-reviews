"""Tests for BaseSearch ABC."""

import pytest

from app_reviews.clients.base_search import BaseSearch
from app_reviews.models.country import Country
from app_reviews.models.retry import RetryConfig


class ConcreteSearch(BaseSearch):
    """Minimal concrete implementation for testing the ABC."""

    def search(self, query, *, country=Country.US, limit=50):
        return []

    def lookup(self, app_id, *, country=Country.US):
        return None


class TestBaseSearch:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseSearch()

    def test_concrete_subclass_can_instantiate(self):
        client = ConcreteSearch()
        assert client is not None

    def test_stores_proxy(self):
        client = ConcreteSearch(proxy="http://proxy:8080")
        assert client._proxy == "http://proxy:8080"

    def test_stores_retry_config(self):
        retry = RetryConfig(max_retries=5)
        client = ConcreteSearch(retry=retry)
        assert client._retry is retry

    def test_default_retry_is_default_config(self):
        client = ConcreteSearch()
        assert isinstance(client._retry, RetryConfig)

    def test_default_proxy_is_none(self):
        client = ConcreteSearch()
        assert client._proxy is None
