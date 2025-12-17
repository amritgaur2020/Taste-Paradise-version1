"""
Taste Paradise API - Cloud Deployment Version
Simplified for Render.com deployment
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import uuid
import secrets
import asyncio

from fastapi import FastAPI, APIRouter, HTTPException, Form, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from passlib.context import CryptContext
import pandas as pd
from io import BytesIO
from enum import Enum
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Import payment routes
from routes.payment_routes import router as payment_router, init_payment_routes

# Fix for MongoDB URI environment variable
if not os.getenv('MONGODB_URI'):
    if os.getenv('MONGODB_URL'):
        os.environ['MONGODB_URI'] = os.getenv('MONGODB_URL')

# ==================== CONFIG ====================
IST = pytz.timezone('Asia/Kolkata')

# Get MongoDB URI from environment variable
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("❌ MONGODB_URI environment variable is not set!")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global database connection
mongo_client = None
db = None

# ==================== ENUMS ====================
class OrderStatus(str, Enum):
    PENDING = "pending"
    COOKING = "cooking"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"

class PaymentMethod(str, Enum):
    CASH = "cash"
    ONLINE = "online"

class KitchenStatus(str, Enum):
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"

class TableStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"

# ==================== MODELS ====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

class OrderItem(BaseModel):
    menu_item_id: str
    menu_item_name: str
    quantity: int
    price: float
    special_instructions: str = ""

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    price: float
    category: str
    image_url: Optional[str] = None
    is_available: bool = True
    preparation_time: int = 15
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MenuItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    category: str
    image_url: Optional[str] = None
    preparation_time: int = 15

def generate_order_id():
    """Generate a short 8-character order ID"""
    return secrets.token_hex(4)

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = Field(default_factory=generate_order_id)
    customer_name: str = ""
    table_number: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    gst_applicable: bool = False
    gst_amount: float = 0.0
    final_amount: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_completion: Optional[datetime] = None
    kot_generated: bool = False

class OrderCreate(BaseModel):
    customer_name: str = ""
    table_number: Optional[str] = None
    items: List[OrderItem]
    gst_applicable: bool = False

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    table_number: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    total_amount: Optional[float] = None
    gst_applicable: Optional[bool] = None
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = Field(default=None, alias="paymentStatus")
    payment_method: Optional[PaymentMethod] = Field(default=None, alias="paymentMethod")
    estimated_completion: Optional[datetime] = None
    kot_generated: Optional[bool] = None
    
    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True

class KOT(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    order_number: str
    table_number: Optional[str] = None
    items: List[OrderItem]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: OrderStatus = OrderStatus.PENDING

class DashboardStats(BaseModel):
    today_orders: int
    today_revenue: float
    pending_orders: int
    cooking_orders: int
    ready_orders: int
    served_orders: int
    kitchen_status: KitchenStatus
    pending_payments: int

class RestaurantTable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    table_number: str
    capacity: int = 4
    status: TableStatus = TableStatus.AVAILABLE
    current_order_id: Optional[str] = None
    position_x: int = 0
    position_y: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TableCreate(BaseModel):
    table_number: str
    capacity: int = 4
    position_x: int = 0
    position_y: int = 0

class TableUpdate(BaseModel):
    status: Optional[TableStatus] = None
    current_order_id: Optional[str] = None

class DailyReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    revenue: float = 0.0
    orders: int = 0
    kots: int = 0
    bills: int = 0
    invoices: int = 0
    orders_list: List[Order] = []
    kots_list: List[KOT] = []
    bills_list: List[Order] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== HELPER FUNCTIONS ====================
def prepare_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to ISO strings for MongoDB"""
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
        elif isinstance(v, list):
            data[k] = [prepare_for_mongo(i) if isinstance(i, dict) else i for i in v]
    return data

