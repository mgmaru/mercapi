import asyncio
import logging
from mercapi import Mercapi

# Set up logging to see warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(name)s:%(message)s')

async def main():
    api = Mercapi()
    item = await api.item('m67451288459')

    print(f"item_attributes: {item.item_attributes}")
    print(f"photo_descriptions: {item.photo_descriptions}")
    print(f"has_active_mercard: {item.has_active_mercard}")

if __name__ == '__main__':
    asyncio.run(main())
