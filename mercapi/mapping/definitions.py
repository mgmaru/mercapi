import logging
from datetime import datetime
from typing import NamedTuple, List, Dict, TypeVar, Type, Any, Optional, Callable

from mercapi.models import Item, Items, Profile, SearchResults, SearchResultItem
from mercapi.models.profile import (
    SellerItem,
    SellerItemAuctionInfo,
    SellerItemsPage,
)
from mercapi.models.common import ItemCategory, ItemCategorySummary
from mercapi.models.search import PhotoUri, Auction, Shop
from mercapi.models.shop import (
    ShopProduct,
    ShopStats,
    ShopItemSummary,
    ShopBadge,
    ShopDetail,
    ShopProductCategory,
    ShopProductBrand,
    ShopProductCondition,
    ShopProductShippingMethod,
    ShopProductShippingPayer,
    ShopProductShippingDuration,
    ShopProductShippingFromArea,
    PromotionAction,
    Promotion,
    ProductStats,
    TimeSaleDetails,
    ProductVariant,
    ShippingFeeConfig,
    VariationGrouping,
    BuyerPromotion,
    FollowPromotion,
    RealCardReward,
    MercardCampaign,
    SeoMetadata,
    ProductPreOrder,
    ShopProductDetail,
)
from mercapi.models.item.data import (
    Seller,
    ItemCondition,
    Color,
    ShippingPayer,
    ShippingMethod,
    ShippingFromArea,
    ShippingDuration,
    ShippingClass,
    Comment,
    Requester,
    ItemSize,
    ItemBrand,
    ItemAttribute,
    ItemAttributeValue,
    Defpay,
    PromotionInstallment,
    PricePromotionAreaDetails,
    PromotionInfo,
    EstimateInfo,
    ParentCategoryNtier,
    AuctionInfo,
)
from mercapi.util.errors import ParseAPIResponseError
from mercapi.models.base import ResponseModel
from mercapi.models.profile.items import SellerItem
from mercapi.models.search import Meta

T = TypeVar("T")
ExtractorDef = Callable[[dict], Optional[T]]


class ResponseProperty(NamedTuple):
    raw_property_name: str
    model_property_name: str
    extractor: ExtractorDef


class ResponseMappingDefinition(NamedTuple):
    required_properties: List[ResponseProperty]
    optional_properties: List[ResponseProperty]


class Extractors:
    """
    Collection of HOFs for parsing API responses in the most common ways.

    Each extractor function MUST handle lack of requested key
    in the response object (dict) and return None in such cases.
    """

    @staticmethod
    def get(key: str) -> ExtractorDef[Any]:
        return lambda x: x.get(key)

    S = TypeVar("S", int, float, str)

    @staticmethod
    def get_as(key: str, type_: Type[S]) -> ExtractorDef[S]:
        return lambda x: type_(x[key]) if key in x else None

    M = TypeVar("M", bound=ResponseModel)

    @staticmethod
    def get_as_model(
        key: str, model: Type[M], map_def: Optional[ResponseMappingDefinition] = None
    ) -> ExtractorDef[M]:
        if type(model) == str:
            model = Extractors.__import_class(model)
        return (
            lambda x: map_to_class(x[key], model, map_def)
            if key in x and x[key] is not None
            else None
        )

    @staticmethod
    def get_with(key: str, mapper: Callable[[S], T]) -> ExtractorDef[T]:
        return lambda x: mapper(x[key]) if key in x else None

    @staticmethod
    def get_list_with(key: str, mapper: Callable[[Any], T]) -> ExtractorDef[List[T]]:
        return lambda x: [mapper(i) for i in x[key]] if key in x else None

    @staticmethod
    def get_list_of_model(key: str, model: Type[M]) -> ExtractorDef[List[M]]:
        if type(model) == str:
            model = Extractors.__import_class(model)
        return (
            lambda x: [map_to_class(i, model) for i in x[key]]
            if key in x and x[key] is not None
            else None
        )

    @staticmethod
    def get_datetime(key: str) -> ExtractorDef[datetime]:
        return Extractors.get_with(key, lambda x: datetime.fromtimestamp(float(x)))

    @staticmethod
    def get_either(*keys: str) -> ExtractorDef[Any]:
        """Try multiple keys in order, return first non-None value"""

        def extractor(x):
            for key in keys:
                if key in x and x[key] is not None:
                    return x[key]
            return None

        return extractor

    @staticmethod
    def __import_class(model: str) -> Type[ResponseModel]:
        import importlib

        module_name, class_name = model.rsplit(".", 1)
        return getattr(importlib.import_module(module_name), class_name)


def _extract_has_next(response: dict) -> Optional[bool]:
    """Read ``meta.has_next``.

    Returns ``None`` when the field is missing so the caller reports a parse
    error instead of quietly treating the page as the last one.
    """
    meta = response.get("meta")
    if not isinstance(meta, dict) or "has_next" not in meta:
        return None
    return bool(meta["has_next"])


R = ResponseMappingDefinition

