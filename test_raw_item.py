import asyncio
import json
from mercapi import Mercapi

async def main():
    api = Mercapi()
    item = await api.item('m67451288459')

    print("photo_descriptions type:", type(item.photo_descriptions))
    print("photo_descriptions value:", item.photo_descriptions)

    print("\nitem_attributes type:", type(item.item_attributes))
    print("item_attributes value:", item.item_attributes)

    print("\nhas_active_mercard type:", type(item.has_active_mercard))
    print("has_active_mercard value:", repr(item.has_active_mercard))

    print("\nadditional_services type:", type(item.additional_services))
    print("additional_services value:", item.additional_services)

    print("\napplication_attributes type:", type(item.application_attributes))
    print("application_attributes value:", item.application_attributes)

if __name__ == '__main__':
    asyncio.run(main())
