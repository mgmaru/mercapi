# Test fixtures

Hand written JSON used by tests that replace the HTTP layer with
`httpx.MockTransport`. These files are **not** recorded traffic: they carry the
observed response shape with masked values only.

Rules

- No raw response, request header, DPoP token or cookie
- No real item id, seller name, item title or image URL
- One fixture, one behaviour under test
- Response bodies are hand written from an observed shape, never invented

## Provenance

| Fixture | Kind | Derived from | Observed | Behaviour under test |
|---|---|---|---|---|
| `seller_items/page_1_has_next.json` | observed | — | 2026-08-31 | `has_next=true` carries the last `pager_id` as the next cursor |
| `seller_items/page_2_end.json` | derived | `page_1_has_next.json` | 2026-08-31 | `has_next=false` returns no cursor |
| `seller_items/empty_end.json` | derived | `page_1_has_next.json` | 2026-08-31 | empty page with `has_next=false` is a normal end |
| `seller_items/empty_has_next.json` | derived | `page_1_has_next.json` | 2026-08-31 | empty page with `has_next=true` is a parse error |
| `seller_items/missing_last_pager_id.json` | derived | `page_1_has_next.json` | 2026-08-31 | missing trailing `pager_id` is a parse error |
| `seller_items/with_auction.json` | observed | — | 2026-08-31 | `auction_info` is present only on auction listings |
| `seller_items/unknown_auction_shape.json` | derived | `with_auction.json` | 2026-08-31 | an unrecognised `auction_info` shape is preserved, not dropped |
| `item/auction.json` | observed | — | 2026-08-31 | every `auction_info` property of an auction listing is parsed |
| `item/fixed_price.json` | observed | — | 2026-08-31 | a listing without `auction_info` leaves the model unset |
| `item/auction_info_null.json` | derived | `item/fixed_price.json` | 2026-08-31 | a null `auction_info` leaves the model unset |
| `item/auction_info_empty.json` | derived | `item/auction.json` | 2026-08-31 | an empty `auction_info` is preserved, not dropped |
| `item/auction_info_unknown_shape.json` | derived | `item/auction.json` | 2026-08-31 | an unrecognised `auction_info` shape is preserved, not dropped |
| `item/auction_info_partial.json` | derived | `item/auction.json` | 2026-08-31 | the properties that could be read survive a partial shape |
| `item/seller_inactive.json` | observed | — | 2026-09-04 | `seller.is_inactive` is parsed when Mercari sets it |
| `item/seller_active.json` | derived | `item/seller_inactive.json` | 2026-09-04 | `false` is an answer and survives as `False` |
| `item/seller_without_is_inactive.json` | derived | `item/seller_inactive.json` | 2026-09-04 | an absent flag is `None`, never `False` |
| `search/by_seller.json` | observed | — | 2026-11-20 | a search limited to one seller returns that seller's listings, each with `itemConditionId` |

`observed` fixtures follow a response shape recorded during the Card Digger
auction validation on 2026-08-31 against upstream commit
`20ba68fd42677997c4c91b4e4eb17c1e7e387efa`, except
`item/seller_inactive.json`, whose shape comes from the Card Digger
`is_inactive` observation of 2026-09-04 (139 item detail responses, all of
which carried `seller.is_inactive`). `derived` fixtures change only the
values or the presence of a field of an observed fixture; no field name, nesting
or type was invented. There is no `assumed` fixture.

`search/by_seller.json` follows the search result shape recorded on 2026-08-31
and the Card Digger seller condition observation of 2026-11-20: one seller,
`sellerId` sent as text with an empty keyword. Every listing returned was that
seller's (117 of 117 on sale, 43 of 43 sold or trading) and every one carried
`itemConditionId`. The 30 listings `GET /items/get_items` returned for each
status were all among them. One seller, one run: it shows the filter is
honoured, not how it behaves for every seller.

## Shapes

`POST /v2/entities:search` takes the sellers to search within as
`searchCondition.sellerId`, a list of text ids. A seller item from
`GET /items/get_items` carries no condition under any name (42 property names
observed on 2026-11-20 across 60 items, none of them a condition), so the search is the only
listing of a seller's shelf that says how worn each item is.

`GET /items/get_items` returns:

```text
{ "result": "OK",
  "meta": { "has_next": <bool> },
  "data": [ { "id", "seller", "status", "name", "price", "pager_id", ... } ] }
```

`auction_info` appears on a seller item only when the request carries
`with_auction=true`, and only for auction listings:

```text
{ "id", "bid_deadline", "total_bid", "initial_price", "highest_bid" }
```

`bid_deadline` is an ISO 8601 string. The other three are integers. This differs
from the item detail endpoint, which uses `total_bids`, `state`, `auction_type`
and `expected_end_time`.

`GET /items/get` returns the listing under `data`, and carries `auction_info`
only for an auction listing requested with `include_auction=true`:

```text
{ "id", "start_time", "total_bids", "initial_price", "highest_bid",
  "state", "auction_type", "expected_end_time" }
```

`start_time` and `expected_end_time` are epoch seconds, `state` and
`auction_type` are tokens such as `STATE_ONGOING` and `AUCTION_TYPE_NORMAL`.

The `seller` object of `GET /items/get` carries 18 properties, of which this
model reads 17. `is_inactive` is a boolean and is present on every response
observed so far; `region_code` is the one still unread.

```text
{ "id", "name", "created", "num_sell_items", "num_ratings", "ratings",
  "score", "star_rating_score", "is_official", "quick_shipper",
  "is_followable", "is_blocked", "is_inactive", "region_code",
  "photo_url", "photo_thumbnail_url", "register_sms_confirmation",
  "register_sms_confirmation_at" }
```

`GET /users/get_profile` does **not** carry `is_inactive`. It was looked for
across all 37 of that response's properties and is not among them.
