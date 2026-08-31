from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from mercapi.models.base import ResponseModel


@dataclass
class Seller(ResponseModel):
    @dataclass
    class Ratings(ResponseModel):
        good: int
        normal: int
        bad: int

    id_: int
    name: str
    photo: str
    photo_thumbnail: str
    register_sms_confirmation: str
    register_sms_confirmation_at: datetime
    created: datetime
    num_sell_items: int
    ratings: Ratings
    num_ratings: int
    score: int
    is_official: bool
    quick_shipper: bool
    star_rating_score: int
    is_followable: bool
    is_blocked: bool


@dataclass
class ItemCondition(ResponseModel):
    id_: int
    name: str
    subname: str


@dataclass
class Color(ResponseModel):
    id_: int
    name: str
    rgb: int

    @property
    def rgb_code(self) -> str:
        return hex(self.rgb)


@dataclass
class ShippingPayer(ResponseModel):
    id_: int
    name: str
    code: str


@dataclass
class ShippingMethod(ResponseModel):
    id_: int
    name: str
    is_deprecated: str


@dataclass
class ShippingFromArea(ResponseModel):
    id_: int
    name: str


@dataclass
class ShippingDuration(ResponseModel):
    id_: int
    name: str
    min_days: int
    max_days: int


@dataclass
class ShippingClass(ResponseModel):
    id_: int
    fee: int
    icon_id: int
    pickup_fee: int
    shipping_fee: int
    total_fee: int
    is_pickup: bool


@dataclass
class Comment(ResponseModel):
    @dataclass
    class User(ResponseModel):
        id_: int
        name: str
        photo: str
        photo_thumbnail: str

    id_: int
    message: str
    user: User
    created: datetime


@dataclass
class Requester(ResponseModel):
    created: datetime


@dataclass
class ItemSize(ResponseModel):
    id_: int
    name: str


@dataclass
class ItemBrand(ResponseModel):
    id_: int
    name: str
    sub_name: str


@dataclass
class ItemAttributeValue(ResponseModel):
    id_: str
    text: str


@dataclass
class ItemAttribute(ResponseModel):
    id_: str
    text: str
    values: list
    deep_facet_filterable: bool
    show_on_ui: bool


@dataclass
class PromotionInstallment(ResponseModel):
    message: str
    campaign_message: str
    campaign_url: str


@dataclass
class Defpay(ResponseModel):
    calculated_price: int
    is_easypay_heavy_user: bool
    has_ever_used_installment_payment: bool
    installment_monthly_amount: int
    installment_times: int
    promotion_installment: PromotionInstallment


@dataclass
class PromotionInfo(ResponseModel):
    label_text: str
    supplementary_text: str


@dataclass
class PricePromotionAreaDetails(ResponseModel):
    promotion_type: str
    promotion_info: list


@dataclass
class EstimateInfo(ResponseModel):
    total_rate: int
    mercard_estimate_reward: int
    estimate_reward_text: str
    disclaimer_text: str
    lp_url: str


@dataclass
class ParentCategoryNtier(ResponseModel):
    id_: int
    name: str
    display_order: int


@dataclass
class AuctionInfo(ResponseModel):
    """Auction properties of an item detail listing.

    Only returned for auction listings, and only when the request carries
    ``include_auction=true``. The shape differs from the seller items endpoint,
    which uses ``total_bid`` and ``bid_deadline``.

    Every property is optional so an unrecognised shape is preserved rather than
    silently reported as a normal listing. A required property that cannot be
    read is not an error here: the mapper reports it on the log and leaves the
    whole model unset, which is indistinguishable from an ordinary listing that
    carries no auction at all.
    """

    id_: Optional[str] = None
    start_time: Optional[datetime] = None
    total_bids: Optional[int] = None
    initial_price: Optional[int] = None
    highest_bid: Optional[int] = None
    state: Optional[str] = None
    auction_type: Optional[str] = None
    expected_end_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    winner_id: Optional[str] = None
    expected_winner_period_end_time: Optional[datetime] = None
