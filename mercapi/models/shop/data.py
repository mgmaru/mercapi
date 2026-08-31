"""
Data models for Mercari Shop products.

This module contains all the data models specific to Mercari Shop listings,
which are business/commercial seller listings with additional features
compared to regular personal seller listings.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from mercapi.models.base import ResponseModel
from mercapi.models.common import ItemCategorySummary
from mercapi.models.item.data import (
    ItemCondition,
    ShippingMethod,
    ShippingDuration,
    ShippingFromArea,
    ShippingPayer,
    ItemBrand,
)


@dataclass
class ShopStats(ResponseModel):
    """Shop statistics including rating and review count."""

    shop_id: str
    """Shop identifier"""

    score: int
    """Shop rating score (1-5 stars)"""

    review_count: str
    """Number of reviews the shop has received"""


@dataclass
class ShopItemSummary(ResponseModel):
    """Summary information for other products from the same shop."""

    product_id: str
    """Product ID"""

    display_name: str
    """Product display name"""

    product_tags: List[str]
    """Product tags"""

    thumbnail: str
    """Thumbnail image URL"""

    price: str
    """Product price in yen"""


@dataclass
class ShopBadge(ResponseModel):
    badge_type: str
    badge_name: Optional[str] = None
    status: Optional[str] = None


@dataclass
class ShopDetail(ResponseModel):
    """Complete shop information including stats, badges, and other products."""

    name: str
    """Internal shop name/ID"""

    display_name: str
    """Shop display name"""

    thumbnail: str
    """Shop logo/thumbnail URL"""

    shop_stats: ShopStats
    """Shop statistics (rating, review count)"""

    allow_direct_message: bool
    """Whether direct messaging to the shop is allowed"""

    shop_items: List[ShopItemSummary]
    """Other products from this shop"""

    is_inbound_xb: bool
    """Cross-border inbound status"""

    badges: List[ShopBadge]
    """Shop badges and certifications"""

    has_approved_brand_screening: bool
    """Whether shop has passed brand screening"""

    always_show_stock: Optional[bool] = None
    """Whether stock is always shown"""


@dataclass
class ShopProductCategory(ResponseModel):
    category_id: str
    display_name: str
    parent_id: str
    root_id: str
    has_child: bool


@dataclass
class ShopProductBrand(ResponseModel):
    brand_id: str
    display_name: str


@dataclass
class ShopProductCondition(ResponseModel):
    display_name: str


@dataclass
class ShopProductShippingMethod(ResponseModel):
    shipping_method_id: str
    display_name: str
    is_anonymous: bool


@dataclass
class ShopProductShippingPayer(ResponseModel):
    shipping_payer_id: str
    display_name: str
    code: str


@dataclass
class ShopProductShippingDuration(ResponseModel):
    shipping_duration_id: str
    display_name: str
    min_days: int
    max_days: int


@dataclass
class ShopProductShippingFromArea(ResponseModel):
    shipping_area_code: str
    display_name: str


@dataclass
class PromotionAction(ResponseModel):
    """Detailed promotion action information including discount details."""

    action: str
    """Action type (e.g., 'Shop follow')"""

    discount_type: str
    """Type of discount (e.g., 'RATE' for percentage)"""

    discount_value: str
    """Discount value (percentage or amount)"""

    return_type: str
    """Return type for the promotion"""

    coupon_type: str
    """Type of coupon (e.g., 'COUPON_TYPE_SHOPS_BUYER_COUPON')"""

    max_return_amount: str
    """Maximum return amount in yen"""

    return_text: str
    """Return text description"""

    discount_amount: str
    """Actual discount amount in yen"""

    discounted_price: str
    """Final price after discount in yen"""


@dataclass
class Promotion(ResponseModel):
    """Product promotion information."""

    display_name: str
    """Promotion display name/description"""

    action: PromotionAction
    """Detailed promotion action information"""


@dataclass
class ProductStats(ResponseModel):
    """Product statistics including likes and reviews."""

    product_id: str
    """Product identifier"""

    score: int
    """Product score/rating"""

    review_count: int
    """Number of reviews"""

    likes_count: int
    """Number of likes"""


@dataclass
class TimeSaleDetails(ResponseModel):
    """Time-limited sale information including discount percentage and pricing."""

    name: str
    """Sale identifier/name"""

    percentage: int
    """Discount percentage"""

    price: str
    """Sale price in yen"""

    start_time: str
    """Sale start time (ISO 8601 format)"""

    end_time: str
    """Sale end time (ISO 8601 format)"""

    base: str
    """Base price type (e.g., 'STABLE_PRICE')"""

    calculation_start_time: str
    """Price calculation start time (ISO 8601 format)"""

    calculation_end_time: str
    """Price calculation end time (ISO 8601 format)"""


@dataclass
class ProductVariant(ResponseModel):
    """Product variant (size, color, etc.) with quantity information."""

    variant_id: str
    """Variant identifier"""

    display_name: str
    """Variant display name"""

    quantity: str
    """Available quantity for this variant"""

    size: str
    """Size information"""

    attributes: List[dict]
    """Additional variant attributes"""


@dataclass
class ShippingFeeConfig(ResponseModel):
    fee_type: str
    base_fee: Optional[str] = None
    additional_fee: Optional[str] = None


@dataclass
class VariationGrouping(ResponseModel):
    group_id: str
    group_name: str
    variations: List[dict]


@dataclass
class BuyerPromotion(ResponseModel):
    promotion_id: str
    promotion_type: str
    discount_value: str


@dataclass
class FollowPromotion(ResponseModel):
    display_name: str
    action: PromotionAction


@dataclass
class RealCardReward(ResponseModel):
    reward_amount: str
    has_active_card: bool
    has_mvno: bool
    reward_rate: float
    lp_uri: str
    estimate_reward_text: str
    disclaimer_text: str
    show_component: bool


@dataclass
class MercardCampaign(ResponseModel):
    id_: str
    title: str
    uri: str
    text: str
    discount_amount: int
    max_discount: int


@dataclass
class SeoMetadata(ResponseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None


@dataclass
class ProductPreOrder(ResponseModel):
    is_pre_order: bool
    expected_ship_date: Optional[str] = None


@dataclass
class ShopProductDetail(ResponseModel):
    """
    Comprehensive product details for a shop listing.

    This model contains all the detailed information about a shop product,
    including shop information, shipping details, promotions, variants, and more.
    """

    shop: ShopDetail
    """Complete shop information"""

    photos: List[str]
    """Product photo URLs"""

    description: str
    """Product description"""

    categories: List[ShopProductCategory]
    """Product categories (hierarchical)"""

    brand: Optional[ShopProductBrand]
    """Brand information (if available)"""

    condition: ShopProductCondition
    """Item condition"""

    shipping_method: ShopProductShippingMethod
    """Shipping method details"""

    shipping_payer: ShopProductShippingPayer
    """Who pays for shipping"""

    shipping_duration: ShopProductShippingDuration
    """Estimated delivery time"""

    shipping_from_area: ShopProductShippingFromArea
    """Shipping origin location"""

    promotions: List[Promotion]
    """Active promotions"""

    product_stats: Optional[ProductStats]
    """Product statistics (views, likes)"""

    time_sale_details: Optional[TimeSaleDetails]
    """Limited-time sale information"""

    variants: List[ProductVariant]
    """Product variants (size, color, etc.)"""

    shipping_fee_config: Optional[ShippingFeeConfig]
    """Shipping fee configuration"""

    variation_grouping: Optional[VariationGrouping]
    """Variation groupings"""

    buyer_promotion: Optional[BuyerPromotion]
    """Buyer-specific promotions"""

    follow_promotion: Optional[FollowPromotion]
    """Follow-based promotions"""

    last_purchased_date_time: Optional[str]
    """Last purchase timestamp"""

    real_card_reward: Optional[RealCardReward]
    """Mercard (Mercari credit card) reward information"""

    mercard_campaign: Optional[MercardCampaign]
    """Mercard campaign details"""

    seo_metadata: Optional[SeoMetadata]
    """SEO metadata"""

    product_pre_order: Optional[ProductPreOrder]
    """Pre-order information"""
