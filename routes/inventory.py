"""
Inventory Management System Routes with SMART UNIT CONVERSION & ROUNDING

✅ FIXES:
1. Proper decimal rounding (no 0.7000000000000001)
2. Smart display (700 gm instead of 0.7 kg for clarity)
3. Clean calculations with base units (gm, ml)

Handles:
- Menu items with ingredients
- Inventory stock management with unit conversion
- Auto-deduction (kg→gm, ltr→ml for precision)
- Low stock alerts
- Stock transactions logging
- Excel import/export
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Query, Body
from fastapi.responses import Response
import pandas as pd
from io import BytesIO
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

# This will be injected from main.py
db = None

router = APIRouter(prefix="/inventory", tags=["inventory"])

def set_db(database):
    """Set database reference from main.py"""
    global db
    db = database
    logger.info("✅ Inventory database reference set")

# ==================== SMART UNIT CONVERSION WITH ROUNDING ====================
def normalize_to_base_unit(quantity: float, unit: str) -> tuple:
    """
    Convert quantity to BASE UNIT (gm for weight, ml for volume)
    Returns: (normalized_quantity, base_unit)

    Examples:
    - 1.5 kg → (1500, 'gm')
    - 8 ltr → (8000, 'ml')
    - 100 gm → (100, 'gm')
    - 50 pieces → (50, 'pieces')
    """
    unit = unit.lower().strip()

    # Weight: Convert to grams (gm)
    if unit in ['kg', 'kgs', 'kilogram', 'kilograms']:
        return (round(quantity * 1000, 2), 'gm')  # Round to 2 decimals
    elif unit in ['gm', 'g', 'gms', 'gram', 'grams']:
        return (round(quantity, 2), 'gm')

    # Volume: Convert to milliliters (ml)
    elif unit in ['ltr', 'l', 'ltrs', 'litre', 'liter', 'litres', 'liters']:
        return (round(quantity * 1000, 2), 'ml')
    elif unit in ['ml', 'millilitre', 'milliliter', 'millilitres', 'milliliters']:
        return (round(quantity, 2), 'ml')

    # Count: No conversion
    elif unit in ['pieces', 'piece', 'pcs', 'pc', 'nos', 'no']:
        return (round(quantity, 2), 'pieces')

    # Unknown: Return as-is
    else:
        logger.warning(f"Unknown unit: {unit}, treating as base unit")
        return (round(quantity, 2), unit)

def convert_from_base_unit(quantity: float, base_unit: str, target_unit: str) -> float:
    """
    Convert from BASE UNIT back to TARGET UNIT with proper rounding

    Examples:
    - 1500 gm → kg = 1.5 kg
    - 700 gm → kg = 0.7 kg
    - 8000 ml → ltr = 8 ltr
    """
    base_unit = base_unit.lower().strip()
    target_unit = target_unit.lower().strip()

    # Same unit
    if base_unit == target_unit:
        return round(quantity, 2)

    # Convert gm → kg
    if base_unit == 'gm' and target_unit in ['kg', 'kgs', 'kilogram', 'kilograms']:
        return round(quantity / 1000, 2)  # Round to 2 decimals

    # Convert ml → ltr
    if base_unit == 'ml' and target_unit in ['ltr', 'l', 'ltrs', 'litre', 'liter', 'litres', 'liters']:
        return round(quantity / 1000, 2)

    # No conversion needed
    return round(quantity, 2)

def format_quantity_smart(quantity: float, unit: str) -> str:
    """
    Smart formatting: Show in smaller unit if less than 1 of larger unit

    Examples:
    - 0.7 kg → "700 gm" (easier to read)
    - 1.5 kg → "1.5 kg" (keep as is)
    - 0.04 ltr → "40 ml"
    - 8 ltr → "8 ltr"
    """
    unit = unit.lower().strip()

    # Weight: Show in gm if < 1 kg
    if unit in ['kg', 'kgs', 'kilogram', 'kilograms']:
        if quantity < 1:
            gm_value = round(quantity * 1000, 0)  # No decimals for gm
            return f"{int(gm_value)} gm"
        else:
            return f"{quantity} kg"

    # Volume: Show in ml if < 1 ltr
    elif unit in ['ltr', 'l', 'ltrs', 'litre', 'liter', 'litres', 'liters']:
        if quantity < 1:
            ml_value = round(quantity * 1000, 0)
            return f"{int(ml_value)} ml"
        else:
            return f"{quantity} ltr"

    # Other units: Show as-is
    else:
        return f"{quantity} {unit}"

# ==================== INITIALIZE COLLECTIONS ====================
async def initialize_collections():
    """Initialize inventory collections if they don't exist"""
    global db
    if db is None:
        logger.error("Database not initialized")
        return

    try:
        # Get existing collections
        collections = await db.list_collection_names()

        # Create inventory_items collection if missing
        if 'inventory_items' not in collections:
            await db.create_collection('inventory_items')
            logger.info("✅ Created inventory_items collection")

        # Create stock_transactions collection if missing
        if 'stock_transactions' not in collections:
            await db.create_collection('stock_transactions')
            logger.info("✅ Created stock_transactions collection")

        logger.info("✅ Inventory collections initialized")

    except Exception as e:
        logger.error(f"Error initializing inventory collections: {e}")
        raise

