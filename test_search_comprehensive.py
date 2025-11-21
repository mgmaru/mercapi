"""
Comprehensive test for Mercari search API responses.
Prints EVERY field from the search results JSON, including null and empty values.
"""
import asyncio
import sys
from mercapi import Mercapi


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f" {title}")
    print('='*80)


def print_item_complete(item, index):
    """Print every single field from a SearchResultItem."""
    print(f"\n{'─'*80}")
    print(f"ITEM #{index}: {item.name}")
    print('─'*80)

    # Top-level required fields
    print(f"\n📌 REQUIRED FIELDS:")
    print(f"  id:                    {repr(item.id_)}")
    print(f"  name:                  {repr(item.name)}")
    print(f"  price:                 {repr(item.price)}")

    # Top-level optional fields (in order from the JSON)
    print(f"\n📋 TOP-LEVEL OPTIONAL FIELDS:")
    print(f"  sellerId:              {repr(item.seller_id)}")
    print(f"  buyerId:               {repr(item.buyer_id)}")
    print(f"  status:                {repr(item.status)}")
    print(f"  created:               {repr(item.created)}")
    print(f"  updated:               {repr(item.updated)}")

    # Thumbnails
    print(f"\n📸 THUMBNAILS:")
    if item.thumbnails is not None:
        if item.thumbnails:
            print(f"  thumbnails (count):    {len(item.thumbnails)}")
            for idx, thumb in enumerate(item.thumbnails):
                print(f"    [{idx}] {thumb}")
        else:
            print(f"  thumbnails:            [] (empty array)")
    else:
        print(f"  thumbnails:            None")

    # Item metadata
    print(f"\n🏷️  ITEM METADATA:")
    print(f"  itemType:              {repr(item.item_type)}")
    print(f"  itemConditionId:       {repr(item.item_condition_id)}")
    print(f"  shippingPayerId:       {repr(item.shipping_payer_id)}")
    print(f"  shippingMethodId:      {repr(item.shipping_method_id)}")
    print(f"  categoryId:            {repr(item.category_id)}")
    print(f"  isNoPrice:             {repr(item.is_no_price)}")
    print(f"  title:                 {repr(item.title)}")
    print(f"  isLiked:               {repr(item.is_liked)}")
    print(f"  shopName:              {repr(item.shop_name)}")

    # Item sizes (list)
    print(f"\n📏 ITEM SIZES (itemSizes):")
    if item.item_sizes is not None:
        if item.item_sizes:
            print(f"  itemSizes (count):     {len(item.item_sizes)}")
            for idx, size in enumerate(item.item_sizes):
                print(f"    [{idx}] ItemSize:")
                print(f"        id:            {repr(size.id_)}")
                print(f"        name:          {repr(size.name)}")
        else:
            print(f"  itemSizes:             [] (empty array)")
    else:
        print(f"  itemSizes:             None")

    # Item brand
    print(f"\n🏷️  ITEM BRAND (itemBrand):")
    if item.item_brand is not None:
        print(f"  itemBrand:")
        print(f"    id:                  {repr(item.item_brand.id_)}")
        print(f"    name:                {repr(item.item_brand.name)}")
        print(f"    subName:             {repr(item.item_brand.sub_name)}")
    else:
        print(f"  itemBrand:             None")

    # Item promotions
    print(f"\n🎁 ITEM PROMOTIONS (itemPromotions):")
    if item.item_promotions is not None:
        if item.item_promotions:
            print(f"  itemPromotions (count): {len(item.item_promotions)}")
            for idx, promo in enumerate(item.item_promotions):
                print(f"    [{idx}] {promo}")
        else:
            print(f"  itemPromotions:        [] (empty array)")
    else:
        print(f"  itemPromotions:        None")

    # Item size (single)
    print(f"\n📏 ITEM SIZE (itemSize - single):")
    if item.item_size is not None:
        print(f"  itemSize:")
        print(f"    id:                  {repr(item.item_size.id_)}")
        print(f"    name:                {repr(item.item_size.name)}")
    else:
        print(f"  itemSize:              None")

    # Photos
    print(f"\n📸 PHOTOS:")
    if item.photos is not None:
        if item.photos:
            print(f"  photos (count):        {len(item.photos)}")
            for idx, photo in enumerate(item.photos):
                print(f"    [{idx}] PhotoUri:")
                print(f"        uri:           {repr(photo.uri)}")
        else:
            print(f"  photos:                [] (empty array)")
    else:
        print(f"  photos:                None")

    # Auction
    print(f"\n🔨 AUCTION:")
    if item.auction is not None:
        print(f"  auction:")
        print(f"    id:                  {repr(item.auction.id_)}")
        print(f"    bidDeadline:         {repr(item.auction.bid_deadline)}")
        print(f"    totalBid:            {repr(item.auction.total_bid)}")
        print(f"    highestBid:          {repr(item.auction.highest_bid)}")
    else:
        print(f"  auction:               null")

    # Shop
    print(f"\n🏪 SHOP:")
    if item.shop is not None:
        print(f"  shop:")
        print(f"    id:                  {repr(item.shop.id_)}")
        print(f"    displayName:         {repr(item.shop.display_name)}")
        print(f"    thumbnail:           {repr(item.shop.thumbnail)}")
    else:
        print(f"  shop:                  null")


