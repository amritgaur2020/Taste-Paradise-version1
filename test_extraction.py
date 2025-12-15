from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['taste_paradise']
    
    print("Testing collections in 'taste_paradise' database:")
    print("="*70)
    
    # Try different collection names
    collections_to_try = [
        'menu_items',
        'menuitems', 
        'menu',
        'orders',
        'bills'
    ]
    
    for coll_name in collections_to_try:
        try:
            count = await db[coll_name].count_documents({})
            print(f"✓ {coll_name}: {count} documents")
            
            if count > 0:
                # Show sample document
                sample = await db[coll_name].find_one()
                print(f"  Sample keys: {list(sample.keys())[:5]}")
        except Exception as e:
            print(f"✗ {coll_name}: Error - {e}")
    
    client.close()

asyncio.run(test())
