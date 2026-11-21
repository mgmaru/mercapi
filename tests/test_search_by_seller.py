"""Searching within one seller's listings.

The search request has always carried a `sellerId` list, sent empty. These
tests are about what is sent when it is not empty. Whether Mercari honours it
was observed separately (see `tests/fixtures/README.md`); nothing here reaches
Mercari.
"""

import json
from pathlib import Path

import httpx
import pytest

from mercapi import Mercapi
from mercapi.requests import SearchRequestData


FIXTURE = Path(__file__).parent / "fixtures" / "search" / "by_seller.json"


def mercapi_returning_the_fixture():
    requests: list[httpx.Request] = []
    body = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=body)

    api = Mercapi()
    api._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return api, requests


def sent_condition(request: httpx.Request) -> dict:
    return json.loads(request.content)["searchCondition"]


class TestRequestData:
    def test_no_seller_is_an_empty_list_as_before(self):
        conditions = SearchRequestData.SearchConditions(query="sharpnel")

        assert SearchRequestData(conditions).data["searchCondition"]["sellerId"] == []

    def test_sellers_are_sent_in_the_seller_list(self):
        conditions = SearchRequestData.SearchConditions(
            query="", seller_ids=["100000001", "100000002"]
        )

        assert SearchRequestData(conditions).data["searchCondition"]["sellerId"] == [
            "100000001",
            "100000002",
        ]

    def test_a_seller_given_as_a_number_is_sent_as_text(self):
        # The form that was observed to work. Every seller id Mercari returns
        # in a search result is text.
        conditions = SearchRequestData.SearchConditions(
            query="", seller_ids=[100000001]
        )

        assert SearchRequestData(conditions).data["searchCondition"]["sellerId"] == [
            "100000001"
        ]

    def test_positional_construction_still_means_what_it_meant(self):
        # `Mercapi.search` and callers written before `seller_ids` build the
        # conditions positionally. The new field goes last so none of them
        # shift.
        conditions = SearchRequestData.SearchConditions(
            "sharpnel", [75], [], [], 100, 500, [3], [], [], [], [], None, None, "cd"
        )

        assert conditions.exclude == "cd"
        assert conditions.seller_ids == []


class TestSearch:
    @pytest.mark.asyncio
    async def test_sends_the_seller(self):
        api, requests = mercapi_returning_the_fixture()

        await api.search("", seller_ids=["100000001"])

        assert sent_condition(requests[0])["sellerId"] == ["100000001"]

    @pytest.mark.asyncio
    async def test_sends_no_seller_unless_asked(self):
        api, requests = mercapi_returning_the_fixture()

        await api.search("sharpnel")

        assert sent_condition(requests[0])["sellerId"] == []

    @pytest.mark.asyncio
    async def test_an_empty_keyword_is_sent_as_it_is(self):
        # A seller's whole shelf, not the part of it that matches a word.
        api, requests = mercapi_returning_the_fixture()

        await api.search("", seller_ids=["100000001"])

        assert sent_condition(requests[0])["keyword"] == ""

    @pytest.mark.asyncio
    async def test_combines_with_the_other_conditions(self):
        api, requests = mercapi_returning_the_fixture()

        await api.search(
            "",
            seller_ids=["100000001"],
            status=[SearchRequestData.Status.STATUS_ON_SALE],
            sort_by=SearchRequestData.SortBy.SORT_CREATED_TIME,
            sort_order=SearchRequestData.SortOrder.ORDER_DESC,
        )

        condition = sent_condition(requests[0])
        assert condition["sellerId"] == ["100000001"]
        assert condition["status"] == ["STATUS_ON_SALE"]
        assert condition["sort"] == "SORT_CREATED_TIME"

    @pytest.mark.asyncio
    async def test_results_carry_the_seller_and_the_condition(self):
        api, _ = mercapi_returning_the_fixture()

        results = await api.search("", seller_ids=["100000001"])

        assert [item.seller_id for item in results.items] == ["100000001"] * 2
        assert [item.item_condition_id for item in results.items] == [1, 3]

    @pytest.mark.asyncio
    async def test_the_next_page_keeps_the_seller(self):
        api, requests = mercapi_returning_the_fixture()
        results = await api.search("", seller_ids=["100000001"])
        results.meta.next_page_token = "cursor-page-2"

        await results.next_page()

        assert sent_condition(requests[1])["sellerId"] == ["100000001"]
        assert json.loads(requests[1].content)["pageToken"] == "cursor-page-2"
