"""
Fix old orders - Add total_amount field
"""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "taste_paradise")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

# Find orders without total_amount
orders_to_fix = db.orders.find({"total_amount": {"$exists": False}})

count = 0
for order in orders_to_fix:
    # If order has 'total' field, copy it to 'total_amount'
    if "total" in order:
        db.orders.update_one(
            {"_id": order["_id"]},
            {"$set": {"total_amount": order["total"]}}
        )
        count += 1
        print(f"✅ Fixed order {order['_id']}")

print(f"\n🎉 Fixed {count} orders!")
print("All orders now have 'total_amount' field.")
