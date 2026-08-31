import json
from pathlib import Path

import httpx
import pytest

from mercapi import Mercapi
from mercapi.util.errors import ParseAPIResponseError


FIXTURES = Path(__file__).parent / "fixtures" / "seller_items"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def mercapi_returning(*fixture_names: str):
    """Build a Mercapi whose HTTP layer replays fixtures in order.

    The recorded requests are returned alongside the client so a test can assert
    on what was actually sent, which is what most of these tests are about.
    """
    requests: list[httpx.Request] = []
    bodies = [load_fixture(name) for name in fixture_names]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = bodies[min(len(requests) - 1, len(bodies) - 1)]
        return httpx.Response(200, json=body)

    api = Mercapi()
    api._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return api, requests


def mercapi_returning_status(status_code: int):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={})

    api = Mercapi()
    api._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return api


class TestRequest:
    @pytest.mark.asyncio
    async def test_sends_a_single_status(self):
        api, requests = mercapi_returning("page_2_end.json")

        await api.items_page("100000001", ("on_sale",))

        params = requests[0].url.params
        assert params["seller_id"] == "100000001"
        assert params["status"] == "on_sale"
        assert params["limit"] == "30"
        assert "max_pager_id" not in params

    @pytest.mark.asyncio
    async def test_sends_sold_out_separately(self):
        api, requests = mercapi_returning("page_2_end.json")

        await api.items_page("100000001", ("sold_out",))

        assert requests[0].url.params["status"] == "sold_out"

    @pytest.mark.asyncio
    async def test_joins_multiple_statuses_with_a_comma(self):
        api, requests = mercapi_returning("page_2_end.json")

        await api.items_page("100000001", ("on_sale", "trading", "sold_out"))

        assert requests[0].url.params["status"] == "on_sale,trading,sold_out"

    @pytest.mark.asyncio
    async def test_sends_with_auction_only_when_requested(self):
        api, requests = mercapi_returning("with_auction.json", "with_auction.json")

        await api.items_page("100000001", ("on_sale",), with_auction=True)
        await api.items_page("100000001", ("on_sale",))

        assert requests[0].url.params["with_auction"] == "true"
        assert "with_auction" not in requests[1].url.params

    @pytest.mark.asyncio
    async def test_honours_a_custom_limit(self):
        api, requests = mercapi_returning("page_2_end.json")

        await api.items_page("100000001", ("on_sale",), limit=5)

        assert requests[0].url.params["limit"] == "5"


class TestPaging:
    @pytest.mark.asyncio
    async def test_exposes_the_last_pager_id_as_the_next_cursor(self):
        api, _ = mercapi_returning("page_1_has_next.json")

        page = await api.items_page("100000001", ("on_sale",))

        assert page.has_next is True
        assert page.next_max_pager_id == 8

    @pytest.mark.asyncio
    async def test_second_page_sends_the_previous_last_pager_id(self):
        api, requests = mercapi_returning("page_1_has_next.json", "page_2_end.json")

        first = await api.items_page("100000001", ("on_sale",))
        second = await api.items_page(
            "100000001", ("on_sale",), max_pager_id=first.next_max_pager_id
        )

        assert requests[1].url.params["max_pager_id"] == "8"
        assert second.has_next is False

    @pytest.mark.asyncio
    async def test_returns_no_cursor_on_the_last_page(self):
        api, _ = mercapi_returning("page_2_end.json")

        page = await api.items_page("100000001", ("on_sale",))

        assert page.has_next is False
        assert page.next_max_pager_id is None

    @pytest.mark.asyncio
    async def test_empty_page_without_next_is_a_normal_end(self):
        api, _ = mercapi_returning("empty_end.json")

        page = await api.items_page("100000001", ("on_sale",))

        assert page.items == []
        assert page.has_next is False
        assert page.next_max_pager_id is None

    @pytest.mark.asyncio
    async def test_keeps_the_response_order(self):
        api, _ = mercapi_returning("page_1_has_next.json")

        page = await api.items_page("100000001", ("on_sale",))

        assert [item.id_ for item in page.items] == [
            "m000000000001",
            "m000000000002",
        ]

    @pytest.mark.asyncio
    async def test_returns_none_for_a_missing_seller(self):
        api = mercapi_returning_status(404)

        assert await api.items_page("100000001", ("on_sale",)) is None


