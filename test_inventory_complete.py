import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8002/api/inventory"

print("=" * 80)
print("🧪 COMPLETE INVENTORY SYSTEM TEST")
print("=" * 80)
print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ==================== TEST 1: CREATE INVENTORY ITEMS ====================
print("\n📦 TEST 1: Creating Inventory Items")
print("-" * 80)

items_to_create = [
    {
        "name": "Butter",
        "category": "Dairy",
        "unit": "kg",
        "current_stock": 5.0,
        "reorder_level": 2.0,
        "unit_cost": 450,
        "supplier": "ABC Dairy Suppliers",
        "supplier_contact": "+91-9876543210"
    },
    {
        "name": "Paneer",
        "category": "Dairy",
        "unit": "kg",
        "current_stock": 1.5,
        "reorder_level": 3.0,  # Low stock!
        "unit_cost": 350,
        "supplier": "ABC Dairy Suppliers",
        "supplier_contact": "+91-9876543210"
    },
    {
        "name": "Tomato",
        "category": "Vegetables",
        "unit": "kg",
        "current_stock": 15.0,
        "reorder_level": 5.0,
        "unit_cost": 50,
        "supplier": "Fresh Veggie Co",
        "supplier_contact": "+91-9876543211"
    },
    {
        "name": "Onion",
        "category": "Vegetables",
        "unit": "kg",
        "current_stock": 2.0,
        "reorder_level": 10.0,  # Critical low stock!
        "unit_cost": 40,
        "supplier": "Fresh Veggie Co",
        "supplier_contact": "+91-9876543211"
    },
    {
        "name": "Oil",
        "category": "Cooking Essentials",
        "unit": "ltr",
        "current_stock": 8.0,
        "reorder_level": 3.0,
        "unit_cost": 180,
        "supplier": "XYZ Oil Traders",
        "supplier_contact": "+91-9876543212"
    }
]

created_items = []
for item in items_to_create:
    response = requests.post(f"{BASE_URL}/items", json=item)
    if response.status_code == 200:
        result = response.json()
        created_items.append(result)
        print(f"✅ Created: {item['name']} (Stock: {item['current_stock']} {item['unit']})")
    else:
        print(f"❌ Failed to create {item['name']}: {response.status_code}")

print(f"\n📊 Total items created: {len(created_items)}")

# ==================== TEST 2: GET ALL INVENTORY ITEMS ====================
print("\n\n📋 TEST 2: Get All Inventory Items")
print("-" * 80)

response = requests.get(f"{BASE_URL}/items")
if response.status_code == 200:
    all_items = response.json()
    print(f"✅ Total items in inventory: {len(all_items)}")
    print("\nInventory Summary:")
    for item in all_items:
        stock_status = "🟢" if item['current_stock'] > item['reorder_level'] else "🔴"
        inventory_value = item['current_stock'] * item['unit_cost']
        print(f"  {stock_status} {item['name']}: {item['current_stock']}/{item['reorder_level']} {item['unit']} "
              f"(₹{inventory_value:.2f})")
else:
    print(f"❌ Failed: {response.status_code}")

# ==================== TEST 3: GET LOW STOCK ALERTS ====================
print("\n\n⚠️  TEST 3: Get Low Stock Alerts")
print("-" * 80)

response = requests.get(f"{BASE_URL}/alerts/low-stock")
if response.status_code == 200:
    result = response.json()
    print(f"✅ Low stock items found: {result['count']}")
    print(f"   Critical items: {result['critical_count']}")
    
    if result['low_stock_items']:
        print("\nLow Stock Details:")
        for item in result['low_stock_items']:
            urgency_icon = "🚨" if item['urgency'] == 'critical' else "⚠️"
            print(f"  {urgency_icon} {item['name']} ({item['urgency'].upper()})")
            print(f"     Current: {item['current_stock']} {item['unit']}")
            print(f"     Reorder Level: {item['reorder_level']} {item['unit']}")
            print(f"     Need to order: {item['needed']} {item['unit']}")
            print(f"     Supplier: {item.get('supplier', 'N/A')}")
            print(f"     Contact: {item.get('supplier_contact', 'N/A')}")
            print()
    else:
        print("✅ No low stock items found")
else:
    print(f"❌ Failed: {response.status_code}")

# ==================== TEST 4: FILTER BY CATEGORY ====================
print("\n\n🏷️  TEST 4: Filter Items by Category")
print("-" * 80)

categories = ["Dairy", "Vegetables", "Cooking Essentials"]
for category in categories:
    response = requests.get(f"{BASE_URL}/items?category={category}")
    if response.status_code == 200:
        items = response.json()
        print(f"✅ {category}: {len(items)} items")
        for item in items:
            print(f"   - {item['name']}: {item['current_stock']} {item['unit']}")
    else:
        print(f"❌ Failed for {category}")

