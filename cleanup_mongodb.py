# cleanup_mongodb_fixed.py
from pymongo import MongoClient
import os

try:
    # Connect to MongoDB
    print("📡 Connecting to MongoDB...")
    client = MongoClient('mongodb://localhost:27017/')
    
    # Get your database name
    db = client['restaurant_db']  # Change if needed
    print(f"✅ Connected to database: {db.name}")
    
    # Get all collection names
    collections = db.list_collection_names()
    print(f"\n📊 Found {len(collections)} collections:")
    for col in collections:
        print(f"  - {col}")
    
    # Check sizes BEFORE
    print("\n📈 SIZES BEFORE CLEANUP:")
    total_before = 0
    for collection_name in collections:
        try:
            stats = db.command('collstats', collection_name)
            size_mb = stats.get('size', 0) / (1024*1024)
            total_before += size_mb
            print(f"  {collection_name}: {size_mb:.2f} MB")
        except:
            print(f"  {collection_name}: (could not read)")
    
    print(f"\n  Total: {total_before:.2f} MB")
    
    # Compact ALL collections
    print("\n🔧 COMPACTING COLLECTIONS...")
    for collection_name in collections:
        try:
            result = db.command('compact', collection_name)
            print(f"  ✅ {collection_name} compacted")
        except Exception as e:
            print(f"  ⚠️  {collection_name}: {str(e)[:50]}")
    
    # Check sizes AFTER
    print("\n📈 SIZES AFTER CLEANUP:")
    total_after = 0
    for collection_name in collections:
        try:
            stats = db.command('collstats', collection_name)
            size_mb = stats.get('size', 0) / (1024*1024)
            total_after += size_mb
            print(f"  {collection_name}: {size_mb:.2f} MB")
        except:
            print(f"  {collection_name}: (could not read)")
    
    print(f"\n  Total: {total_after:.2f} MB")
    print(f"\n💾 SPACE SAVED: {total_before - total_after:.2f} MB")
    print("\n✅ MongoDB cleanup complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure MongoDB is running")
    print("2. Check database name is correct")
    print("3. Ensure you have proper permissions")

finally:
    client.close()
    print("\nConnection closed.")
