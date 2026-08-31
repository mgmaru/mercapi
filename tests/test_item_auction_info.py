"""Auction properties of the item detail endpoint.

The response carries three different auction shapes across the API, and this
endpoint is the one whose model used to demand every property. A listing whose
``auction_info`` could not be read was reported as ``None``, which is exactly
what an ordinary listing looks like, so an auction could pass as a normal sale.

These tests pin the opposite behaviour: an unrecognised shape stays visible.
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


class TestKnownShape:
    @pytest.mark.asyncio
    async def test_parses_every_property_of_an_auction_listing(self):
        api = mercapi_returning("auction.json")

        item = await api.item("m000000000001")

        auction = item.auction_info
        assert auction is not None
        assert auction.id_ == "100000001"
        assert auction.total_bids == 3
        assert auction.initial_price == 300
        assert auction.highest_bid == 1200
        assert auction.state == "STATE_ONGOING"
        assert auction.auction_type == "AUCTION_TYPE_NORMAL"
        assert auction.start_time is not None
        assert auction.expected_end_time is not None

    @pytest.mark.asyncio
    async def test_leaves_auction_info_unset_for_a_normal_listing(self):
        api = mercapi_returning("fixed_price.json")

        item = await api.item("m000000000002")

        assert item.auction_info is None

    @pytest.mark.asyncio
    async def test_leaves_auction_info_unset_when_the_key_is_null(self):
        api = mercapi_returning("auction_info_null.json")

        item = await api.item("m000000000003")

        assert item.auction_info is None


class TestUnknownShape:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fixture,item_id",
        [
            ("auction_info_empty.json", "m000000000004"),
            ("auction_info_unknown_shape.json", "m000000000005"),
        ],
    )
    async def test_keeps_an_unreadable_shape_distinguishable(self, fixture, item_id):
        api = mercapi_returning(fixture)

        item = await api.item(item_id)

        auction = item.auction_info
        assert (
            auction is not None
        ), "an unrecognised shape must not look like a normal listing"
        assert auction.id_ is None
        assert auction.highest_bid is None
        assert auction.state is None

    @pytest.mark.asyncio
    async def test_keeps_the_properties_it_could_read(self):
        api = mercapi_returning("auction_info_partial.json")

        item = await api.item("m000000000006")

        auction = item.auction_info
        assert auction is not None
        assert auction.id_ == "100000001"
        assert auction.highest_bid == 1200
        assert auction.state is None
        assert auction.total_bids is None