def parse_from_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse MongoDB document back to proper types"""
    if '_id' in data:
        del data['_id']
    
    for k, v in data.items():
        if isinstance(v, str) and k.endswith(('_at', 'completion')):
            try:
                data[k] = datetime.fromisoformat(v.replace('Z', '+00:00'))
            except Exception:
                pass
        elif isinstance(v, list):
            data[k] = [parse_from_mongo(i) if isinstance(i, dict) else i for i in v]
    return data

# ==================== FASTAPI APP ====================
app = FastAPI(title="Taste Paradise API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    global mongo_client, db
    logger.info("Connecting to MongoDB...")
    try:
        mongo_client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
        # Try to ping but don't crash if it fails
        mongo_client.admin.command('ping')
        db = mongo_client['taste_paradise']
        logger.info("✅ MongoDB connected successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.warning("⚠️  Server starting WITHOUT MongoDB connection!")
        mongo_client = None
        db = None

        
        # Initialize payment routes
        init_payment_routes(db)
        logger.info("✅ Payment routes initialized!")
        
        # Start scheduler for daily reset
        try:
            if not scheduler.get_job('daily_reset'):
                scheduler.add_job(
                    daily_reset,
                    "cron",
                    hour=0,
                    minute=0,
                    second=0,
                    id="daily_reset",
                    replace_existing=True
                )
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        
        if not scheduler.running:
            scheduler.start()
            logger.info("✅ Scheduler started - daily reset scheduled for midnight")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    try:
        if scheduler.running:
            scheduler.shutdown()
        if mongo_client:
            mongo_client.close()
        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def daily_reset():
    """Daily reset job"""
    try:
        logger.info("Running daily reset...")
        today = datetime.now(timezone.utc).date().isoformat()
        await db.daily_reports.delete_one({"date": today})
        logger.info(f"Daily reset completed for {today}")
    except Exception as e:
        logger.error(f"Error in daily reset: {str(e)}")

# ==================== HEALTH CHECK ====================
@app.get("/")
async def root():
    return {"status": "ok", "message": "Taste Paradise API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    try:
        await mongo_client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# ==================== MENU ENDPOINTS ====================
@api_router.post("/menu", response_model=MenuItem)
async def create_menu_item(item: MenuItemCreate):
    menu_item = MenuItem(**item.model_dump())
    item_dict = prepare_for_mongo(menu_item.model_dump())
    await db.menu_items.insert_one(item_dict)
    return menu_item

@api_router.get("/menu", response_model=List[MenuItem])
async def get_menu():
    items_cursor = db.menu_items.find({})
    menu_items = []
    async for item in items_cursor:
        menu_items.append(MenuItem(**parse_from_mongo(item)))
    return menu_items

@api_router.put("/menu/{menu_item_id}", response_model=MenuItem)
async def update_menu_item(menu_item_id: str, item: MenuItemCreate = Body(...)):
    updated = await db.menu_items.find_one_and_update(
        {"id": menu_item_id},
        {"$set": item.model_dump()},
        return_document=True
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return MenuItem(**parse_from_mongo(updated))

@api_router.delete("/menu/{menu_item_id}")
async def delete_menu_item(menu_item_id: str):
    result = await db.menu_items.delete_one({"id": menu_item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"message": "Menu item deleted successfully"}

# ==================== EXCEL IMPORT/EXPORT ====================
@api_router.get("/menu/template")
async def download_template():
    """Download Excel template for bulk menu import"""
    try:
        data = {
            'name': ['Paneer Tikka', 'Butter Chicken', 'Dal Makhani', 'Naan', 'Gulab Jamun'],
            'description': [
                'Cottage cheese marinated in spices',
                'Chicken in rich tomato gravy',
                'Black lentils in creamy sauce',
                'Indian flatbread',
                'Sweet milk-solid dumplings'
            ],
            'price': [250.00, 350.00, 180.00, 40.00, 80.00],
            'category': ['Starters', 'Main Course', 'Main Course', 'Breads', 'Desserts'],
            'preparation_time': [20, 30, 25, 10, 15]
        }
        
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Menu Items', index=False)
        
        output.seek(0)
        
        return Response(
            content=output.read(),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': 'attachment; filename=menu_template.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@api_router.post("/menu/import")
async def import_menu(file: UploadFile = File(...)):
    """Import menu items from Excel file"""
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are allowed"
            )
        
        contents = await file.read()
        df = pd.DataFrame(pd.read_excel(BytesIO(contents)))
        
        required_columns = ['name', 'category', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                existing_item = await db.menu_items.find_one({"name": row['name']})
                if existing_item:
                    skipped_count += 1
                    continue
                
                menu_item = {
                    "id": str(uuid.uuid4()),
                    "name": str(row['name']),
                    "description": str(row.get('description', '')),
                    "price": float(row['price']),
                    "category": str(row['category']),
                    "image_url": str(row.get('image_url', '')) if pd.notna(row.get('image_url')) else None,
                    "is_available": True,
                    "preparation_time": int(row.get('preparation_time', 15)),
                    "created_at": datetime.now(timezone.utc)
                }
                
                await db.menu_items.insert_one(prepare_for_mongo(menu_item))
                imported_count += 1
                
            except Exception as e:
                error_msg = f"Row {index + 2}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        result = {
            "imported": imported_count,
            "skipped": skipped_count,
            "total_rows": len(df),
            "errors": errors[:10]
        }
        
        logger.info(f"Import complete: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing menu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ==================== ORDER ENDPOINTS ====================
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    total_amount = sum(i.quantity * i.price for i in order_data.items)
    
    gst_amount = 0.0
    final_amount = total_amount
    if order_data.gst_applicable:
        gst_amount = round(total_amount * 0.05, 2)
        final_amount = round(total_amount + gst_amount, 2)
    
    max_prep_time = 30
    for i in order_data.items:
        menu_item = await db.menu_items.find_one({"id": i.menu_item_id})
        if menu_item:
            max_prep_time = max(max_prep_time, menu_item.get('preparation_time', 15))
    
    estimated_completion = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=max_prep_time)
    now_ist = datetime.now(IST)
    
    order = Order(
        **order_data.model_dump(),
        total_amount=total_amount,
        gst_amount=gst_amount,
        final_amount=final_amount,
        estimated_completion=estimated_completion,
        created_at=now_ist,
        updated_at=now_ist
    )
    
    order_dict = prepare_for_mongo(order.model_dump())
    await db.orders.insert_one(order_dict)
    
    if order.table_number:
        await db.tables.update_one(
            {"table_number": order.table_number},
            {"$set": {"status": "occupied", "current_order_id": order.id}},
        )
    
    return order

@api_router.get("/orders", response_model=List[Order])
async def get_orders():
    orders_cursor = db.orders.find().sort("_id", -1)
    orders = []
    async for order in orders_cursor:
        orders.append(Order(**parse_from_mongo(order)))
    return orders

@api_router.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, order_data: OrderUpdate = Body(...)):
    try:
        order_dict = order_data.model_dump(exclude_unset=True)
        
        if "items" in order_dict or "gst_applicable" in order_dict:
            current_order = await db.orders.find_one({"id": order_id})
            if not current_order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            items = order_dict.get("items", current_order.get("items", []))
            gst_applicable = order_dict.get("gst_applicable", current_order.get("gst_applicable", False))
            
            total_amount = sum(item.get("quantity", 0) * item.get("price", 0) for item in items)
            gst_amount = 0.0
            final_amount = total_amount
            
            if gst_applicable:
                gst_amount = round(total_amount * 0.05, 2)
                final_amount = round(total_amount + gst_amount, 2)
            
            order_dict["total_amount"] = total_amount
            order_dict["gst_amount"] = gst_amount
            order_dict["final_amount"] = final_amount
            order_dict["estimated_completion"] = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=30)
        
        order_dict["updated_at"] = datetime.now(timezone.utc)
        
        updated = await db.orders.find_one_and_update(
            {"id": order_id},
            {"$set": order_dict},
            return_document=True
        )
        
        if updated is None:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return Order(**parse_from_mongo(updated))
        
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

@api_router.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    result = await db.orders.delete_one({"id": order_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

@api_router.put("/orders/{order_id}/pay")
async def pay_order(order_id: str, payment_data: dict = Body(...)):
    payment_status = payment_data.get('payment_status', 'paid')
    payment_method = payment_data.get('payment_method')
    
    update_data = {
        "payment_status": payment_status,
        "payment_method": payment_method,
        "status": OrderStatus.SERVED.value,
        "updated_at": datetime.now(timezone.utc)
    }
    
    updated = await db.orders.find_one_and_update(
        {"id": order_id},
        {"$set": update_data},
        return_document=True
    )
    
    if updated is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Payment processed", "order": parse_from_mongo(updated)}

@api_router.put("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    updated = await db.orders.find_one_and_update(
        {"id": order_id},
        {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )
    
    if updated is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order cancelled", "order": parse_from_mongo(updated)}

# ==================== KOT ENDPOINTS ====================
@api_router.post("/kot/{order_id}", response_model=KOT)
async def generate_kot(order_id: str):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_obj = Order(**parse_from_mongo(order))
    kot_count = await db.kots.count_documents({}) + 1
    order_number = f"ORD-{kot_count:04d}"
    
    kot = KOT(
        order_id=order_id,
        order_number=order_number,
        table_number=order_obj.table_number,
        items=order_obj.items,
    )
    
    kot_dict = prepare_for_mongo(kot.model_dump())
    await db.kots.insert_one(kot_dict)
    await db.orders.update_one({"id": order_id}, {"$set": {"kot_generated": True}})
    
    return kot

@api_router.get("/kot", response_model=List[KOT])
async def get_kots():
    kots_cursor = db.kots.find().sort("created_at", -1)
    kots = []
    async for kot in kots_cursor:
        kots.append(KOT(**parse_from_mongo(kot)))
    return kots

# ==================== DASHBOARD ====================
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard():
    today = datetime.now(timezone.utc).date()
    
    orders_today = await db.orders.count_documents({"created_at": {"$gte": today.isoformat()}})
    
    pipeline = [
        {"$match": {"created_at": {"$gte": today.isoformat()}}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$final_amount"}}}
    ]
    revenue_result = await db.orders.aggregate(pipeline).to_list(length=1)
    total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0.0
    
    pending_orders = await db.orders.count_documents({"status": OrderStatus.PENDING.value})
    cooking_orders = await db.orders.count_documents({"status": OrderStatus.COOKING.value})
    ready_orders = await db.orders.count_documents({"status": OrderStatus.READY.value})
    served_orders = await db.orders.count_documents({"status": OrderStatus.SERVED.value})
    pending_payments = await db.orders.count_documents({"payment_status": PaymentStatus.PENDING.value})
    
    return DashboardStats(
        today_orders=orders_today,
        today_revenue=total_revenue,
        pending_orders=pending_orders,
        cooking_orders=cooking_orders,
        ready_orders=ready_orders,
        served_orders=served_orders,
        kitchen_status=KitchenStatus.ACTIVE,
        pending_payments=pending_payments,
    )

# ==================== PAYMENTS ====================
@api_router.get("/payments/{date}")
async def get_payments_by_date(date: str):
    """Get all paid orders for a specific date"""
    try:
        target_date = datetime.fromisoformat(date).date()
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        payments_query = {
            "created_at": {
                "$gte": start_datetime.isoformat(),
                "$lt": end_datetime.isoformat()
            },
            "payment_status": "paid"
        }
        
        payments_cursor = db.orders.find(payments_query).sort("created_at", -1)
        payments_list = []
        
        async for payment in payments_cursor:
            payments_list.append({
                "order_id": payment.get("order_id", "N/A"),
                "_id": str(payment["_id"]),
                "final_amount": payment.get("final_amount", 0),
                "payment_method": payment.get("payment_method", "N/A"),
                "payment_status": payment.get("payment_status", "N/A"),
                "created_at": payment.get("created_at"),
                "customer_name": payment.get("customer_name", "Walk-in"),
                "table_number": payment.get("table_number"),
                "items": payment.get("items", []),
                "total_amount": payment.get("total_amount", 0),
                "gst_amount": payment.get("gst_amount", 0),
                "gst_applicable": payment.get("gst_applicable", False)
            })
        
        return payments_list
        
    except Exception as e:
        logger.error(f"Error fetching payments for {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/payments/pending/{date}")
async def get_pending_orders(date: str):
    """Get all pending payment orders for a specific date"""
    try:
        target_date = datetime.fromisoformat(date).date()
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        pending_query = {
            "created_at": {
                "$gte": start_datetime.isoformat(),
                "$lt": end_datetime.isoformat()
            },
            "payment_status": "pending"
        }
        
        pending_cursor = db.orders.find(pending_query).sort("created_at", -1)
        pending_list = []
        
        async for order in pending_cursor:
            pending_list.append({
                "order_id": order.get("order_id", "N/A"),
                "id": str(order["_id"]),
                "total_amount": order.get("total_amount", 0),
                "final_amount": order.get("final_amount", 0),
                "payment_method": "pending",
                "payment_status": "pending",
                "created_at": order.get("created_at"),
                "customer_name": order.get("customer_name", "Walk-in"),
                "table_number": order.get("table_number"),
                "items": order.get("items", [])
            })
        
        return pending_list
        
    except Exception as e:
        logger.error(f"Error fetching pending orders for {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# ==================== TABLES ====================
@api_router.post("/tables", response_model=RestaurantTable)
async def create_table(table_data: TableCreate):
    table = RestaurantTable(**table_data.model_dump())
    table_dict = prepare_for_mongo(table.model_dump())
    await db.tables.insert_one(table_dict)
    return table

@api_router.get("/tables", response_model=List[RestaurantTable])
async def get_tables():
    tables_cursor = db.tables.find({})
    tables = []
    async for table in tables_cursor:
        tables.append(RestaurantTable(**parse_from_mongo(table)))
    return tables

@api_router.put("/tables/{table_id}", response_model=RestaurantTable)
async def update_table(table_id: str, table_data: TableUpdate = Body(...)):
    updated = await db.tables.find_one_and_update(
        {"id": table_id},
        {"$set": table_data.model_dump(exclude_unset=True)},
        return_document=True
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return RestaurantTable(**parse_from_mongo(updated))

@api_router.delete("/tables/{table_id}")
async def delete_table(table_id: str):
    result = await db.tables.delete_one({"id": table_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Table not found")
    return {"message": "Table deleted successfully"}


# ==================== REPORTS ====================
@api_router.get("/report")
async def get_daily_report(date: str):
    try:
        target_date = datetime.fromisoformat(date).date()
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        orders_query = {
            "created_at": {
                "$gte": start_datetime.isoformat(),
                "$lt": end_datetime.isoformat()
            }
        }
        
        orders_cursor = db.orders.find(orders_query)
        orders_list = []
        total_revenue = 0.0
        
        async for order in orders_cursor:
            parsed_order = parse_from_mongo(order)
            orders_list.append(parsed_order)
            if parsed_order.get("final_amount"):
                total_revenue += float(parsed_order.get("final_amount", 0))
        
        kots_query = {
            "created_at": {
                "$gte": start_datetime.isoformat(),
                "$lt": end_datetime.isoformat()
            }
        }
        kots_cursor = db.kots.find(kots_query)
        kots_list = []
        async for kot in kots_cursor:
            kots_list.append(parse_from_mongo(kot))
        
        bills_query = {
            "created_at": {
                "$gte": start_datetime.isoformat(),
                "$lt": end_datetime.isoformat()
            },
            "payment_status": "paid"
        }
        bills_cursor = db.orders.find(bills_query)
        bills_list = []
        async for bill in bills_cursor:
            bills_list.append(parse_from_mongo(bill))
        
        daily_report = DailyReport(
            date=date,
            revenue=total_revenue,
            orders=len(orders_list),
            kots=len(kots_list),
            bills=len(bills_list),
            invoices=len(bills_list),
            orders_list=orders_list,
            kots_list=kots_list,
            bills_list=bills_list
        )
        
        report_dict = prepare_for_mongo(daily_report.model_dump())
        report_dict["updated_at"] = datetime.now(timezone.utc)
        
        await db.daily_reports.replace_one(
            {"date": date},
            report_dict,
            upsert=True
        )
        
        logger.info(f"Daily report saved for {date}. Revenue: ₹{total_revenue}, Orders: {len(orders_list)}")
        return daily_report.model_dump()
        
    except Exception as e:
        logger.error(f"Error generating daily report for {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating daily report: {str(e)}")

@api_router.get("/reports")
async def get_all_reports():
    try:
        pipeline = [
            {"$sort": {"date": -1, "updated_at": -1}},
            {"$group": {"_id": "$date", "latest_report": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$latest_report"}},
            {"$sort": {"date": -1}}
        ]
        
        reports_cursor = db.daily_reports.aggregate(pipeline)
        reports = []
        async for report in reports_cursor:
            reports.append(parse_from_mongo(report))
        
        return reports
        
    except Exception as e:
        logger.error(f"Error fetching all reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching reports: {str(e)}")

# ==================== PRINT INVOICE ====================
@api_router.post("/print-invoice")
async def print_invoice(invoice_data: Dict[str, Any] = Body(...)):
    """Generate printable invoice HTML"""
    try:
        invoice_no = invoice_data.get('invoiceNo', 'N/A')
        customer_name = invoice_data.get('customerName', 'Walk-in Customer')
        table_no = invoice_data.get('tableNo', 'N/A')
        items = invoice_data.get('items', [])
        subtotal = invoice_data.get('subtotal', 0)
        gst = invoice_data.get('gst', 0)
        total = invoice_data.get('total', 0)
        
        # Generate simple HTML invoice
        html_content = f"""
        <html>
        <body>
            <h1>Taste Paradise</h1>
            <p>Invoice: {invoice_no}</p>
            <p>Customer: {customer_name}</p>
            <p>Table: {table_no}</p>
            <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <table>
                <tr><th>Item</th><th>Qty</th><th>Price</th><th>Amount</th></tr>
                {''.join([f"<tr><td>{item.get('name', '')}</td><td>{item.get('quantity', 0)}</td><td>₹{item.get('price', 0):.2f}</td><td>₹{(item.get('quantity', 0) * item.get('price', 0)):.2f}</td></tr>" for item in items])}
            </table>
            <hr>
            <p>Subtotal: ₹{subtotal:.2f}</p>
            <p>GST (5%): ₹{gst:.2f}</p>
            <h2>Total: ₹{total:.2f}</h2>
        </body>
        </html>
        """
        
        return {"html": html_content}
        
    except Exception as e:
        logger.error(f"Error generating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating invoice: {str(e)}")

# ==================== INCLUDE ROUTERS ====================
app.include_router(payment_router)
app.include_router(api_router)

# ==================== RUN (for local debug only) ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

