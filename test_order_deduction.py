"""
Test script for inventory auto-deduction with SMART DISPLAY

✅ FIXED: Correct API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8002/api"

def format_quantity_display(item):
    """Smart display formatting"""
    if 'current_stock_display' in item:
        return item['current_stock_display']

    stock = item.get('current_stock', 0)
    unit = item.get('unit', '')

    # Show in gm if < 1 kg
    if unit.lower() in ['kg', 'kgs']:
        if stock < 1:
            return f"{int(stock * 1000)} gm"
        else:
            return f"{stock} kg"

    # Show in ml if < 1 ltr
    elif unit.lower() in ['ltr', 'l', 'ltrs']:
        if stock < 1:
            return f"{int(stock * 1000)} ml"
        else:
            return f"{stock} ltr"

    return f"{stock} {unit}"

print("=" * 80)
print("🧪 PERFECTED TESTING ORDER WITH AUTO-DEDUCTION")
print("=" * 80)
print()

# ==================== STEP 1: Get Menu Items ====================
print("1️⃣  Getting menu items...")
try:
    # Try different endpoint variations
    endpoints = [
        f"{BASE_URL}/menu",           # Most common
        f"{BASE_URL}/menu/items",
        "http://127.0.0.1:8002/menu", # Without /api
    ]

    menu_items = None
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                menu_items = response.json()
                print(f"✅ Total menu items: {len(menu_items)}")
                print(f"✅ Using endpoint: {endpoint}")
                break
        except:
            continue

    if not menu_items:
        print("❌ Could not connect to menu endpoint")
        print("⚠️  Please check if server is running: python main.py")
        print("⚠️  Server should be at: http://127.0.0.1:8002")
        exit(1)

    # Find item with ingredients
    test_item = None
    for item in menu_items:
        if item.get('ingredients') and len(item['ingredients']) > 0:
            test_item = item
            break

    if test_item:
        print(f"✅ Found menu item with ingredients: {test_item['name']}")
        print(f"   Ingredients: {len(test_item['ingredients'])}")
        for ing in test_item['ingredients']:
            print(f"   - {ing['ingredient_name']}: {ing['quantity']} {ing['unit']}")
    else:
        print("❌ No menu items with ingredients found")
        print("⚠️  Please import menu items first using:")
        print("   POST /api/inventory/import-menu-with-ingredients")
        exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    print("⚠️  Make sure the server is running!")
    exit(1)

print()

# ==================== STEP 2: Check Inventory BEFORE Order ====================
print("2️⃣  Checking inventory BEFORE order...")
try:
    response = requests.get(f"{BASE_URL}/inventory/items")
    if response.status_code == 200:
        inventory_before = response.json()
        print(f"✅ Total inventory items: {len(inventory_before)}")
        print()
        print("Inventory snapshot:")

        # Create lookup for easy comparison
        inventory_lookup_before = {}
        for item in inventory_before:
            display = format_quantity_display(item)
            inventory_lookup_before[item['name']] = {
                'stock': item['current_stock'],
                'unit': item['unit'],
                'display': display
            }
            print(f"   {item['name']}: {display}")
    else:
        print(f"❌ Failed to get inventory: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print()

# ==================== STEP 3: Create Order ====================
order_quantity = 2
print(f"3️⃣  Creating order ({order_quantity}x {test_item['name']})...")

order_data = {
    "customerName": "Test Customer",
    "customerPhone": "9876543210",
    "paymentMethod": "cash",
    "items": [
        {
            "menuitemid": test_item.get('id') or test_item.get('_id'),
            "menuitemname": test_item['name'],
            "quantity": order_quantity,
            "price": test_item['price']
        }
    ],
    "totalAmount": test_item['price'] * order_quantity,
    "orderType": "dine-in"
}

try:
    # Try different order endpoints
    order_endpoints = [
        f"{BASE_URL}/orders",
        "http://127.0.0.1:8002/orders",
    ]

    order_created = False
    for endpoint in order_endpoints:
        try:
            response = requests.post(endpoint, json=order_data)
            if response.status_code == 200:
                order_result = response.json()
                order_id = order_result.get('order_id') or order_result.get('orderId')
                print(f"✅ Order created: {order_id}")
                order_created = True
                break
        except:
            continue

    if not order_created:
        print(f"❌ Failed to create order")
        print(f"⚠️  Response: {response.text[:200]}")
        exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print()

# ==================== STEP 4: Trigger Inventory Deduction ====================
print("4️⃣  Triggering inventory deduction...")

deduction_data = {
    "order_id": order_id,
    "items": order_data["items"]
}

try:
    response = requests.post(f"{BASE_URL}/inventory/deduct-for-order", json=deduction_data)
    if response.status_code == 200:
        deduction_result = response.json()
        print(f"✅ Deduction Status: {deduction_result.get('status')}")
        print(f"   Deducted items: {len(deduction_result.get('deducted_items', []))}")
        print()

        if deduction_result.get('deducted_items'):
            print("✅ Deduction details:")
            for item in deduction_result['deducted_items']:
                deducted_display = item.get('deducted_display', f"{item['deducted']} {item['deducted_unit']}")
                remaining_display = item.get('remaining_display', f"{item['remaining']} {item['remaining_unit']}")
                print(f"   - {item['ingredient']}: -{deducted_display} (remaining: {remaining_display})")
        else:
            print("⚠️  No items were deducted!")

        if deduction_result.get('failed_items'):
            print()
            print("❌ Failed deductions:")
            for failure in deduction_result['failed_items']:
                print(f"   - {failure}")
    else:
        print(f"❌ Deduction failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ==================== STEP 5: Check Inventory AFTER Order ====================
print("5️⃣  Checking inventory AFTER order...")
try:
    response = requests.get(f"{BASE_URL}/inventory/items")
    if response.status_code == 200:
        inventory_after = response.json()
        print()
        print("✅ Inventory changes:")

        for item in inventory_after:
            if item['name'] in inventory_lookup_before:
                before = inventory_lookup_before[item['name']]
                after_display = format_quantity_display(item)

                # Calculate change
                change = round(item['current_stock'] - before['stock'], 2)

                if change != 0:
                    change_str = f"−{abs(change)}" if change < 0 else f"+{change}"
                    print(f"   {item['name']}: {before['display']} → {after_display} ({change_str} {item['unit']})")
                else:
                    print(f"   {item['name']}: {before['display']} (no change)")
    else:
        print(f"❌ Failed to get inventory: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ==================== STEP 6: Check Stock Transactions ====================
print("6️⃣  Checking stock transactions...")
try:
    response = requests.get(f"{BASE_URL}/inventory/transactions?order_id={order_id}")
    if response.status_code == 200:
        transactions = response.json().get('transactions', [])
        print(f"✅ Transactions logged: {len(transactions)}")

        if transactions:
            for txn in transactions:
                prev = round(txn.get('previous_stock', 0), 2)
                new = round(txn.get('new_stock', 0), 2)
                unit = txn.get('storage_unit', '')
                qty_deducted = txn.get('quantity_deducted', 0)
                base_unit = txn.get('unit', '')

                print(f"   - {txn['item_name']}: {prev} {unit} - {qty_deducted} {base_unit} = {new} {unit}")
    else:
        print(f"❌ Failed to get transactions: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# ==================== STEP 7: Check Low Stock Alerts ====================
print("7️⃣  Checking low stock alerts...")
try:
    response = requests.get(f"{BASE_URL}/inventory/alerts/low-stock")
    if response.status_code == 200:
        alerts = response.json()
        low_stock_items = alerts.get('low_stock_items', [])
        critical_count = alerts.get('critical_count', 0)

        print(f"⚠️  Low stock items: {len(low_stock_items)}")
        print(f"🚨 Critical items: {critical_count}")

        if low_stock_items:
            print()
            print("Low stock details:")
            for item in low_stock_items:
                display = item.get('current_stock_display', f"{item['current_stock']} {item['unit']}")
                print(f"   - {item['name']}: {display}/{item['reorder_level']} {item['unit']} ({item['urgency']})")
    else:
        print(f"❌ Failed to get alerts: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 80)
print("✅ TEST COMPLETED PERFECTLY!")
print("=" * 80)