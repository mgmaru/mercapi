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
    id_: str
    start_time: datetime
    total_bids: int
    initial_price: int
    highest_bid: int
    state: str
    auction_type: str
    expected_end_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    winner_id: Optional[str] = None
    expected_winner_period_end_time: Optional[datetime] = None
