"""
Clear MongoDB Atlas Data Only
Deletes data from MongoDB Atlas cloud backup
Local MongoDB data remains UNTOUCHED
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

def clear_atlas_only():
    """
    Delete data from MongoDB Atlas ONLY
    Local MongoDB is NOT affected
    """
    print("\n" + "="*70)
    print("🗑️  CLEAR MONGODB ATLAS DATA")
    print("="*70)
    
    # Get license key
    license_key = get_license_key()
    if not license_key:
        return False
    
    print(f"\n📋 License Key: {license_key[:20]}...")
    print("\n⚠️  This will delete data from:")
    print("   ❌ MongoDB Atlas (cloud backup)")
    print("\n✅ Local data will NOT be touched:")
    print("   ✅ Local MongoDB (taste_paradise database)")
    print("   ✅ All your orders, menu items, etc.")
    print("\n" + "="*70)
    
    # Confirmation
    print("\n❓ Delete cloud data only?")
    confirm = input("   Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("\n❌ Cancelled. No data deleted.")
        return False
    
    print("\n⏳ Connecting to MongoDB Atlas...")
    
    try:
        # Connect to MongoDB Atlas
        atlas_client = MongoClient(ATLAS_MONGO_URI, serverSelectionTimeoutMS=10000)
        atlas_db = atlas_client['tasteparadise']
        atlas_collection = atlas_db['customer_data']
        
        print("✅ Connected to MongoDB Atlas")
        
        # Count documents before deletion
        print("\n🔍 Checking your cloud data...")
        doc_count = atlas_collection.count_documents({'_license': license_key})
        
        if doc_count == 0:
            print("\n⚠️  No data found in MongoDB Atlas!")
            print("   Cloud backup is already empty.")
            atlas_client.close()
            return True
        
        print(f"📊 Found {doc_count} documents in cloud")
        
        # Final confirmation
        print(f"\n❓ Delete {doc_count} documents from cloud?")
        confirm2 = input("   Type 'DELETE' to confirm: ")
        
        if confirm2 != 'DELETE':
            print("\n❌ Cancelled. No data deleted.")
            atlas_client.close()
            return False
        
        # Delete all documents for this license
        print("\n🗑️  Deleting cloud data...")
        result = atlas_collection.delete_many({'_license': license_key})
        
        print("\n" + "="*70)
        print("✅ CLOUD DATA DELETED!")
        print("="*70)
        print(f"🗑️  Deleted {result.deleted_count} documents from MongoDB Atlas")
        print("☁️  Cloud backup cleared")
        print("💾 Local MongoDB data is SAFE (unchanged)")
        print("="*70)
        
        print("\n📌 Next steps:")
        print("   1. Your local app still has all data")
        print("   2. Create new orders to test cloud sync")
        print("   3. New data will sync to Atlas automatically")
        print("   4. Check Atlas after 5 minutes to see new data")
        
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
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║           CLEAR MONGODB ATLAS DATA (LOCAL STAYS SAFE)            ║
║                                                                   ║
║  This tool will:                                                 ║
║  ❌ Delete data from MongoDB Atlas (cloud backup)                ║
║  ✅ Keep local MongoDB data SAFE (unchanged)                     ║
║                                                                   ║
║  Use this to test cloud sync with fresh uploads!                ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    success = clear_atlas_only()
    
    if success:
        print("\n✅ Atlas cleared successfully!")
        print("Your local data is safe and untouched! 🎉")
    else:
        print("\n❌ Operation failed or cancelled!")
    
    input("\nPress Enter to exit...")
