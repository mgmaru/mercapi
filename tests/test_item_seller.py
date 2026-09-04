"""``is_inactive`` on the seller of an item detail response.

Mercari puts a boolean called ``is_inactive`` inside the ``seller`` object of
``GET /items/get``. It is the only place the API says anything about the state
of an account: ``GET /users/get_profile`` does not carry it, so it cannot be
read from :class:`~mercapi.models.Profile`.

The behaviour worth pinning is the three way answer. ``True`` and ``False`` are
Mercari's, and **absent is neither** — a response that says nothing must not
arrive as ``False``, which is a caller reporting that Mercari cleared a seller
it was never asked about.
"""

import json
from pathlib import Path

import httpx
import pytest

from mercapi import Mercapi


FIXTURES = Path(__file__).parent / "fixtures" / "item"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def mercapi_returning(fixture_name: str):
    body = load_fixture(fixture_name)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    api = Mercapi()
    api._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return api


class TestIsInactive:
    @pytest.mark.asyncio
    async def test_parses_a_seller_marked_inactive(self):
        api = mercapi_returning("seller_inactive.json")

        item = await api.item("m000000000010")

        assert item.seller.is_inactive is True

    @pytest.mark.asyncio
    async def test_parses_a_seller_marked_active(self):
        api = mercapi_returning("seller_active.json")

        item = await api.item("m000000000011")

        assert item.seller.is_inactive is False

    @pytest.mark.asyncio
    async def test_a_seller_without_the_flag_is_none_and_not_false(self):
        """Absent is not an answer. ``False`` is."""
        api = mercapi_returning("seller_without_is_inactive.json")

        item = await api.item("m000000000012")

        assert item.seller.is_inactive is None

    @pytest.mark.asyncio
    async def test_a_response_without_a_seller_still_parses(self):
        """``seller`` is an optional property, and stays one."""
        api = mercapi_returning("fixed_price.json")

        item = await api.item("m000000000002")

        assert item.seller is None

    @pytest.mark.asyncio
    async def test_the_rest_of_the_seller_is_untouched(self):
        api = mercapi_returning("seller_inactive.json")

        item = await api.item("m000000000010")

        seller = item.seller
        assert seller.id_ == 100000010
        assert seller.num_sell_items == 13
        assert seller.num_ratings == 17
        assert seller.is_blocked is False
