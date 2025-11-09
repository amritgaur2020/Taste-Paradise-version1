"""
Migrate old licenses from JSON to MongoDB Cloud
Run this ONCE to transfer all existing licenses
"""

from pymongo import MongoClient
import json

# MongoDB connection
MONGODB_URI = "mongodb+srv://gaurhariom60_db_user:S4J2vvbZLbrRAlP7@cluster01.7o6we1z.mongodb.net/tasteparadise?retryWrites=true&w=majority&appName=cluster01"

def migrate_licenses():
    print("="*70)
    print("MIGRATING LICENSES TO CLOUD")
    print("="*70)
    
    # Connect to MongoDB
    print("\n1. Connecting to MongoDB Atlas...")
    client = MongoClient(MONGODB_URI)
    db = client['tasteparadise']
    licenses_collection = db['licenses']
    print("   ✅ Connected!")
    
    # Load old licenses
    print("\n2. Loading old licenses from licenses_db.json...")
    try:
        with open('licenses_db.json', 'r') as f:
            old_licenses = json.load(f)
        print(f"   ✅ Found {len(old_licenses)} licenses")
    except FileNotFoundError:
        print("   ❌ licenses_db.json not found!")
        return
    
    # Migrate each license
    print("\n3. Migrating licenses to cloud...")
    migrated = 0
    skipped = 0
    
    for license in old_licenses:
        # Check if already exists
        existing = licenses_collection.find_one({'key': license['key']})
        if existing:
            print(f"   ⏩ Skipping {license['key']} (already exists)")
            skipped += 1
            continue
        
        # Insert to cloud
        licenses_collection.insert_one(license)
        print(f"   ✅ Migrated {license['key']} ({license['customer']})")
        migrated += 1
    
    print("\n" + "="*70)
    print("MIGRATION COMPLETE!")
    print("="*70)
    print(f"   ✅ Migrated: {migrated} licenses")
    print(f"   ⏩ Skipped: {skipped} licenses")
    print(f"   📊 Total in cloud: {licenses_collection.count_documents({})}")
    print("="*70)
    
    # Backup old file
    print("\n4. Backing up old licenses_db.json...")
    import shutil
    shutil.copy('licenses_db.json', 'licenses_db.json.backup')
    print("   ✅ Backup created: licenses_db.json.backup")
    
    print("\n✅ Migration successful!")
    print("   You can now delete the old files:")
    print("   - license_system.py")
    print("   - license_generator.py")
    print("   - licenses_db.json (backup saved)")

if __name__ == "__main__":
    migrate_licenses()
