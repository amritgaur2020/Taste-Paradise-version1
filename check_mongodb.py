from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')

print("="*70)
print("MONGODB DATABASES AND COLLECTIONS")
print("="*70)

# List all databases
print("\nAvailable Databases:")
for db_name in client.list_database_names():
    print(f"  📦 {db_name}")
    
    # List collections in each database
    db = client[db_name]
    collections = db.list_collection_names()
    if collections:
        for coll in collections:
            count = db[coll].count_documents({})
            print(f"      └─ {coll}: {count} documents")
    else:
        print(f"      └─ (no collections)")

print("\n" + "="*70)

# Check specifically for TasteParadise data
print("\nChecking 'tasteparadise' database:")
db = client['tasteparadise']
for coll in ['menu_items', 'menuitems', 'orders', 'bills']:
    try:
        count = db[coll].count_documents({})
        print(f"  {coll}: {count} documents")
    except:
        print(f"  {coll}: collection doesn't exist")

client.close()
