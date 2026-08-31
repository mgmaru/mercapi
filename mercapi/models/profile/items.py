from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from mercapi.models import Item
from mercapi.models.base import ResponseModel
from mercapi.models.common import ItemCategorySummary
from mercapi.models.item.data import ShippingFromArea


@dataclass
class SellerItemAuctionInfo(ResponseModel):
    """Auction properties of a seller item listing.

    Only returned when the seller items request carries ``with_auction=true``,
    and only for auction listings. The shape differs from the item detail
    endpoint, which uses ``total_bids``, ``state`` and ``expected_end_time``.

    Every property is optional so an unrecognised shape is preserved rather than
    silently reported as a normal listing.
    """

    id_: Optional[str] = None
    bid_deadline: Optional[str] = None
    total_bid: Optional[int] = None
    initial_price: Optional[int] = None
    highest_bid: Optional[int] = None


@dataclass
class SellerItem(ResponseModel):
    id_: str
    seller_id: str
    status: str
    name: str
    price: int
    thumbnails: List[str]
    root_category_id: int
    num_likes: int
    num_comments: int
    created: datetime
    updated: datetime
    item_category: Optional[ItemCategorySummary]
    shipping_from_area: ShippingFromArea
    pager_id: Optional[int] = None
    auction_info: Optional[SellerItemAuctionInfo] = None

    async def full_item(self) -> Item:
        """Fetch full details of a listing (item).

        Equivalent of :func:`~mercapi.Mercapi.item`
        """
        return await self._mercapi.item(self.id_)


@dataclass
class Items(ResponseModel):
    items: List[SellerItem]


@dataclass
class SellerItemsPage(ResponseModel):
    """One page of seller items, with the cursor needed for the next page.

    ``next_max_pager_id`` is never guessed. It is the ``pager_id`` of the last
    item of this page, and only when the response reports another page.
    """

    items: List[SellerItem]
    has_next: bool
    next_max_pager_id: Optional[int] = None
