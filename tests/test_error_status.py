"""Error statuses reach the caller as an error.

A 401, 403, 429 or 5xx used to be handed to the mapper as if it were a normal
body. The caller saw a parse error, could not tell rate limiting apart from a
response format change, and had no reason to back off.

These tests replace the HTTP layer with `httpx.MockTransport`; no cassette is
recorded or read.
"""

import httpx
import pytest

from mercapi import Mercapi
from mercapi.requests import SearchRequestData


def mercapi_returning_status(status_code: int, body: dict = None):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=body if body is not None else {})

    api = Mercapi()
    api._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return api


async def call(api: Mercapi, operation: str):
    if operation == "search":
        return await api.search("sample query")
    if operation == "item":
        return await api.item("m000000000001")
    if operation == "profile":
        return await api.profile("100000001")
    if operation == "items":
        return await api.items("100000001")
    if operation == "items_page":
        return await api.items_page("100000001", ("on_sale",))
    if operation == "shop_product":
        return await api.shop_product("p000000001")
    raise AssertionError(f"unknown operation {operation}")


OPERATIONS = ["search", "item", "profile", "items", "items_page", "shop_product"]


class TestErrorStatus:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [401, 403, 429, 500, 503])
    @pytest.mark.parametrize("operation", OPERATIONS)
    async def test_reports_the_status(self, operation, status_code):
        api = mercapi_returning_status(status_code)

        with pytest.raises(httpx.HTTPStatusError) as raised:
            await call(api, operation)

        assert raised.value.response.status_code == status_code


class TestNotFound:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "operation", ["item", "profile", "items", "items_page", "shop_product"]
    )
    async def test_a_missing_resource_stays_a_normal_answer(self, operation):
        api = mercapi_returning_status(404)

        assert await call(api, operation) is None


class TestSuccess:
    @pytest.mark.asyncio
    async def test_a_successful_response_is_untouched(self):
        api = mercapi_returning_status(
            200, {"result": "OK", "meta": {"has_next": False}, "data": []}
        )

        page = await api.items_page("100000001", ("on_sale",))

        assert page.items == []
        assert page.has_next is False

    @pytest.mark.asyncio
    async def test_search_keeps_its_request_for_paging(self):
        api = mercapi_returning_status(
            200,
            {
                "meta": {"nextPageToken": "", "previousPageToken": "", "numFound": "0"},
                "items": [],
            },
        )

        results = await api.search("sample query")

        assert results.items == []
        assert isinstance(results._request, SearchRequestData)