@router.get("/template")
async def download_inventory_template():
    """Download Excel template for bulk inventory import"""
    try:
        import pandas as pd
        from io import BytesIO
        from fastapi.responses import Response
        
        # Create sample template data
        template_data = {
            'name': ['Butter', 'Paneer', 'Chicken', 'Tomato', 'Onion'],
            'category': ['Dairy', 'Dairy', 'Meat', 'Vegetables', 'Vegetables'],
            'unit': ['kg', 'kg', 'kg', 'kg', 'kg'],
            'current_stock': [5.0, 10.0, 15.0, 20.0, 8.0],
            'reorder_level': [2.0, 5.0, 5.0, 10.0, 5.0],
            'unit_cost': [400.0, 350.0, 280.0, 40.0, 30.0],
            'supplier': ['ABC Dairy', 'ABC Dairy', 'Fresh Meat Co', 'Veggie Mart', 'Veggie Mart'],
            'supplier_contact': ['+91 98765 43210', '+91 98765 43210', '+91 98765 43211', '+91 98765 43212', '+91 98765 43212']
        }
        
        df = pd.DataFrame(template_data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Set column widths
            worksheet = writer.sheets['Inventory']
            worksheet.column_dimensions['A'].width = 20
            worksheet.column_dimensions['B'].width = 15
            worksheet.column_dimensions['C'].width = 10
            worksheet.column_dimensions['D'].width = 15
            worksheet.column_dimensions['E'].width = 15
            worksheet.column_dimensions['F'].width = 12
            worksheet.column_dimensions['G'].width = 20
            worksheet.column_dimensions['H'].width = 20
        
        output.seek(0)
        
        return Response(
            content=output.read(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': 'attachment; filename=inventory_template.xlsx'
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating inventory template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IMPORT INVENTORY ITEMS FROM EXCEL ====================
@router.post("/import-inventory-items")
async def import_inventory_items(file: UploadFile = File(...)):
    """
    Import inventory items from Excel

    Excel Format Expected:
    | name | category | unit | current_stock | reorder_level | unit_cost | supplier | supplier_contact |
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are supported"
            )

        # Read Excel file
        content = await file.read()
        df = pd.read_excel(BytesIO(content))

        # Validate required columns
        required_columns = ['name', 'category', 'unit', 'current_stock', 'reorder_level', 'unit_cost']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )

        imported_count = 0
        updated_count = 0

        for idx, row in df.iterrows():
            try:
                if pd.isna(row['name']):
                    continue

                item_data = {
                    "name": str(row['name']).strip(),
                    "category": str(row['category']).strip(),
                    "unit": str(row['unit']).strip(),
                    "current_stock": round(float(row['current_stock']), 2),
                    "reorder_level": round(float(row['reorder_level']), 2),
                    "unit_cost": round(float(row['unit_cost']), 2),
                    "supplier": str(row.get('supplier', '')),
                    "supplier_contact": str(row.get('supplier_contact', '')),
                    "status": "active",
                    "last_updated": datetime.now(timezone.utc)
                }

                # Check if item exists
                existing = await db.inventory_items.find_one(
                    {"name": {"$regex": f"^{item_data['name']}$", "$options": "i"}}
                )

                if existing:
                    # Update existing
                    await db.inventory_items.update_one(
                        {"_id": existing["_id"]},
                        {"$set": item_data}
                    )
                    updated_count += 1
                else:
                    # Insert new
                    item_data["created_at"] = datetime.now(timezone.utc)
                    await db.inventory_items.insert_one(item_data)
                    imported_count += 1

            except Exception as e:
                logger.error(f"Error processing row {idx+2}: {e}")
                continue

        return {
            "message": "Inventory items imported successfully",
            "imported": imported_count,
            "updated": updated_count,
            "total": imported_count + updated_count,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== IMPORT MENU WITH INGREDIENTS FROM EXCEL ====================
@router.post("/import-menu-with-ingredients")
async def import_menu_with_ingredients(file: UploadFile = File(...)):
    """
    Import menu items from Excel WITH ingredients column

    Excel Format Expected:
    | name | price | category | food_type | preparationtime | ingredients |
    | Burger | 100 | Main | non-veg | 10 | Bun(2 pieces),Tikki(1 piece),Tomato(100 gm) |

    Ingredients format: "ingredient_name(quantity unit), ingredient_name(quantity unit)"
    Example: "Butter(200 gm), Paneer(500 gm), Tomato(3 pieces)"
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are supported"
            )

        # Read Excel file
        content = await file.read()
        df = pd.read_excel(BytesIO(content))

        # Validate required columns
        required_columns = ['name', 'price', 'category', 'ingredients']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}. Required: {required_columns}"
            )

        imported_items = []
        updated_items = []
        errors = []

        # Process each row
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row['name']):
                    continue

                # ============ PARSE INGREDIENTS ============
                ingredients_list = []

                if pd.notna(row['ingredients']) and str(row['ingredients']).strip():
                    ingredient_strings = str(row['ingredients']).split(',')

                    for ing_str in ingredient_strings:
                        ing_str = ing_str.strip()

                        # Parse format: "Bun(2 pieces)" or "Tomato(100 gm)"
                        if '(' in ing_str and ')' in ing_str:
                            try:
                                # Extract name and quantity/unit
                                name_part = ing_str[:ing_str.index('(')].strip()
                                quantity_unit = ing_str[ing_str.index('(')+1:ing_str.index(')')].strip()

                                # Split quantity and unit
                                parts = quantity_unit.split(maxsplit=1)
                                if len(parts) >= 2:
                                    quantity = float(parts[0])
                                    unit = parts[1]
                                else:
                                    quantity = float(parts[0]) if parts else 1
                                    unit = "pieces"

                                # Find inventory item (case-insensitive)
                                inventory_item = await db.inventory_items.find_one(
                                    {"name": {"$regex": name_part, "$options": "i"}}
                                )

                                if inventory_item:
                                    ingredients_list.append({
                                        "ingredient_id": str(inventory_item["_id"]),
                                        "ingredient_name": inventory_item["name"],
                                        "quantity": quantity,
                                        "unit": unit,
                                        "cost_per_unit": inventory_item.get("unit_cost", 0)
                                    })
                                    logger.info(f"Found ingredient: {name_part}")
                                else:
                                    errors.append(
                                        f"Row {idx+2}: Ingredient '{name_part}' not found in inventory. "
                                        f"Please add '{name_part}' to inventory first."
                                    )
                                    logger.warning(f"Ingredient not found: {name_part}")

                            except Exception as e:
                                errors.append(f"Row {idx+2}: Error parsing ingredient '{ing_str}': {str(e)}")
                        else:
                            errors.append(
                                f"Row {idx+2}: Invalid ingredient format. Use: 'name(quantity unit)'. Got: '{ing_str}'"
                            )

                # ============ CREATE/UPDATE MENU ITEM ============
                menu_item_data = {
                    "id": str(uuid.uuid4()),
                    "name": str(row['name']).strip(),
                    "price": float(row['price']),
                    "category": str(row['category']).strip(),
                    "food_type": str(row.get('food_type', 'veg')).strip(),
                    "ingredients": ingredients_list,
                    "preparation_time": int(row.get('preparationtime', 10)) if pd.notna(row.get('preparationtime')) else 10,
                    "description": str(row.get('description', '')),
                    "is_available": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                # Check if item already exists
                existing = await db.menu_items.find_one(
                    {"name": {"$regex": f"^{menu_item_data['name']}$", "$options": "i"}}
                )

                if existing:
                    # Update existing item
                    result = await db.menu_items.update_one(
                        {"_id": existing["_id"]},
                        {"$set": menu_item_data}
                    )

                    updated_items.append({
                        "id": str(existing["_id"]),
                        "name": row['name'],
                        "ingredients_count": len(ingredients_list),
                        "action": "updated"
                    })
                    logger.info(f"Updated menu item: {row['name']}")
                else:
                    # Create new item
                    result = await db.menu_items.insert_one(menu_item_data)

                    imported_items.append({
                        "id": str(result.inserted_id),
                        "name": row['name'],
                        "ingredients_count": len(ingredients_list),
                        "action": "created"
                    })
                    logger.info(f"Created menu item: {row['name']}")

            except Exception as e:
                logger.error(f"Error processing row {idx+2}: {str(e)}")
                errors.append(f"Row {idx+2}: {str(e)}")

        return {
            "message": "Menu items imported successfully",
            "imported_count": len(imported_items),
            "updated_count": len(updated_items),
            "imported_items": imported_items,
            "updated_items": updated_items,
            "errors": errors if errors else None,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing menu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import menu: {str(e)}")

# ==================== AUTO-DEDUCT INVENTORY (SMART CONVERSION + ROUNDING) ====================
@router.post("/deduct-for-order")
async def deduct_inventory_for_order(order_data: Dict = Body(...)):
    """
    Auto-deduct inventory with SMART unit conversion and proper rounding

    ✅ LOGIC:
    1. Convert inventory to BASE UNIT (kg→gm, ltr→ml)
    2. Compare and deduct in BASE UNIT (clean integers!)
    3. Convert back to original unit with proper rounding
    4. Smart display (700 gm instead of 0.7 kg)

    Example:
    - Inventory: 1.1 kg = 1100 gm
    - Recipe: 2 × 200 gm = 400 gm
    - Deduct: 1100 - 400 = 700 gm
    - Store: 700 gm = 0.7 kg (rounded)
    - Display: "700 gm" (clearer than 0.7 kg)
    """
    try:
        order_id = order_data.get('order_id')
        order_items = order_data.get('items', [])

        if not order_id or not order_items:
            raise HTTPException(status_code=400, detail="Missing order_id or items")

        deducted_items = []
        failed_items = []
        transactions = []

        for order_item in order_items:
            menu_item_id = order_item.get('menuitemid')
            menu_item_name = order_item.get('menuitemname', 'Unknown')
            order_quantity = int(order_item.get('quantity', 1))

            # Get menu item with ingredients
            menu_item = await db.menu_items.find_one({"id": menu_item_id})

            # Try with _id if not found by id
            if not menu_item:
                try:
                    menu_item = await db.menu_items.find_one({"_id": ObjectId(menu_item_id)})
                except:
                    pass

            if not menu_item or not menu_item.get('ingredients'):
                logger.warning(f"No ingredients found for {menu_item_name}")
                continue

            # Deduct each ingredient
            for ingredient in menu_item['ingredients']:
                ingredient_id = ingredient.get('ingredient_id')
                ingredient_name = ingredient.get('ingredient_name')
                required_quantity = ingredient.get('quantity', 0) * order_quantity
                recipe_unit = ingredient.get('unit')

                # Get inventory item
                try:
                    inv_item = await db.inventory_items.find_one({"_id": ObjectId(ingredient_id)})
                except:
                    inv_item = None

                if not inv_item:
                    failed_items.append(f"{ingredient_name}: Not found in inventory")
                    continue

                current_stock = inv_item.get('current_stock', 0)
                inventory_unit = inv_item.get('unit')

                # ✅ STEP 1: Convert inventory to BASE UNIT (kg→gm, ltr→ml)
                stock_in_base, base_unit = normalize_to_base_unit(current_stock, inventory_unit)

                # ✅ STEP 2: Convert recipe requirement to BASE UNIT
                required_in_base, required_base_unit = normalize_to_base_unit(required_quantity, recipe_unit)

                # ✅ STEP 3: Check units match
                if base_unit != required_base_unit:
                    failed_items.append(
                        f"{ingredient_name}: Unit mismatch (inventory: {base_unit}, recipe: {required_base_unit})"
                    )
                    continue

                logger.info(
                    f"🔄 Conversion: Inventory {current_stock} {inventory_unit} = {stock_in_base} {base_unit}, "
                    f"Need {required_quantity} {recipe_unit} = {required_in_base} {base_unit}"
                )

                # ✅ STEP 4: Check sufficient stock (comparing in BASE UNIT - clean!)
                if stock_in_base < required_in_base:
                    failed_items.append(
                        f"{ingredient_name}: Insufficient stock "
                        f"(need {required_in_base} {base_unit}, "
                        f"have {stock_in_base} {base_unit})"
                    )
                    continue

                # ✅ STEP 5: Deduct in BASE UNIT (clean calculation!)
                new_stock_in_base = round(stock_in_base - required_in_base, 2)

                # ✅ STEP 6: Convert back to ORIGINAL UNIT for storage (with rounding)
                new_stock_in_original = convert_from_base_unit(new_stock_in_base, base_unit, inventory_unit)

                # ✅ STEP 7: Smart display format
                display_deducted = format_quantity_smart(
                    convert_from_base_unit(required_in_base, base_unit, inventory_unit), 
                    inventory_unit
                )
                display_remaining = format_quantity_smart(new_stock_in_original, inventory_unit)

                logger.info(
                    f"✅ Deduction: {stock_in_base} - {required_in_base} = {new_stock_in_base} {base_unit} "
                    f"= {new_stock_in_original} {inventory_unit} ({display_remaining})"
                )

                # Update database
                await db.inventory_items.update_one(
                    {"_id": ObjectId(ingredient_id)},
                    {
                        "$set": {
                            "current_stock": new_stock_in_original,
                            "last_updated": datetime.now(timezone.utc)
                        }
                    }
                )

                # Log transaction
                transaction = {
                    "item_id": ingredient_id,
                    "item_name": ingredient_name,
                    "transaction_type": "order_deduction",
                    "quantity_deducted": required_in_base,
                    "unit": base_unit,
                    "previous_stock": current_stock,
                    "new_stock": new_stock_in_original,
                    "storage_unit": inventory_unit,
                    "order_id": order_id,
                    "menu_item": menu_item_name,
                    "recipe_quantity": required_quantity,
                    "recipe_unit": recipe_unit,
                    "transaction_date": datetime.now(timezone.utc),
                    "created_by": "system"
                }

                await db.stock_transactions.insert_one(transaction)
                transactions.append(transaction)

                deducted_items.append({
                    "ingredient": ingredient_name,
                    "deducted": required_in_base,
                    "deducted_unit": base_unit,
                    "deducted_display": display_deducted,
                    "remaining": new_stock_in_original,
                    "remaining_unit": inventory_unit,
                    "remaining_display": display_remaining,
                    "recipe_requested": f"{required_quantity} {recipe_unit}"
                })

                logger.info(
                    f"✅ Successfully deducted {display_deducted} "
                    f"of {ingredient_name} for order {order_id}. Remaining: {display_remaining}"
                )

        return {
            "message": "Inventory deduction completed",
            "order_id": order_id,
            "deducted_items": deducted_items,
            "failed_items": failed_items,
            "transactions_logged": len(transactions),
            "status": "success" if not failed_items else "partial_success"
        }

    except Exception as e:
        logger.error(f"Error deducting inventory: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CREATE INVENTORY ITEM ====================
@router.post("/items")
async def create_inventory_item(item_data: Dict = Body(...)):
    """Create a new inventory item (ingredient/stock)"""
    try:
        inventory_item = {
            **item_data,
            "current_stock": round(float(item_data.get("current_stock", 0)), 2),
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc)
        }

        result = await db.inventory_items.insert_one(inventory_item)
        logger.info(f"Created inventory item: {item_data.get('name')}")

        return {
            "id": str(result.inserted_id),
            "message": "Inventory item created successfully",
            "status": "success",
            "data": {
                "id": str(result.inserted_id),
                **item_data
            }
        }

    except Exception as e:
        logger.error(f"Error creating inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GET ALL INVENTORY ITEMS ====================
@router.get("/items")
async def get_inventory_items(
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    status: Optional[str] = Query("active")
):
    """Get all inventory items with optional filters"""
    try:
        query = {}
        if status:
            query["status"] = status
        if category:
            query["category"] = category

        items = await db.inventory_items.find(query).to_list(length=None)

        if low_stock_only:
            items = [
                item for item in items 
                if item["current_stock"] <= item["reorder_level"]
            ]

        formatted_items = []
        for item in items:
            formatted_items.append({
                "id": str(item["_id"]),
                "name": item["name"],
                "category": item["category"],
                "unit": item["unit"],
                "current_stock": round(item["current_stock"], 2),
                "current_stock_display": format_quantity_smart(item["current_stock"], item["unit"]),
                "reorder_level": round(item["reorder_level"], 2),
                "unit_cost": item.get("unit_cost", 0),
                "supplier": item.get("supplier"),
                "supplier_contact": item.get("supplier_contact"),
                "status": item.get("status", "active"),
                "inventory_value": round(item["current_stock"] * item.get("unit_cost", 0), 2),
                "last_updated": item.get("last_updated"),
                "created_at": item.get("created_at")
            })

        logger.info(f"Retrieved {len(formatted_items)} inventory items")
        return formatted_items

    except Exception as e:
        logger.error(f"Error fetching inventory items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GET SINGLE INVENTORY ITEM ====================
@router.get("/items/{item_id}")
async def get_inventory_item(item_id: str):
    """Get single inventory item by ID"""
    try:
        item = await db.inventory_items.find_one({"_id": ObjectId(item_id)})

        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        return {
            "id": str(item["_id"]),
            "name": item["name"],
            "category": item["category"],
            "unit": item["unit"],
            "current_stock": round(item["current_stock"], 2),
            "reorder_level": round(item["reorder_level"], 2),
            "unit_cost": item.get("unit_cost", 0),
            "supplier": item.get("supplier"),
            "supplier_contact": item.get("supplier_contact"),
            "status": item.get("status", "active"),
            "inventory_value": round(item["current_stock"] * item.get("unit_cost", 0), 2),
            "last_updated": item.get("last_updated"),
            "created_at": item.get("created_at")
        }

    except Exception as e:
        logger.error(f"Error fetching inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== UPDATE INVENTORY ITEM ====================
@router.put("/items/{item_id}")
async def update_inventory_item(item_id: str, item_data: Dict = Body(...)):
    """Update inventory item details"""
    try:
        if "current_stock" in item_data:
            item_data["current_stock"] = round(float(item_data["current_stock"]), 2)
        item_data["last_updated"] = datetime.now(timezone.utc)

        result = await db.inventory_items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": item_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        logger.info(f"Updated inventory item: {item_id}")
        return {"message": "Item updated successfully", "status": "success"}

    except Exception as e:
        logger.error(f"Error updating item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DELETE INVENTORY ITEM ====================
@router.delete("/items/{item_id}")
async def delete_inventory_item(item_id: str):
    """Soft delete inventory item (mark as inactive)"""
    try:
        result = await db.inventory_items.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {"status": "inactive", "last_updated": datetime.now(timezone.utc)}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        logger.info(f"Deleted inventory item: {item_id}")
        return {"message": "Item deleted successfully", "status": "success"}

    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GET LOW STOCK ALERTS ====================
@router.get("/alerts/low-stock")
async def get_low_stock_alerts():
    """Get items that are below reorder level"""
    try:
        items = await db.inventory_items.find({
            "status": "active",
            "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
        }).to_list(length=None)

        formatted_items = []
        critical_count = 0

        for item in items:
            if item["current_stock"] <= item["reorder_level"] * 0.5:
                urgency = "critical"
                critical_count += 1
            else:
                urgency = "warning"

            needed = max(0, item["reorder_level"] - item["current_stock"])

            formatted_items.append({
                "id": str(item["_id"]),
                "name": item["name"],
                "category": item["category"],
                "current_stock": round(item["current_stock"], 2),
                "current_stock_display": format_quantity_smart(item["current_stock"], item["unit"]),
                "reorder_level": round(item["reorder_level"], 2),
                "unit": item["unit"],
                "urgency": urgency,
                "needed": round(needed, 2),
                "supplier": item.get("supplier"),
                "supplier_contact": item.get("supplier_contact")
            })

        logger.info(f"Found {len(formatted_items)} low stock items")

        return {
            "low_stock_items": formatted_items,
            "count": len(formatted_items),
            "critical_count": critical_count,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching low stock alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GET STOCK TRANSACTIONS ====================
@router.get("/transactions")
async def get_stock_transactions(
    order_id: Optional[str] = Query(None),
    item_name: Optional[str] = Query(None),
    limit: int = Query(50, le=500)
):
    """Get stock transaction history"""
    try:
        query = {}
        if order_id:
            query["order_id"] = order_id
        if item_name:
            query["item_name"] = {"$regex": item_name, "$options": "i"}

        transactions = await db.stock_transactions.find(query).sort("transaction_date", -1).limit(limit).to_list(length=limit)

        formatted = []
        for txn in transactions:
            formatted.append({
                "id": str(txn.get("_id")),
                "item_name": txn.get("item_name"),
                "transaction_type": txn.get("transaction_type"),
                "quantity_deducted": txn.get("quantity_deducted"),
                "unit": txn.get("unit"),
                "previous_stock": round(txn.get("previous_stock", 0), 2),
                "new_stock": round(txn.get("new_stock", 0), 2),
                "storage_unit": txn.get("storage_unit"),
                "order_id": txn.get("order_id"),
                "menu_item": txn.get("menu_item"),
                "recipe_quantity": txn.get("recipe_quantity"),
                "recipe_unit": txn.get("recipe_unit"),
                "transaction_date": txn.get("transaction_date"),
                "created_by": txn.get("created_by")
            })

        return {
            "transactions": formatted,
            "count": len(formatted)
        }

    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== GET INVENTORY DASHBOARD STATS ====================
@router.get("/dashboard/stats")
async def get_inventory_dashboard_stats():
    """Get inventory dashboard statistics"""
    try:
        total_items = await db.inventory_items.count_documents({"status": "active"})

        low_stock_items = await db.inventory_items.count_documents({
            "status": "active",
            "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
        })

        all_items = await db.inventory_items.find({"status": "active"}).to_list(length=None)
        total_value = sum(item["current_stock"] * item.get("unit_cost", 0) for item in all_items)

        from datetime import timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_transactions = await db.stock_transactions.count_documents({
            "transaction_date": {"$gte": yesterday}
        })

        return {
            "total_items": total_items,
            "low_stock_items": low_stock_items,
            "total_inventory_value": round(total_value, 2),
            "recent_transactions": recent_transactions,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