mapping_definitions: Dict[Type[ResponseModel], ResponseMappingDefinition] = {
    Item: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("status", "status", Extractors.get("status")),
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty("price", "price", Extractors.get("price")),
        ],
        optional_properties=[
            ResponseProperty(
                "seller", "seller", Extractors.get_as_model("seller", Seller)
            ),
            ResponseProperty(
                "description", "description", Extractors.get("description")
            ),
            ResponseProperty("photos", "photos", Extractors.get("photos")),
            ResponseProperty(
                "photo_paths", "photo_paths", Extractors.get("photo_paths")
            ),
            ResponseProperty("thumbnails", "thumbnails", Extractors.get("thumbnails")),
            ResponseProperty(
                "item_category",
                "item_category",
                Extractors.get_as_model("item_category", ItemCategorySummary),
            ),
            ResponseProperty(
                "item_condition",
                "item_condition",
                Extractors.get_as_model("item_condition", ItemCondition),
            ),
            ResponseProperty(
                "colors",
                "colors",
                Extractors.get_list_of_model("colors", Color),
            ),
            ResponseProperty(
                "shipping_payer",
                "shipping_payer",
                Extractors.get_as_model("shipping_payer", ShippingPayer),
            ),
            ResponseProperty(
                "shipping_method",
                "shipping_method",
                Extractors.get_as_model("shipping_method", ShippingMethod),
            ),
            ResponseProperty(
                "shipping_from_area",
                "shipping_from_area",
                Extractors.get_as_model("shipping_from_area", ShippingFromArea),
            ),
            ResponseProperty(
                "shipping_duration",
                "shipping_duration",
                Extractors.get_as_model("shipping_duration", ShippingDuration),
            ),
            ResponseProperty(
                "shipping_class",
                "shipping_class",
                Extractors.get_as_model("shipping_class", ShippingClass),
            ),
            ResponseProperty("num_likes", "num_likes", Extractors.get("num_likes")),
            ResponseProperty(
                "num_comments", "num_comments", Extractors.get("num_comments")
            ),
            ResponseProperty(
                "comments",
                "comments",
                Extractors.get_list_of_model("comments", Comment),
            ),
            ResponseProperty("updated", "updated", Extractors.get_datetime("updated")),
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
            ResponseProperty("pager_id", "pager_id", Extractors.get("pager_id")),
            ResponseProperty("liked", "liked", Extractors.get("liked")),
            ResponseProperty("checksum", "checksum", Extractors.get("checksum")),
            ResponseProperty(
                "is_dynamic_shipping_fee",
                "is_dynamic_shipping_fee",
                Extractors.get("is_dynamic_shipping_fee"),
            ),
            # unknown schema:
            ResponseProperty(
                "application_attributes",
                "application_attributes",
                Extractors.get("application_attributes"),
            ),
            ResponseProperty(
                "is_shop_item", "is_shop_item", Extractors.get("is_shop_item")
            ),
            ResponseProperty(
                "is_anonymous_shipping",
                "is_anonymous_shipping",
                Extractors.get("is_anonymous_shipping"),
            ),
            ResponseProperty(
                "is_web_visible", "is_web_visible", Extractors.get("is_web_visible")
            ),
            ResponseProperty(
                "is_offerable", "is_offerable", Extractors.get("is_offerable")
            ),
            ResponseProperty(
                "is_organizational_user",
                "is_organizational_user",
                Extractors.get("is_organizational_user"),
            ),
            ResponseProperty(
                "organizational_user_status",
                "organizational_user_status",
                Extractors.get("organizational_user_status"),
            ),
            ResponseProperty(
                "is_stock_item", "is_stock_item", Extractors.get("is_stock_item")
            ),
            ResponseProperty(
                "is_cancelable", "is_cancelable", Extractors.get("is_cancelable")
            ),
            ResponseProperty(
                "shipped_by_worker",
                "shipped_by_worker",
                Extractors.get("shipped_by_worker"),
            ),
            ResponseProperty(
                "additional_services",
                "additional_services",
                Extractors.get("additional_services"),
            ),
            ResponseProperty(
                "has_additional_service",
                "has_additional_service",
                Extractors.get("has_additional_service"),
            ),
            ResponseProperty(
                "has_like_list", "has_like_list", Extractors.get("has_like_list")
            ),
            ResponseProperty(
                "is_offerable_v2", "is_offerable_v2", Extractors.get("is_offerable_v2")
            ),
            ResponseProperty(
                "requester",
                "requester",
                Extractors.get_as_model("requester", Requester),
            ),
            ResponseProperty(
                "item_size", "item_size", Extractors.get_as_model("item_size", ItemSize)
            ),
            ResponseProperty(
                "item_brand",
                "item_brand",
                Extractors.get_as_model("item_brand", ItemBrand),
            ),
            ResponseProperty(
                "item_category_ntiers",
                "item_category_ntiers",
                Extractors.get_as_model("item_category_ntiers", ItemCategorySummary),
            ),
            ResponseProperty(
                "parent_categories_ntiers",
                "parent_categories_ntiers",
                Extractors.get_list_of_model(
                    "parent_categories_ntiers", ParentCategoryNtier
                ),
            ),
            ResponseProperty(
                "registered_prices_count",
                "registered_prices_count",
                Extractors.get("registered_prices_count"),
            ),
            ResponseProperty(
                "promotion_explanation_message",
                "promotion_explanation_message",
                Extractors.get("promotion_explanation_message"),
            ),
            ResponseProperty("hash_tags", "hash_tags", Extractors.get("hash_tags")),
            ResponseProperty(
                "item_attributes",
                "item_attributes",
                Extractors.get_list_of_model("item_attributes", ItemAttribute),
            ),
            ResponseProperty(
                "is_dismissed", "is_dismissed", Extractors.get("is_dismissed")
            ),
            ResponseProperty(
                "photo_descriptions",
                "photo_descriptions",
                Extractors.get("photo_descriptions"),
            ),
            ResponseProperty(
                "has_active_mercard",
                "has_active_mercard",
                Extractors.get("has_active_mercard"),
            ),
            ResponseProperty(
                "defpay", "defpay", Extractors.get_as_model("defpay", Defpay)
            ),
            ResponseProperty("meta_title", "meta_title", Extractors.get("meta_title")),
            ResponseProperty(
                "meta_subtitle", "meta_subtitle", Extractors.get("meta_subtitle")
            ),
            ResponseProperty(
                "price_promotion_area_details",
                "price_promotion_area_details",
                Extractors.get_as_model(
                    "price_promotion_area_details", PricePromotionAreaDetails
                ),
            ),
            ResponseProperty(
                "estimate_info",
                "estimate_info",
                Extractors.get_as_model("estimate_info", EstimateInfo),
            ),
            ResponseProperty(
                "auction_info",
                "auction_info",
                Extractors.get_as_model("auction_info", AuctionInfo),
            ),
        ],
    ),
    AuctionInfo: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty(
                "start_time", "start_time", Extractors.get_datetime("start_time")
            ),
            ResponseProperty(
                "total_bids", "total_bids", Extractors.get_as("total_bids", int)
            ),
            ResponseProperty(
                "initial_price",
                "initial_price",
                Extractors.get_as("initial_price", int),
            ),
            ResponseProperty(
                "highest_bid", "highest_bid", Extractors.get_as("highest_bid", int)
            ),
            ResponseProperty("state", "state", Extractors.get("state")),
            ResponseProperty(
                "auction_type", "auction_type", Extractors.get("auction_type")
            ),
        ],
        optional_properties=[
            ResponseProperty(
                "expected_end_time",
                "expected_end_time",
                Extractors.get_datetime("expected_end_time"),
            ),
            ResponseProperty(
                "finish_time", "finish_time", Extractors.get_datetime("finish_time")
            ),
            ResponseProperty("winner_id", "winner_id", Extractors.get("winner_id")),
            ResponseProperty(
                "expected_winner_period_end_time",
                "expected_winner_period_end_time",
                Extractors.get_datetime("expected_winner_period_end_time"),
            ),
        ],
    ),
    Seller: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty("photo_url", "photo", Extractors.get("photo_url")),
            ResponseProperty(
                "photo_thumbnail_url",
                "photo_thumbnail",
                Extractors.get("photo_thumbnail_url"),
            ),
            ResponseProperty(
                "register_sms_confirmation",
                "register_sms_confirmation",
                Extractors.get("register_sms_confirmation"),
            ),
            ResponseProperty(
                "register_sms_confirmation_at",
                "register_sms_confirmation_at",
                Extractors.get_with(
                    "register_sms_confirmation_at",
                    lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"),
                ),
            ),
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
            ResponseProperty(
                "num_sell_items", "num_sell_items", Extractors.get("num_sell_items")
            ),
            ResponseProperty(
                "ratings",
                "ratings",
                Extractors.get_as_model("ratings", Seller.Ratings),
            ),
            ResponseProperty(
                "num_ratings", "num_ratings", Extractors.get("num_ratings")
            ),
            ResponseProperty("score", "score", Extractors.get("score")),
            ResponseProperty(
                "is_official", "is_official", Extractors.get("is_official")
            ),
            ResponseProperty(
                "quick_shipper", "quick_shipper", Extractors.get("quick_shipper")
            ),
            ResponseProperty(
                "star_rating_score",
                "star_rating_score",
                Extractors.get("star_rating_score"),
            ),
            ResponseProperty(
                "is_followable", "is_followable", Extractors.get("is_followable")
            ),
            ResponseProperty("is_blocked", "is_blocked", Extractors.get("is_blocked")),
        ],
    ),
    Seller.Ratings: R(
        required_properties=[
            ResponseProperty("good", "good", Extractors.get("good")),
            ResponseProperty("normal", "normal", Extractors.get("normal")),
            ResponseProperty("bad", "bad", Extractors.get("bad")),
        ],
        optional_properties=[],
    ),
    ItemCondition: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty("subname", "subname", Extractors.get("subname")),
        ],
    ),
    Color: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty(
                "rgb", "rgb", Extractors.get_with("rgb", lambda x: int(x[1:], 16))
            ),
        ],
        optional_properties=[],
    ),
    ShippingPayer: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty("code", "code", Extractors.get("code")),
        ],
    ),
    ShippingMethod: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty(
                "is_deprecated", "is_deprecated", Extractors.get("is_deprecated")
            ),
        ],
    ),
    ShippingFromArea: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[],
    ),
    ShippingDuration: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty("min_days", "min_days", Extractors.get("min_days")),
            ResponseProperty("max_days", "max_days", Extractors.get("max_days")),
        ],
        optional_properties=[],
    ),
    ShippingClass: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("fee", "fee", Extractors.get("fee")),
            ResponseProperty("icon_id", "icon_id", Extractors.get("icon_id")),
            ResponseProperty("pickup_fee", "pickup_fee", Extractors.get("pickup_fee")),
            ResponseProperty(
                "shipping_fee", "shipping_fee", Extractors.get("shipping_fee")
            ),
            ResponseProperty("total_fee", "total_fee", Extractors.get("total_fee")),
            ResponseProperty("is_pickup", "is_pickup", Extractors.get("is_pickup")),
        ],
        optional_properties=[],
    ),
    Comment: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("message", "message", Extractors.get("message")),
        ],
        optional_properties=[
            ResponseProperty(
                "user", "user", Extractors.get_as_model("user", Comment.User)
            ),
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
        ],
    ),
    Comment.User: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty("photo_url", "photo", Extractors.get("photo_url")),
            ResponseProperty(
                "photo_thumbnail_url",
                "photo_thumbnail",
                Extractors.get("photo_thumbnail_url"),
            ),
        ],
    ),
    Requester: R(
        required_properties=[
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
        ],
        optional_properties=[],
    ),
    ItemSize: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[],
    ),
    ItemBrand: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            # API inconsistency: search uses "subName" (camelCase), item details uses "sub_name" (snake_case)
            ResponseProperty(
                "subName|sub_name",
                "sub_name",
                Extractors.get_either("subName", "sub_name"),
            ),
        ],
    ),
    ItemAttributeValue: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("text", "text", Extractors.get("text")),
        ],
        optional_properties=[],
    ),
    ItemAttribute: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("text", "text", Extractors.get("text")),
            ResponseProperty("values", "values", Extractors.get("values")),
            ResponseProperty(
                "deep_facet_filterable",
                "deep_facet_filterable",
                Extractors.get("deep_facet_filterable"),
            ),
            ResponseProperty("show_on_ui", "show_on_ui", Extractors.get("show_on_ui")),
        ],
        optional_properties=[],
    ),
    PromotionInstallment: R(
        required_properties=[
            ResponseProperty("message", "message", Extractors.get("message")),
            ResponseProperty(
                "campaign_message",
                "campaign_message",
                Extractors.get("campaign_message"),
            ),
            ResponseProperty(
                "campaign_url", "campaign_url", Extractors.get("campaign_url")
            ),
        ],
        optional_properties=[],
    ),
    Defpay: R(
        required_properties=[
            ResponseProperty(
                "calculated_price",
                "calculated_price",
                Extractors.get("calculated_price"),
            ),
            ResponseProperty(
                "is_easypay_heavy_user",
                "is_easypay_heavy_user",
                Extractors.get("is_easypay_heavy_user"),
            ),
            ResponseProperty(
                "has_ever_used_installment_payment",
                "has_ever_used_installment_payment",
                Extractors.get("has_ever_used_installment_payment"),
            ),
            ResponseProperty(
                "installment_monthly_amount",
                "installment_monthly_amount",
                Extractors.get("installment_monthly_amount"),
            ),
            ResponseProperty(
                "installment_times",
                "installment_times",
                Extractors.get("installment_times"),
            ),
            ResponseProperty(
                "promotion_installment",
                "promotion_installment",
                Extractors.get_as_model("promotion_installment", PromotionInstallment),
            ),
        ],
        optional_properties=[],
    ),
    PromotionInfo: R(
        required_properties=[
            ResponseProperty("label_text", "label_text", Extractors.get("label_text")),
            ResponseProperty(
                "supplementary_text",
                "supplementary_text",
                Extractors.get("supplementary_text"),
            ),
        ],
        optional_properties=[],
    ),
    PricePromotionAreaDetails: R(
        required_properties=[
            ResponseProperty(
                "promotion_type", "promotion_type", Extractors.get("promotion_type")
            ),
            ResponseProperty(
                "promotion_info", "promotion_info", Extractors.get("promotion_info")
            ),
        ],
        optional_properties=[],
    ),
    EstimateInfo: R(
        required_properties=[
            ResponseProperty("total_rate", "total_rate", Extractors.get("total_rate")),
            ResponseProperty(
                "mercard_estimate_reward",
                "mercard_estimate_reward",
                Extractors.get("mercard_estimate_reward"),
            ),
            ResponseProperty(
                "estimate_reward_text",
                "estimate_reward_text",
                Extractors.get("estimate_reward_text"),
            ),
            ResponseProperty(
                "disclaimer_text", "disclaimer_text", Extractors.get("disclaimer_text")
            ),
            ResponseProperty("lp_url", "lp_url", Extractors.get("lp_url")),
        ],
        optional_properties=[],
    ),
    ParentCategoryNtier: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty(
                "display_order", "display_order", Extractors.get("display_order")
            ),
        ],
        optional_properties=[],
    ),
    Items: R(
        required_properties=[
            ResponseProperty(
                "data", "items", Extractors.get_list_of_model("data", SellerItem)
            ),
        ],
        optional_properties=[],
    ),
    SellerItem: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty(
                "seller",
                "seller_id",
                Extractors.get_with(
                    "seller", lambda x: str(x["id"]) if "id" in x else None
                ),
            ),
            ResponseProperty("status", "status", Extractors.get("status")),
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty("price", "price", Extractors.get("price")),
        ],
        optional_properties=[
            ResponseProperty("thumbnails", "thumbnails", Extractors.get("thumbnails")),
            ResponseProperty(
                "root_category_id",
                "root_category_id",
                Extractors.get("root_category_id"),
            ),
            ResponseProperty("num_likes", "num_likes", Extractors.get("num_likes")),
            ResponseProperty(
                "num_comments", "num_comments", Extractors.get("num_comments")
            ),
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
            ResponseProperty("updated", "updated", Extractors.get_datetime("updated")),
            ResponseProperty(
                "item_category",
                "item_category",
                Extractors.get_as_model("item_category", ItemCategorySummary),
            ),
            ResponseProperty(
                "shipping_from_area",
                "shipping_from_area",
                Extractors.get_as_model("shipping_from_area", ShippingFromArea),
            ),
            ResponseProperty("pager_id", "pager_id", Extractors.get("pager_id")),
            ResponseProperty(
                "auction_info",
                "auction_info",
                Extractors.get_as_model("auction_info", SellerItemAuctionInfo),
            ),
        ],
    ),
    SellerItemAuctionInfo: R(
        required_properties=[],
        optional_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty(
                "bid_deadline", "bid_deadline", Extractors.get("bid_deadline")
            ),
            ResponseProperty("total_bid", "total_bid", Extractors.get("total_bid")),
            ResponseProperty(
                "initial_price", "initial_price", Extractors.get("initial_price")
            ),
            ResponseProperty(
                "highest_bid", "highest_bid", Extractors.get("highest_bid")
            ),
        ],
    ),
    SellerItemsPage: R(
        required_properties=[
            ResponseProperty(
                "data", "items", Extractors.get_list_of_model("data", SellerItem)
            ),
            ResponseProperty("meta", "has_next", _extract_has_next),
        ],
        optional_properties=[],
    ),
    Profile: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty("photo_url", "photo_url", Extractors.get("photo_url")),
            ResponseProperty(
                "photo_thumbnail_url",
                "photo_thumbnail_url",
                Extractors.get("photo_thumbnail_url"),
            ),
            ResponseProperty(
                "register_sms_confirmation",
                "register_sms_confirmation",
                Extractors.get("register_sms_confirmation"),
            ),
            ResponseProperty(
                "ratings",
                "ratings",
                Extractors.get_as_model("ratings", Profile.Ratings),
            ),
            ResponseProperty(
                "polarized_ratings",
                "polarized_ratings",
                Extractors.get_as_model("polarized_ratings", Profile.PolarizedRatings),
            ),
            ResponseProperty(
                "num_ratings", "num_ratings", Extractors.get("num_ratings")
            ),
            ResponseProperty(
                "star_rating_score",
                "star_rating_score",
                Extractors.get("star_rating_score"),
            ),
            ResponseProperty(
                "is_followable", "is_followable", Extractors.get("is_followable")
            ),
            ResponseProperty("is_blocked", "is_blocked", Extractors.get("is_blocked")),
            ResponseProperty(
                "following_count", "following_count", Extractors.get("following_count")
            ),
            ResponseProperty(
                "follower_count", "follower_count", Extractors.get("follower_count")
            ),
            ResponseProperty("score", "score", Extractors.get("score")),
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
            ResponseProperty("proper", "proper", Extractors.get("proper")),
            ResponseProperty(
                "introduction", "introduction", Extractors.get("introduction")
            ),
            ResponseProperty(
                "is_official", "is_official", Extractors.get("is_official")
            ),
            ResponseProperty(
                "num_sell_items", "num_sell_items", Extractors.get("num_sell_items")
            ),
            ResponseProperty("num_ticket", "num_ticket", Extractors.get("num_ticket")),
            ResponseProperty(
                "bounce_mail_flag",
                "bounce_mail_flag",
                Extractors.get("bounce_mail_flag"),
            ),
            # useless without authorization context
            # ('is_following', 'is_following', Extractors.get('is_following'))
            ResponseProperty(
                "current_point", "current_point", Extractors.get("current_point")
            ),
            ResponseProperty(
                "current_sales", "current_sales", Extractors.get("current_sales")
            ),
            ResponseProperty(
                "is_organizational_user",
                "is_organizational_user",
                Extractors.get("is_organizational_user"),
            ),
        ],
    ),
    Profile.PolarizedRatings: R(
        required_properties=[
            ResponseProperty("good", "good", Extractors.get("good")),
            ResponseProperty("bad", "bad", Extractors.get("bad")),
        ],
        optional_properties=[],
    ),
    Profile.Ratings: R(
        required_properties=[
            ResponseProperty("good", "good", Extractors.get("good")),
            ResponseProperty("normal", "normal", Extractors.get("normal")),
            ResponseProperty("bad", "bad", Extractors.get("bad")),
        ],
        optional_properties=[],
    ),
    SearchResults: R(
        required_properties=[
            ResponseProperty("meta", "meta", Extractors.get_as_model("meta", Meta)),
            ResponseProperty(
                "items",
                "items",
                Extractors.get_list_of_model("items", SearchResultItem),
            ),
        ],
        optional_properties=[],
    ),
    Meta: R(
        required_properties=[
            ResponseProperty(
                "nextPageToken", "next_page_token", Extractors.get("nextPageToken")
            ),
            ResponseProperty(
                "previousPageToken",
                "prev_page_token",
                Extractors.get("previousPageToken"),
            ),
            ResponseProperty(
                "numFound", "num_found", Extractors.get_as("numFound", int)
            ),
        ],
        optional_properties=[],
    ),
    PhotoUri: R(
        required_properties=[
            ResponseProperty("uri", "uri", Extractors.get("uri")),
        ],
        optional_properties=[],
    ),
    Auction: R(
        required_properties=[],
        optional_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty(
                "bidDeadline", "bid_deadline", Extractors.get("bidDeadline")
            ),
            ResponseProperty("totalBid", "total_bid", Extractors.get("totalBid")),
            ResponseProperty("highestBid", "highest_bid", Extractors.get("highestBid")),
        ],
    ),
    Shop: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
        ],
        optional_properties=[
            ResponseProperty(
                "display_name", "display_name", Extractors.get("display_name")
            ),
            ResponseProperty("thumbnail", "thumbnail", Extractors.get("thumbnail")),
        ],
    ),
    SearchResultItem: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty("price", "price", Extractors.get_as("price", int)),
        ],
        optional_properties=[
            ResponseProperty("sellerId", "seller_id", Extractors.get("sellerId")),
            ResponseProperty("status", "status", Extractors.get("status")),
            ResponseProperty("created", "created", Extractors.get_datetime("created")),
            ResponseProperty("updated", "updated", Extractors.get_datetime("updated")),
            ResponseProperty("thumbnails", "thumbnails", Extractors.get("thumbnails")),
            ResponseProperty("itemType", "item_type", Extractors.get("itemType")),
            ResponseProperty(
                "itemConditionId",
                "item_condition_id",
                Extractors.get_as("itemConditionId", int),
            ),
            ResponseProperty(
                "shippingPayerId",
                "shipping_payer_id",
                Extractors.get_as("shippingPayerId", int),
            ),
            ResponseProperty(
                "shippingMethodId",
                "shipping_method_id",
                Extractors.get_as("shippingMethodId", int),
            ),
            ResponseProperty(
                "categoryId",
                "category_id",
                Extractors.get_as("categoryId", int),
            ),
            ResponseProperty("isNoPrice", "is_no_price", Extractors.get("isNoPrice")),
            ResponseProperty("buyerId", "buyer_id", Extractors.get("buyerId")),
            ResponseProperty("title", "title", Extractors.get("title")),
            ResponseProperty("isLiked", "is_liked", Extractors.get("isLiked")),
            ResponseProperty(
                "itemSizes",
                "item_sizes",
                Extractors.get_list_of_model("itemSizes", ItemSize),
            ),
            ResponseProperty(
                "itemBrand",
                "item_brand",
                Extractors.get_as_model("itemBrand", ItemBrand),
            ),
            ResponseProperty(
                "itemPromotions", "item_promotions", Extractors.get("itemPromotions")
            ),
            ResponseProperty("shopName", "shop_name", Extractors.get("shopName")),
            ResponseProperty(
                "itemSize", "item_size", Extractors.get_as_model("itemSize", ItemSize)
            ),
            ResponseProperty(
                "photos", "photos", Extractors.get_list_of_model("photos", PhotoUri)
            ),
            ResponseProperty(
                "auction", "auction", Extractors.get_as_model("auction", Auction)
            ),
            ResponseProperty("shop", "shop", Extractors.get_as_model("shop", Shop)),
        ],
    ),
    ItemCategory: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty(
                "display_order", "display_order", Extractors.get("display_order")
            ),
            ResponseProperty("tab_order", "tab_order", Extractors.get("tab_order")),
            ResponseProperty(
                "parent_category_id",
                "parent_category_id",
                Extractors.get("parent_category_id"),
            ),
            ResponseProperty(
                "parent_category_name",
                "parent_category_name",
                Extractors.get("parent_category_name"),
            ),
            ResponseProperty(
                "root_category_id",
                "root_category_id",
                Extractors.get("root_category_id"),
            ),
            ResponseProperty(
                "root_category_name",
                "root_category_name",
                Extractors.get("root_category_name"),
            ),
            ResponseProperty(
                "size_group_id", "size_group_id", Extractors.get("size_group_id")
            ),
            ResponseProperty(
                "brand_group_id", "brand_group_id", Extractors.get("brand_group_id")
            ),
            ResponseProperty(
                "children",
                "children",
                Extractors.get_list_of_model("children", ItemCategory),
            ),
        ],
    ),
    ItemCategorySummary: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("name", "name", Extractors.get("name")),
        ],
        optional_properties=[
            ResponseProperty(
                "display_order", "display_order", Extractors.get("display_order")
            ),
            ResponseProperty(
                "parent_category_id",
                "parent_category_id",
                Extractors.get("parent_category_id"),
            ),
            ResponseProperty(
                "parent_category_name",
                "parent_category_name",
                Extractors.get("parent_category_name"),
            ),
            ResponseProperty(
                "root_category_id",
                "root_category_id",
                Extractors.get("root_category_id"),
            ),
            ResponseProperty(
                "root_category_name",
                "root_category_name",
                Extractors.get("root_category_name"),
            ),
            ResponseProperty(
                "size_group_id", "size_group_id", Extractors.get("size_group_id")
            ),
            ResponseProperty(
                "brand_group_id", "brand_group_id", Extractors.get("brand_group_id")
            ),
        ],
    ),
    ShopProduct: R(
        required_properties=[
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty(
                "productTags", "product_tags", Extractors.get("productTags")
            ),
            ResponseProperty("thumbnail", "thumbnail", Extractors.get("thumbnail")),
            ResponseProperty("price", "price", Extractors.get("price")),
            ResponseProperty("createTime", "create_time", Extractors.get("createTime")),
            ResponseProperty("updateTime", "update_time", Extractors.get("updateTime")),
            ResponseProperty("attributes", "attributes", Extractors.get("attributes")),
            ResponseProperty(
                "productDetail",
                "product_detail",
                Extractors.get_as_model("productDetail", ShopProductDetail),
            ),
        ],
        optional_properties=[
            ResponseProperty(
                "isBlockedShop", "is_blocked_shop", Extractors.get("isBlockedShop")
            ),
        ],
    ),
    ShopProductDetail: R(
        required_properties=[
            ResponseProperty(
                "shop", "shop", Extractors.get_as_model("shop", ShopDetail)
            ),
            ResponseProperty("photos", "photos", Extractors.get("photos")),
            ResponseProperty(
                "description", "description", Extractors.get("description")
            ),
            ResponseProperty(
                "categories",
                "categories",
                Extractors.get_list_of_model("categories", ShopProductCategory),
            ),
            ResponseProperty(
                "condition",
                "condition",
                Extractors.get_as_model("condition", ShopProductCondition),
            ),
            ResponseProperty(
                "shippingMethod",
                "shipping_method",
                Extractors.get_as_model("shippingMethod", ShopProductShippingMethod),
            ),
            ResponseProperty(
                "shippingPayer",
                "shipping_payer",
                Extractors.get_as_model("shippingPayer", ShopProductShippingPayer),
            ),
            ResponseProperty(
                "shippingDuration",
                "shipping_duration",
                Extractors.get_as_model(
                    "shippingDuration", ShopProductShippingDuration
                ),
            ),
            ResponseProperty(
                "shippingFromArea",
                "shipping_from_area",
                Extractors.get_as_model(
                    "shippingFromArea", ShopProductShippingFromArea
                ),
            ),
            ResponseProperty(
                "promotions",
                "promotions",
                Extractors.get_list_of_model("promotions", Promotion),
            ),
            ResponseProperty(
                "variants",
                "variants",
                Extractors.get_list_of_model("variants", ProductVariant),
            ),
        ],
        optional_properties=[
            ResponseProperty(
                "brand", "brand", Extractors.get_as_model("brand", ShopProductBrand)
            ),
            ResponseProperty(
                "productStats",
                "product_stats",
                Extractors.get_as_model("productStats", ProductStats),
            ),
            ResponseProperty(
                "timeSaleDetails",
                "time_sale_details",
                Extractors.get_as_model("timeSaleDetails", TimeSaleDetails),
            ),
            ResponseProperty(
                "shippingFeeConfig",
                "shipping_fee_config",
                Extractors.get_as_model("shippingFeeConfig", ShippingFeeConfig),
            ),
            ResponseProperty(
                "variationGrouping",
                "variation_grouping",
                Extractors.get_as_model("variationGrouping", VariationGrouping),
            ),
            ResponseProperty(
                "buyerPromotion",
                "buyer_promotion",
                Extractors.get_as_model("buyerPromotion", BuyerPromotion),
            ),
            ResponseProperty(
                "followPromotion",
                "follow_promotion",
                Extractors.get_as_model("followPromotion", FollowPromotion),
            ),
            ResponseProperty(
                "lastPurchasedDateTime",
                "last_purchased_date_time",
                Extractors.get("lastPurchasedDateTime"),
            ),
            ResponseProperty(
                "realCardReward",
                "real_card_reward",
                Extractors.get_as_model("realCardReward", RealCardReward),
            ),
            ResponseProperty(
                "mercardCampaign",
                "mercard_campaign",
                Extractors.get_as_model("mercardCampaign", MercardCampaign),
            ),
            ResponseProperty(
                "seoMetadata",
                "seo_metadata",
                Extractors.get_as_model("seoMetadata", SeoMetadata),
            ),
            ResponseProperty(
                "productPreOrder",
                "product_pre_order",
                Extractors.get_as_model("productPreOrder", ProductPreOrder),
            ),
        ],
    ),
    ShopDetail: R(
        required_properties=[
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty("thumbnail", "thumbnail", Extractors.get("thumbnail")),
            ResponseProperty(
                "shopStats",
                "shop_stats",
                Extractors.get_as_model("shopStats", ShopStats),
            ),
            ResponseProperty(
                "allowDirectMessage",
                "allow_direct_message",
                Extractors.get("allowDirectMessage"),
            ),
            ResponseProperty(
                "shopItems",
                "shop_items",
                Extractors.get_list_of_model("shopItems", ShopItemSummary),
            ),
            ResponseProperty(
                "isInboundXb", "is_inbound_xb", Extractors.get("isInboundXb")
            ),
            ResponseProperty(
                "badges", "badges", Extractors.get_list_of_model("badges", ShopBadge)
            ),
            ResponseProperty(
                "hasApprovedBrandScreening",
                "has_approved_brand_screening",
                Extractors.get("hasApprovedBrandScreening"),
            ),
        ],
        optional_properties=[
            ResponseProperty(
                "alwaysShowStock",
                "always_show_stock",
                Extractors.get("alwaysShowStock"),
            ),
        ],
    ),
    ShopStats: R(
        required_properties=[
            ResponseProperty("shopId", "shop_id", Extractors.get("shopId")),
            ResponseProperty("score", "score", Extractors.get("score")),
            ResponseProperty(
                "reviewCount", "review_count", Extractors.get("reviewCount")
            ),
        ],
        optional_properties=[],
    ),
    ShopItemSummary: R(
        required_properties=[
            ResponseProperty("productId", "product_id", Extractors.get("productId")),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty(
                "productTags", "product_tags", Extractors.get("productTags")
            ),
            ResponseProperty("thumbnail", "thumbnail", Extractors.get("thumbnail")),
            ResponseProperty("price", "price", Extractors.get("price")),
        ],
        optional_properties=[],
    ),
    ShopBadge: R(
        required_properties=[
            ResponseProperty("badgeType", "badge_type", Extractors.get("badgeType")),
        ],
        optional_properties=[
            ResponseProperty("badgeName", "badge_name", Extractors.get("badgeName")),
            ResponseProperty("status", "status", Extractors.get("status")),
        ],
    ),
    ShopProductCategory: R(
        required_properties=[
            ResponseProperty("categoryId", "category_id", Extractors.get("categoryId")),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty("parentId", "parent_id", Extractors.get("parentId")),
            ResponseProperty("rootId", "root_id", Extractors.get("rootId")),
            ResponseProperty("hasChild", "has_child", Extractors.get("hasChild")),
        ],
        optional_properties=[],
    ),
    ShopProductBrand: R(
        required_properties=[
            ResponseProperty("brandId", "brand_id", Extractors.get("brandId")),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
        ],
        optional_properties=[],
    ),
    ShopProductCondition: R(
        required_properties=[
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
        ],
        optional_properties=[],
    ),
    ShopProductShippingMethod: R(
        required_properties=[
            ResponseProperty(
                "shippingMethodId",
                "shipping_method_id",
                Extractors.get("shippingMethodId"),
            ),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty(
                "isAnonymous", "is_anonymous", Extractors.get("isAnonymous")
            ),
        ],
        optional_properties=[],
    ),
    ShopProductShippingPayer: R(
        required_properties=[
            ResponseProperty(
                "shippingPayerId",
                "shipping_payer_id",
                Extractors.get("shippingPayerId"),
            ),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty("code", "code", Extractors.get("code")),
        ],
        optional_properties=[],
    ),
    ShopProductShippingDuration: R(
        required_properties=[
            ResponseProperty(
                "shippingDurationId",
                "shipping_duration_id",
                Extractors.get("shippingDurationId"),
            ),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty("minDays", "min_days", Extractors.get("minDays")),
            ResponseProperty("maxDays", "max_days", Extractors.get("maxDays")),
        ],
        optional_properties=[],
    ),
    ShopProductShippingFromArea: R(
        required_properties=[
            ResponseProperty(
                "shippingAreaCode",
                "shipping_area_code",
                Extractors.get("shippingAreaCode"),
            ),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
        ],
        optional_properties=[],
    ),
    PromotionAction: R(
        required_properties=[
            ResponseProperty("action", "action", Extractors.get("action")),
            ResponseProperty(
                "discountType", "discount_type", Extractors.get("discountType")
            ),
            ResponseProperty(
                "discountValue", "discount_value", Extractors.get("discountValue")
            ),
            ResponseProperty("returnType", "return_type", Extractors.get("returnType")),
            ResponseProperty("couponType", "coupon_type", Extractors.get("couponType")),
            ResponseProperty(
                "maxReturnAmount",
                "max_return_amount",
                Extractors.get("maxReturnAmount"),
            ),
            ResponseProperty("returnText", "return_text", Extractors.get("returnText")),
            ResponseProperty(
                "discountAmount", "discount_amount", Extractors.get("discountAmount")
            ),
            ResponseProperty(
                "discountedPrice", "discounted_price", Extractors.get("discountedPrice")
            ),
        ],
        optional_properties=[],
    ),
    Promotion: R(
        required_properties=[
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty(
                "action", "action", Extractors.get_as_model("action", PromotionAction)
            ),
        ],
        optional_properties=[],
    ),
    ProductStats: R(
        required_properties=[
            ResponseProperty("productId", "product_id", Extractors.get("productId")),
            ResponseProperty("score", "score", Extractors.get("score")),
            ResponseProperty(
                "reviewCount", "review_count", Extractors.get("reviewCount")
            ),
            ResponseProperty("likesCount", "likes_count", Extractors.get("likesCount")),
        ],
        optional_properties=[],
    ),
    TimeSaleDetails: R(
        required_properties=[
            ResponseProperty("name", "name", Extractors.get("name")),
            ResponseProperty(
                "percentage", "percentage", Extractors.get_as("percentage", int)
            ),
            ResponseProperty("price", "price", Extractors.get("price")),
            ResponseProperty("startTime", "start_time", Extractors.get("startTime")),
            ResponseProperty("endTime", "end_time", Extractors.get("endTime")),
            ResponseProperty("base", "base", Extractors.get("base")),
            ResponseProperty(
                "calculationStartTime",
                "calculation_start_time",
                Extractors.get("calculationStartTime"),
            ),
            ResponseProperty(
                "calculationEndTime",
                "calculation_end_time",
                Extractors.get("calculationEndTime"),
            ),
        ],
        optional_properties=[],
    ),
    ProductVariant: R(
        required_properties=[
            ResponseProperty("variantId", "variant_id", Extractors.get("variantId")),
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty("quantity", "quantity", Extractors.get("quantity")),
            ResponseProperty("size", "size", Extractors.get("size")),
            ResponseProperty("attributes", "attributes", Extractors.get("attributes")),
        ],
        optional_properties=[],
    ),
    ShippingFeeConfig: R(
        required_properties=[
            ResponseProperty("feeType", "fee_type", Extractors.get("feeType")),
        ],
        optional_properties=[
            ResponseProperty("baseFee", "base_fee", Extractors.get("baseFee")),
            ResponseProperty(
                "additionalFee", "additional_fee", Extractors.get("additionalFee")
            ),
        ],
    ),
    VariationGrouping: R(
        required_properties=[
            ResponseProperty("groupId", "group_id", Extractors.get("groupId")),
            ResponseProperty("groupName", "group_name", Extractors.get("groupName")),
            ResponseProperty("variations", "variations", Extractors.get("variations")),
        ],
        optional_properties=[],
    ),
    BuyerPromotion: R(
        required_properties=[
            ResponseProperty(
                "promotionId", "promotion_id", Extractors.get("promotionId")
            ),
            ResponseProperty(
                "promotionType", "promotion_type", Extractors.get("promotionType")
            ),
            ResponseProperty(
                "discountValue", "discount_value", Extractors.get("discountValue")
            ),
        ],
        optional_properties=[],
    ),
    FollowPromotion: R(
        required_properties=[
            ResponseProperty(
                "displayName", "display_name", Extractors.get("displayName")
            ),
            ResponseProperty(
                "action", "action", Extractors.get_as_model("action", PromotionAction)
            ),
        ],
        optional_properties=[],
    ),
    RealCardReward: R(
        required_properties=[
            ResponseProperty(
                "rewardAmount", "reward_amount", Extractors.get("rewardAmount")
            ),
            ResponseProperty(
                "hasActiveCard", "has_active_card", Extractors.get("hasActiveCard")
            ),
            ResponseProperty("hasMvno", "has_mvno", Extractors.get("hasMvno")),
            ResponseProperty("rewardRate", "reward_rate", Extractors.get("rewardRate")),
            ResponseProperty("lpUri", "lp_uri", Extractors.get("lpUri")),
            ResponseProperty(
                "estimateRewardText",
                "estimate_reward_text",
                Extractors.get("estimateRewardText"),
            ),
            ResponseProperty(
                "disclaimerText", "disclaimer_text", Extractors.get("disclaimerText")
            ),
            ResponseProperty(
                "showComponent", "show_component", Extractors.get("showComponent")
            ),
        ],
        optional_properties=[],
    ),
    MercardCampaign: R(
        required_properties=[
            ResponseProperty("id", "id_", Extractors.get("id")),
            ResponseProperty("title", "title", Extractors.get("title")),
            ResponseProperty("uri", "uri", Extractors.get("uri")),
            ResponseProperty("text", "text", Extractors.get("text")),
            ResponseProperty(
                "discountAmount", "discount_amount", Extractors.get("discountAmount")
            ),
            ResponseProperty(
                "maxDiscount", "max_discount", Extractors.get("maxDiscount")
            ),
        ],
        optional_properties=[],
    ),
    SeoMetadata: R(
        required_properties=[],
        optional_properties=[
            ResponseProperty("title", "title", Extractors.get("title")),
            ResponseProperty(
                "description", "description", Extractors.get("description")
            ),
            ResponseProperty("keywords", "keywords", Extractors.get("keywords")),
        ],
    ),
    ProductPreOrder: R(
        required_properties=[
            ResponseProperty(
                "isPreOrder", "is_pre_order", Extractors.get("isPreOrder")
            ),
        ],
        optional_properties=[
            ResponseProperty(
                "expectedShipDate",
                "expected_ship_date",
                Extractors.get("expectedShipDate"),
            ),
        ],
    ),
}