# ==================== TEST 5: GET ONLY LOW STOCK ITEMS ====================
print("\n\n📉 TEST 5: Filter Low Stock Only")
print("-" * 80)

response = requests.get(f"{BASE_URL}/items?low_stock_only=true")
if response.status_code == 200:
    low_stock_items = response.json()
    print(f"✅ Found {len(low_stock_items)} low stock items:")
    for item in low_stock_items:
        percentage = (item['current_stock'] / item['reorder_level']) * 100
        print(f"   🔴 {item['name']}: {item['current_stock']}/{item['reorder_level']} "
              f"{item['unit']} ({percentage:.1f}% of reorder level)")
else:
    print(f"❌ Failed: {response.status_code}")

# ==================== TEST 6: GET SINGLE INVENTORY ITEM ====================
print("\n\n🔍 TEST 6: Get Single Inventory Item Details")
print("-" * 80)

if created_items:
    # Get the first created item's ID
    first_item_id = created_items[0]['id']
    response = requests.get(f"{BASE_URL}/items/{first_item_id}")
    if response.status_code == 200:
        item = response.json()
        print(f"✅ Retrieved item details:")
        print(f"   Name: {item['name']}")
        print(f"   Category: {item['category']}")
        print(f"   Current Stock: {item['current_stock']} {item['unit']}")
        print(f"   Reorder Level: {item['reorder_level']} {item['unit']}")
        print(f"   Unit Cost: ₹{item['unit_cost']}")
        print(f"   Total Value: ₹{item['inventory_value']:.2f}")
        print(f"   Supplier: {item.get('supplier', 'N/A')}")
        print(f"   Status: {item['status']}")
    else:
        print(f"❌ Failed: {response.status_code}")

# ==================== TEST 7: UPDATE INVENTORY ITEM ====================
print("\n\n✏️  TEST 7: Update Inventory Item (Add Stock)")
print("-" * 80)

if created_items:
    first_item_id = created_items[0]['id']
    update_data = {
        "current_stock": 10.0,  # Increased stock
        "unit_cost": 460  # Updated price
    }
    
    response = requests.put(f"{BASE_URL}/items/{first_item_id}", json=update_data)
    if response.status_code == 200:
        print(f"✅ Updated item successfully")
        
        # Verify the update
        verify_response = requests.get(f"{BASE_URL}/items/{first_item_id}")
        if verify_response.status_code == 200:
            updated_item = verify_response.json()
            print(f"   New Stock: {updated_item['current_stock']} {updated_item['unit']}")
            print(f"   New Unit Cost: ₹{updated_item['unit_cost']}")
            print(f"   New Total Value: ₹{updated_item['inventory_value']:.2f}")
    else:
        print(f"❌ Failed: {response.status_code}")

# ==================== TEST 8: CALCULATE TOTAL INVENTORY VALUE ====================
print("\n\n💰 TEST 8: Calculate Total Inventory Value")
print("-" * 80)

response = requests.get(f"{BASE_URL}/items")
if response.status_code == 200:
    all_items = response.json()
    
    total_value = 0
    category_values = {}
    
    for item in all_items:
        item_value = item['current_stock'] * item['unit_cost']
        total_value += item_value
        
        category = item['category']
        if category not in category_values:
            category_values[category] = 0
        category_values[category] += item_value
    
    print(f"✅ Total Inventory Value: ₹{total_value:.2f}")
    print("\nValue by Category:")
    for category, value in category_values.items():
        percentage = (value / total_value) * 100
        print(f"   {category}: ₹{value:.2f} ({percentage:.1f}%)")

# ==================== TEST 9: FILTER ACTIVE ITEMS ====================
print("\n\n✅ TEST 9: Filter Active Items Only")
print("-" * 80)

response = requests.get(f"{BASE_URL}/items?status=active")
if response.status_code == 200:
    active_items = response.json()
    print(f"✅ Active items: {len(active_items)}")
else:
    print(f"❌ Failed: {response.status_code}")

# ==================== SUMMARY ====================
print("\n\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)

response = requests.get(f"{BASE_URL}/items")
if response.status_code == 200:
    all_items = response.json()
    
    low_stock_response = requests.get(f"{BASE_URL}/alerts/low-stock")
    low_stock_data = low_stock_response.json() if low_stock_response.status_code == 200 else {}
    
    total_value = sum(item['current_stock'] * item['unit_cost'] for item in all_items)
    
    print(f"✅ Total Items: {len(all_items)}")
    print(f"⚠️  Low Stock Items: {low_stock_data.get('count', 0)}")
    print(f"🚨 Critical Items: {low_stock_data.get('critical_count', 0)}")
    print(f"💰 Total Inventory Value: ₹{total_value:.2f}")
    print(f"📦 Categories: {len(set(item['category'] for item in all_items))}")

print("\n" + "=" * 80)
print("✅ ALL TESTS COMPLETED!")
print("=" * 80)
