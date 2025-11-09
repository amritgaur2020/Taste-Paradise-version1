"""
Delete Customer Data from MongoDB Atlas
Removes all your restaurant data from cloud backup
Author: Amrit Gaur
"""

from pymongo import MongoClient
import json

# MongoDB Atlas Configuration
ATLAS_MONGO_URI = "mongodb+srv://gaurhariom60_db_user:S4J2vvbZLbrRAlP7@cluster01.7o6we1z.mongodb.net/tasteparadise?retryWrites=true&w=majority&appName=cluster01"

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
        return None

def delete_cloud_data():
    """
    Delete all your data from MongoDB Atlas
    """
    print("\n" + "="*70)
    print("🗑️  DELETE CLOUD DATA FROM MONGODB ATLAS")
    print("="*70)
    
    # Get license key
    license_key = get_license_key()
    if not license_key:
        return False
    
    print(f"\n📋 License Key: {license_key[:20]}...")
    print("\n⚠️  WARNING: This will delete ALL your data from MongoDB Atlas!")
    print("   Your local data will NOT be affected.")
    print("\n" + "="*70)
    
    # Confirmation
    confirm = input("\n❓ Are you sure you want to delete? (type 'yes' to confirm): ")
    
    if confirm.lower() != 'yes':
        print("\n❌ Deletion cancelled.")
        return False
    
    print("\n⏳ Connecting to MongoDB Atlas...")
    
    try:
        # Connect to MongoDB Atlas
        atlas_client = MongoClient(ATLAS_MONGO_URI, serverSelectionTimeoutMS=10000)
        atlas_db = atlas_client['tasteparadise']
        atlas_collection = atlas_db['customer_data']
        
        print("✅ Connected to MongoDB Atlas")
        
        # Count documents before deletion
        print("\n🔍 Checking your data...")
        doc_count = atlas_collection.count_documents({'_license': license_key})
        
        if doc_count == 0:
            print("\n⚠️  No data found for your license key!")
            print("   Nothing to delete.")
            return True
        
        print(f"📊 Found {doc_count} documents to delete")
        
        # Final confirmation
        confirm2 = input(f"\n❓ Delete {doc_count} documents? (type 'DELETE' to confirm): ")
        
        if confirm2 != 'DELETE':
            print("\n❌ Deletion cancelled.")
            return False
        
        # Delete all documents for this license
        print("\n🗑️  Deleting data...")
        result = atlas_collection.delete_many({'_license': license_key})
        
        print("\n" + "="*70)
        print("✅ DELETION COMPLETED!")
        print("="*70)
        print(f"🗑️  Deleted {result.deleted_count} documents")
        print("☁️  Your cloud backup has been cleared")
        print("💾 Local data remains safe")
        print("="*70)
        
        # Close connection
        atlas_client.close()
        
        return True
        
    except Exception as e:
        print("\n" + "="*70)
        print("❌ DELETION FAILED!")
        print("="*70)
        print(f"Error: {e}")
        print("\nPlease check:")
        print("- Internet connection is active")
        print("- MongoDB Atlas credentials are correct")
        print("="*70)
        return False

if __name__ == "__main__":
    success = delete_cloud_data()
    
    if success:
        print("\n✅ Deletion successful!")
        print("Your cloud data has been removed! 🎉")
    else:
        print("\n❌ Deletion failed or cancelled!")
    
    input("\nPress Enter to exit...")