async def main():
    """Run comprehensive search test showing all fields."""
    # Set UTF-8 encoding for console output (Windows compatibility)
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print_section("COMPREHENSIVE SEARCH RESULTS - ALL FIELDS")
    print("This test displays EVERY field from the search results JSON")
    print("including null values and empty arrays/strings.")

    api = Mercapi()

    # Test query
    query = 'isamu katayama backlash'
    print(f"\nSearch query: '{query}'")

    results = await api.search(query)

    print(f"\n📊 SEARCH METADATA:")
    print(f"  Total found:           {results.meta.num_found}")
    print(f"  Retrieved:             {len(results.items)}")
    print(f"  Page token:            {repr(results.meta.next_page_token)}")

    # Show complete details for first 3 items
    items_to_show = min(3, len(results.items))

    print_section(f"DETAILED VIEW - FIRST {items_to_show} ITEMS")
    print("Showing every single field including null/empty values")

    for idx in range(items_to_show):
        print_item_complete(results.items[idx], idx + 1)

    # Summary statistics
    print_section("SUMMARY STATISTICS")

    stats = {
        'total': len(results.items),
        'with_seller_id': sum(1 for i in results.items if i.seller_id),
        'with_buyer_id': sum(1 for i in results.items if i.buyer_id),
        'with_status': sum(1 for i in results.items if i.status),
        'with_thumbnails': sum(1 for i in results.items if i.thumbnails),
        'with_item_type': sum(1 for i in results.items if i.item_type),
        'with_brand': sum(1 for i in results.items if i.item_brand),
        'with_size': sum(1 for i in results.items if i.item_size),
        'with_sizes_list': sum(1 for i in results.items if i.item_sizes),
        'with_promotions': sum(1 for i in results.items if i.item_promotions),
        'with_photos': sum(1 for i in results.items if i.photos),
        'with_auction': sum(1 for i in results.items if i.auction),
        'with_shop': sum(1 for i in results.items if i.shop),
        'with_title': sum(1 for i in results.items if i.title),
        'with_shop_name': sum(1 for i in results.items if i.shop_name),
    }

    print(f"Total items: {stats['total']}\n")
    print("Field presence:")
    print(f"  ├─ sellerId:           {stats['with_seller_id']:3d} / {stats['total']} ({stats['with_seller_id']/stats['total']*100:.1f}%)")
    print(f"  ├─ buyerId:            {stats['with_buyer_id']:3d} / {stats['total']} ({stats['with_buyer_id']/stats['total']*100:.1f}%)")
    print(f"  ├─ status:             {stats['with_status']:3d} / {stats['total']} ({stats['with_status']/stats['total']*100:.1f}%)")
    print(f"  ├─ thumbnails:         {stats['with_thumbnails']:3d} / {stats['total']} ({stats['with_thumbnails']/stats['total']*100:.1f}%)")
    print(f"  ├─ itemType:           {stats['with_item_type']:3d} / {stats['total']} ({stats['with_item_type']/stats['total']*100:.1f}%)")
    print(f"  ├─ itemBrand:          {stats['with_brand']:3d} / {stats['total']} ({stats['with_brand']/stats['total']*100:.1f}%)")
    print(f"  ├─ itemSize:           {stats['with_size']:3d} / {stats['total']} ({stats['with_size']/stats['total']*100:.1f}%)")
    print(f"  ├─ itemSizes:          {stats['with_sizes_list']:3d} / {stats['total']} ({stats['with_sizes_list']/stats['total']*100:.1f}%)")
    print(f"  ├─ itemPromotions:     {stats['with_promotions']:3d} / {stats['total']} ({stats['with_promotions']/stats['total']*100:.1f}%)")
    print(f"  ├─ photos:             {stats['with_photos']:3d} / {stats['total']} ({stats['with_photos']/stats['total']*100:.1f}%)")
    print(f"  ├─ title:              {stats['with_title']:3d} / {stats['total']} ({stats['with_title']/stats['total']*100:.1f}%)")
    print(f"  ├─ shopName:           {stats['with_shop_name']:3d} / {stats['total']} ({stats['with_shop_name']/stats['total']*100:.1f}%)")
    print(f"  ├─ auction:            {stats['with_auction']:3d} / {stats['total']} ({stats['with_auction']/stats['total']*100:.1f}%)")
    print(f"  └─ shop:               {stats['with_shop']:3d} / {stats['total']} ({stats['with_shop']/stats['total']*100:.1f}%)")

    print_section("TEST COMPLETE")


if __name__ == '__main__':
    asyncio.run(main())
