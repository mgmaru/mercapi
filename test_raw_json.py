import asyncio
import json
from mercapi import Mercapi

async def main():
    api = Mercapi()

    # Make the raw API call
    req = api._item('m67451288459')
    res = await api._client.send(req)
    body = res.json()

    data = body.get('data', {})

    # Check if these fields exist
    print("Fields in data object:")
    print(f"  'photo_descriptions' exists: {'photo_descriptions' in data}")
    print(f"  'item_attributes' exists: {'item_attributes' in data}")
    print(f"  'has_active_mercard' exists: {'has_active_mercard' in data}")

    if 'photo_descriptions' in data:
        print(f"\nphoto_descriptions value: {json.dumps(data['photo_descriptions'][:3] if data['photo_descriptions'] else [], indent=2)}")

    if 'item_attributes' in data:
        print(f"\nitem_attributes count: {len(data['item_attributes'])}")
        if data['item_attributes']:
            print(f"First attribute: {json.dumps(data['item_attributes'][0], indent=2)}")

    if 'has_active_mercard' in data:
        print(f"\nhas_active_mercard value: {repr(data['has_active_mercard'])}")

if __name__ == '__main__':
    asyncio.run(main())