RM = TypeVar("RM", bound=ResponseModel)


def map_to_class(
    response: dict,
    clazz: Type[RM],
    mapping_definition: ResponseMappingDefinition = None,
) -> RM:
    if clazz == ResponseModel:
        raise TypeError(
            "map_to_class() is supposed to be called with ResponseModel subclass as a parameter"
        )

    if mapping_definition is None:
        mapping_definition = mapping_definitions.get(clazz)
    if mapping_definition is None:
        raise ValueError(f"Mapping definition is not provided for {clazz.__name__}")

    init_properties = {}

    for prop in mapping_definition.required_properties:
        try:
            raw_prop = prop.extractor(response)
            if raw_prop is None:
                raise ValueError("Extractor returned None value")
            init_properties[prop.model_property_name] = raw_prop
        except Exception as exc:
            raise ParseAPIResponseError(
                f"Failed to retrieve required {clazz.__name__} property {prop.raw_property_name} from the response"
            ) from exc

    for prop in mapping_definition.optional_properties:
        raw_prop = None
        try:
            raw_prop = prop.extractor(response)
        except Exception as exc:
            _report_incorrect_optional(prop.raw_property_name, response, exc)
        init_properties[prop.model_property_name] = raw_prop

    return clazz(**init_properties)


def _report_incorrect_optional(prop: str, response: dict, exc: Exception) -> None:
    logging.warning(
        f"Encountered optional response property {prop} that could not be parsed correctly."
    )
    logging.debug(f"Response body: {response}\nError: {exc}")