class TestBrokenResponses:
    @pytest.mark.asyncio
    async def test_empty_page_with_next_is_a_parse_error(self):
        api, _ = mercapi_returning("empty_has_next.json")

        with pytest.raises(ParseAPIResponseError):
            await api.items_page("100000001", ("on_sale",))

    @pytest.mark.asyncio
    async def test_missing_trailing_pager_id_is_a_parse_error(self):
        api, _ = mercapi_returning("missing_last_pager_id.json")

        with pytest.raises(ParseAPIResponseError):
            await api.items_page("100000001", ("on_sale",))

    @pytest.mark.asyncio
    async def test_missing_meta_is_a_parse_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"result": "OK", "data": []})

        api = Mercapi()
        api._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with pytest.raises(ParseAPIResponseError):
            await api.items_page("100000001", ("on_sale",))


class TestArguments:
    @pytest.mark.asyncio
    async def test_rejects_an_empty_profile_id(self):
        api, _ = mercapi_returning("page_2_end.json")

        with pytest.raises(ValueError):
            await api.items_page("", ("on_sale",))

    @pytest.mark.asyncio
    async def test_rejects_an_empty_status_tuple(self):
        api, _ = mercapi_returning("page_2_end.json")

        with pytest.raises(ValueError):
            await api.items_page("100000001", ())

    @pytest.mark.asyncio
    async def test_rejects_an_unknown_status(self):
        api, _ = mercapi_returning("page_2_end.json")

        with pytest.raises(ValueError):
            await api.items_page("100000001", ("archived",))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limit", [0, 31])
    async def test_rejects_a_limit_outside_the_supported_range(self, limit):
        api, _ = mercapi_returning("page_2_end.json")

        with pytest.raises(ValueError):
            await api.items_page("100000001", ("on_sale",), limit=limit)


class TestAuctionInfo:
    @pytest.mark.asyncio
    async def test_parses_auction_info_of_an_auction_listing(self):
        api, _ = mercapi_returning("with_auction.json")

        page = await api.items_page("100000001", ("on_sale",), with_auction=True)

        auction = page.items[0].auction_info
        assert auction is not None
        assert auction.id_ == "100000001"
        assert auction.bid_deadline == "2026-09-01T11:52:24Z"
        assert auction.total_bid == 3
        assert auction.initial_price == 300
        assert auction.highest_bid == 1200

    @pytest.mark.asyncio
    async def test_leaves_auction_info_unset_for_a_normal_listing(self):
        api, _ = mercapi_returning("with_auction.json")

        page = await api.items_page("100000001", ("on_sale",), with_auction=True)

        assert page.items[1].auction_info is None

    @pytest.mark.asyncio
    async def test_keeps_an_unknown_auction_shape_distinguishable(self):
        api, _ = mercapi_returning("unknown_auction_shape.json")

        page = await api.items_page("100000001", ("on_sale",), with_auction=True)

        auction = page.items[0].auction_info
        assert (
            auction is not None
        ), "an unrecognised shape must not look like a normal listing"
        assert auction.id_ is None
        assert auction.highest_bid is None


class TestBackwardCompatibility:
    @pytest.mark.asyncio
    async def test_items_still_requests_all_statuses_without_a_cursor(self):
        api, requests = mercapi_returning("page_1_has_next.json")

        res = await api.items("100000001")

        params = requests[0].url.params
        assert params["status"] == "on_sale,trading,sold_out"
        assert params["limit"] == "30"
        assert "max_pager_id" not in params
        assert "with_auction" not in params
        assert len(res.items) == 2

    @pytest.mark.asyncio
    async def test_items_exposes_the_pager_id_of_each_item(self):
        api, _ = mercapi_returning("page_1_has_next.json")

        res = await api.items("100000001")

        assert [item.pager_id for item in res.items] == [9, 8]
