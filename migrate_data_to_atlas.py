"""
One-Time Data Migration Script
Migrates all existing local MongoDB data to MongoDB Atlas
Author: Amrit Gaur
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB Configuration
LOCAL_MONGO_URI = "mongodb://localhost:27017"
ATLAS_MONGO_URI = "mongodb+srv://gaurhariom60_db_user:S4J2vvbZLbrRAlP7@cluster01.7o6we1z.mongodb.net/tasteparadise?retryWrites=true&w=majority&appName=cluster01"

# Get license key (from taste_paradise.license file)
def get_license_key():
    """Read license key from local file"""
    try:
        with open('taste_paradise.license', 'r') as f:
            encoded = f.read()
        json_str = bytes.fromhex(encoded).decode('utf-8')
        license_data = json.loads(json_str)
        return license_data.get('key')
    except:
        print("❌ Error: License file not found!")
        print("   Please run the app first to activate your license.")
        return None

def migrate_data():
    """
    Migrate all data from local MongoDB to MongoDB Atlas
    """
    print("\n" + "="*70)
    print("🚀 TASTEPARADISE DATA MIGRATION TO CLOUD")
    print("="*70)
    
    # Get license key
    license_key = get_license_key()
    if not license_key:
        return False
    
    print(f"\n📋 License Key: {license_key[:20]}...")
    print("⏳ Starting migration process...")
    
    try:
        # Connect to local MongoDB
        print("\n1️⃣ Connecting to local MongoDB...")
        local_client = MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=5000)
        local_db = local_client['taste_paradise']
        print("   ✅ Connected to local database")
        
        # Connect to MongoDB Atlas
        print("\n2️⃣ Connecting to MongoDB Atlas...")
        atlas_client = MongoClient(ATLAS_MONGO_URI, serverSelectionTimeoutMS=10000)
        atlas_db = atlas_client['tasteparadise']
        atlas_collection = atlas_db['customer_data']
        print("   ✅ Connected to MongoDB Atlas")
        
        # Get all collections from local database
        print("\n3️⃣ Scanning local database...")
        collection_names = local_db.list_collection_names()
        print(f"   📊 Found {len(collection_names)} collections")
        
        if not collection_names:
            print("\n⚠️  No data found in local database!")
            print("   Your database appears to be empty.")
            return True
        
        # Migrate each collection
        print("\n4️⃣ Starting data migration...")
        total_documents = 0
        
        for collection_name in collection_names:
            # Skip system collections
            if collection_name.startswith('system.'):
                continue
            
            print(f"\n   📦 Migrating collection: {collection_name}")
            
            # Get all documents from local collection
            local_collection = local_db[collection_name]
            documents = list(local_collection.find())
            
            if not documents:
                print(f"      ⚠️  Empty collection - skipped")
                continue
            
            print(f"      📄 Found {len(documents)} documents")
            
            # Prepare documents for Atlas
            atlas_documents = []
            for doc in documents:
                # Remove local MongoDB _id
                doc.pop('_id', None)
                
                # Add metadata for cloud storage
                doc['_collection'] = f"{license_key}_{collection_name}"
                doc['_sync_time'] = datetime.now().isoformat()
                doc['_license'] = license_key
                doc['_migrated'] = True
                doc['_migration_date'] = datetime.now().isoformat()
                
                atlas_documents.append(doc)
            
            # Upload to MongoDB Atlas
            try:
                # Clear existing data for this collection (if any)
                atlas_collection.delete_many({
                    '_collection': f"{license_key}_{collection_name}"
                })
                
                # Insert new data
                if atlas_documents:
                    result = atlas_collection.insert_many(atlas_documents)
                    inserted_count = len(result.inserted_ids)
                    total_documents += inserted_count
                    print(f"      ✅ Uploaded {inserted_count} documents")
            
            except Exception as e:
                print(f"      ❌ Error uploading: {e}")
                continue
        
        # Summary
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETED!")
        print("="*70)
        print(f"📊 Total collections migrated: {len(collection_names)}")
        print(f"📄 Total documents uploaded: {total_documents}")
        print(f"☁️  All data now available in MongoDB Atlas!")
        print("="*70)
        
        # Instructions
        print("\n📌 NEXT STEPS:")
        print("1. Login to MongoDB Atlas: https://cloud.mongodb.com/")
        print("2. Navigate to: Browse Collections → customer_data")
        print(f"3. Filter by: {{ '_license': '{license_key}' }}")
        print("4. ✅ View your migrated data!")
        print("\n" + "="*70)
        
        # Close connections
        local_client.close()
        atlas_client.close()
        
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ MIGRATION FAILED!")
        print("="*70)
        print(f"Error: {e}")
        print("\nPlease check:")
        print("- Local MongoDB is running")
        print("- Internet connection is active")
        print("- MongoDB Atlas credentials are correct")
        print("="*70)
        return False

if __name__ == "__main__":
    success = migrate_data()
    
    if success:
        print("\n✅ Migration successful!")
        print("Your data is now backed up in the cloud! 🎉")
    else:
        print("\n❌ Migration failed!")
        print("Please fix the errors and try again.")
    
    input("\nPress Enter to exit...")
