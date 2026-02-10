"""
Main ShopProduct model representing a Mercari Shop listing.

Shop listings are business/commercial seller listings with additional
features and information compared to regular personal seller listings.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from mercapi.models.base import ResponseModel
from mercapi.models.shop.data import ShopProductDetail


@dataclass
class ShopProduct(ResponseModel):
    """
    Mercari Shop product listing.

    This represents a complete shop product listing from a business/commercial seller.
    Shop products have different structures and additional fields compared to
    regular personal seller listings.

    Use `Mercapi.shop_product(product_id)` to fetch shop product information.

    Example:
        ```python
        api = Mercapi()
        product = await api.shop_product('2JHDxUxi3SsqAG5umbmWY2')

        print(f"Product: {product.display_name}")
        print(f"Price: ¥{product.price}")
        print(f"Shop: {product.product_detail.shop.display_name}")
        print(f"Rating: {product.product_detail.shop.shop_stats.score}/5")
        ```
    """

    name: str
    """Internal product name/ID"""

    display_name: str
    """Human-readable product name"""

    product_tags: List[str]
    """Product tags"""

    thumbnail: str
    """Thumbnail image URL"""

    price: str
    """Product price in yen"""

    create_time: str
    """Creation timestamp (ISO 8601 format)"""

    update_time: str
    """Last update timestamp (ISO 8601 format)"""

    attributes: List[dict]
    """Product attributes"""

    product_detail: ShopProductDetail
    """Detailed product information including shop, shipping, promotions, etc."""

    is_blocked_shop: Optional[bool] = None
    """Whether the shop is blocked"""
