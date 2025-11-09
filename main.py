# Global flag to prevent double startup
app_started = False

# ==================== LICENSE SYSTEM ====================
from license_validator import OfflineLicenseValidator
# ========================================================

import os
import sys
from pathlib import Path

# STEP 1: Set environment variables FIRST - before ANY other imports
if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).parent
    runtime_dll = base_dir / "python313.dll"
    
    if runtime_dll.exists():
        dll_str = str(runtime_dll.resolve())
        # Set ALL required environment variables
        os.environ["PYTHONNET_PYDLL"] = dll_str
        os.environ["PYTHONNET_RUNTIME"] = "netfx"
        
        # Critical: Add DLL directory to PATH at the VERY beginning
        dll_dir = str(base_dir.resolve())
        current_path = os.environ.get("PATH", "")
        if dll_dir not in current_path:
            os.environ["PATH"] = dll_dir + os.pathsep + current_path
        
        # Also set PYTHONHOME to the application directory
        os.environ["PYTHONHOME"] = dll_dir
    else:
        sys.exit(1)
else:
    # Running as script
    python_dir = Path(sys.executable).parent
    runtime_dll = python_dir / f"python{sys.version_info.major}{sys.version_info.minor}.dll"
    if runtime_dll.exists():
        os.environ["PYTHONNET_PYDLL"] = str(runtime_dll.resolve())

# STEP 2: Force Python to reload sys module paths with new environment
import importlib
if hasattr(importlib, 'invalidate_caches'):
    importlib.invalidate_caches()

# STEP 3: NOW import pythonnet with the correct environment
try:
    from pythonnet import set_runtime
    set_runtime("netfx")
except Exception as e:
    error_file = base_dir / "pythonnet_init_error.txt" if getattr(sys, 'frozen', False) else Path("error.txt")
    with open(error_file, "w") as f:
        f.write(f"Failed to initialize pythonnet: {e}\n")
        f.write(f"PYTHONNET_PYDLL: {os.environ.get('PYTHONNET_PYDLL')}\n")
        f.write(f"PATH: {os.environ.get('PATH')}\n")
    sys.exit(1)

# STEP 4: NOW import webview
import webview
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# ... rest of your code


import os, sys, subprocess, time, threading, webview
import platform
import asyncio
from pathlib import Path
from fastapi import FastAPI, APIRouter, HTTPException, Form , Body, WebSocket, WebSocketDisconnect
from passlib.context import CryptContext
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from routes import payments
from fastapi import UploadFile, File
from fastapi.responses import Response
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import uvicorn
import secrets
from datetime import datetime, timedelta
import pytz 
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from routes.payment_routes import router as payment_router, init_payment_routes





# ==================== WEBSOCKET CONNECTION MANAGER ====================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()


# ==================== CONFIG ====================
IST = pytz.timezone('Asia/Kolkata')

if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).parent

MONGODB_BIN = APP_DIR / "mongodb" / "bin" / "mongod.exe"
MONGODB_DATA = APP_DIR / "mongodb" / "data"
STATIC_DIR = APP_DIR / "static"

mongodb_process = None
mongo_client = None
db = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
# ✨ NEW: Password hashing setup
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
    food_type: str = "veg"  
    is_custom_item: bool = False
    category: Optional[str] = "" 
    description: Optional[str] = ""
    taxable: bool = True  
    added_by: Optional[str] = ""
    added_at: Optional[datetime] = None

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    price: float
    category: str
    food_type: str = "veg"
    image_url: Optional[str] = None
    is_available: bool = True
    preparation_time: int = 15
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MenuItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    category: str
    food_type: str = "veg"
    image_url: Optional[str] = None
    preparation_time: int = 15

def generate_order_id():
    """Generate a short 8-character order ID like '68786a3c'"""
    return secrets.token_hex(4)  # Generates 8 hex characters

# ==================== CUSTOMER MODELS ====================
class Address(BaseModel):
    type: str = "home"  # home, work, other
    line1: str
    line2: Optional[str] = ""
    landmark: Optional[str] = ""
    city: str
    pincode: str
    is_default: bool = True

class OrderHistory(BaseModel):
    total_orders: int = 0
    total_spent: float = 0.0
    average_order_value: float = 0.0
    last_order_date: Optional[datetime] = None
    favorite_items: List[str] = []

class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    addresses: List[Address] = []

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    addresses: Optional[List[Address]] = None
    status: Optional[str] = None

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    name: str
    phone: str
    email: Optional[str] = ""
    addresses: List[Address] = []
    order_history: OrderHistory = OrderHistory()
    loyalty_points: int = 0
    status: str = "active"  # active, inactive
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== NEW DISCOUNT MODEL ====================
class Discount(BaseModel):
    type: str  # percentage, fixed
    value: float
    reason: Optional[str] = ""
    amount: float

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = Field(default_factory=generate_order_id)
    order_type: str = "dine-in" 
    customer_id: Optional[str] = None 
    customer_name: str = ""
    phone: Optional[str] = None
    address: Optional[str] = None
    table_number: Optional[str] = None
    items: List[OrderItem]
    total_amount: float
    discount: Optional[Discount] = None
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
    order_type: str = "dine-in"
    customer_id: Optional[str] = None
    customer_name: str = ""
    phone: Optional[str] = None
    address: Optional[str] = None
    table_number: Optional[str] = None
    items: List[OrderItem]
    discount: Optional[Discount] = None
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
    # ✨ NEW: Admin model for authentication
class Admin(BaseModel):
    admin_id: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    created_at: Optional[datetime] = None

# ==================== NEW CUSTOMER MODELS ====================




# ==================== HELPER FUNCTIONS ====================
def prepare_for_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
        elif isinstance(v, list):
            data[k] = [prepare_for_mongo(i) if isinstance(i, dict) else i for i in v]
    return data

def parse_from_mongo(data: Dict[str, Any]) -> Dict[str, Any]:
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



# ==================== MONGODB ====================
def start_mongodb():
    """Start MongoDB server with robust error handling"""
    global mongodb_process
    
    if mongodb_process:
        print("MongoDB process already exists")
        return True
    
    try:
        # Determine base directory
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent
        
        mongodb_bin = base_dir / "mongodb" / "bin" / "mongod.exe"
        mongodb_data = base_dir / "mongodb" / "data"
        mongodb_log = base_dir / "mongodb" / "mongodb.log"
        
        # Validate MongoDB exists
        if not mongodb_bin.exists():
            print(f"❌ MongoDB not found at: {mongodb_bin}")
            return False
        
        # Create data directory with full permissions
        try:
            mongodb_data.mkdir(parents=True, exist_ok=True)
            print(f"✅ Data directory ready: {mongodb_data}")
        except Exception as e:
            print(f"❌ Cannot create data directory: {e}")
            return False
        
        # Check if MongoDB is already running on port 27017
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 27017))
        sock.close()
        
        if result == 0:
            print("✅ MongoDB already running on port 27017")
            return True
        
        # Kill any zombie MongoDB processes
        try:
            subprocess.run(
                ['taskkill', '/F', '/IM', 'mongod.exe'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            time.sleep(2)
        except:
            pass
        
        # Start MongoDB with conservative settings
        print("Starting MongoDB...")
        
        cmd = [
            str(mongodb_bin),
            "--dbpath", str(mongodb_data),
            "--port", "27017",
            "--bind_ip", "127.0.0.1",
            "--logpath", str(mongodb_log),
            "--logappend",
            "--nojournal",  # Reduces disk I/O
            "--wiredTigerCacheSizeGB", "0.25",  # Limit memory
            "--quiet"  # Less verbose
        ]
        
        # Start MongoDB process
        mongodb_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        
        # Wait for MongoDB to be ready (up to 30 seconds)
        print("Waiting for MongoDB to start...")
        max_attempts = 30
        
        for attempt in range(1, max_attempts + 1):
            time.sleep(1)
            
            # Check if process crashed
            if mongodb_process.poll() is not None:
                print(f"❌ MongoDB process terminated unexpectedly")
                print(f"   Check log: {mongodb_log}")
                return False
            
            # Try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 27017))
            sock.close()
            
            if result == 0:
                print(f"✅ MongoDB started successfully after {attempt} seconds")
                return True
            
            if attempt % 5 == 0:
                print(f"   Still waiting... ({attempt}/{max_attempts})")
        
        # Timeout
        print("❌ MongoDB failed to start within 30 seconds")
        if mongodb_process:
            mongodb_process.kill()
            mongodb_process = None
        return False
    
    except Exception as e:
        print(f"❌ Error starting MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False



def stop_mongodb():
    global mongodb_process
    if mongodb_process:
        mongodb_process.terminate()
        mongodb_process.wait()
# ============================================================
# OFFLINE LICENSE VALIDATION FUNCTION
# ============================================================
from license_validator import OfflineLicenseValidator

def verify_license():
    """
    Verify TasteParadise license on startup (OFFLINE)
    Returns True if valid, False otherwise
    """
    validator = OfflineLicenseValidator()
    
    # Check existing license
    is_valid, license_data, message = validator.validate_existing_license()
    
    if is_valid:
        # License is valid - show status
        print("\n" + "="*70)
        print("🔒 TASTEPARADISE LICENSE VERIFICATION")
        print("="*70)
        print(f"✅ {message}")
        print(f"   License Key: {license_data.get('license_key')}")
        print(f"   Expires: {license_data.get('expiry_date', 'Never')[:10]}")
        print(f"   Machine ID: {license_data.get('machine_id')}")
        print("="*70)
        return True
    
    # No valid license - need activation
    print("\n" + "="*70)
    print("🔒 TASTEPARADISE LICENSE VERIFICATION")
    print("="*70)
    print(f"\n⚠️  {message}")
    print("\n" + "="*70)
    print("🔐 LICENSE ACTIVATION")
    print("="*70)
    
    # Show machine ID
    machine_id = validator.machine_id
    print(f"\n🔑 Your Machine ID: {machine_id}")
    print("\nℹ️ ACTIVATION STEPS:")
    print("  1. Contact support with your Machine ID")
    print("     📧 Email: gaurhariom60@gmail.com")
    print("     📱 Phone: +91 82183 55207")
    print("  2. Receive activation code from support")
    print("  3. Enter activation code below")
    print("-"*70)
    
    activation_code = input("\n🔓 Enter Activation Code: ").strip()
    
    if not activation_code:
        print("\n❌ Activation code is required!")
        return False
    
    # Validate activation code
    print("\n⏳ Validating activation code...")
    is_valid, license_data, error = validator.validate_activation_code(activation_code)
    
    if not is_valid:
        print(f"\n" + "="*70)
        print("❌ ACTIVATION FAILED!")
        print("="*70)
        print(f"   Reason: {error}")
        print("\n📞 Contact support: gaurhariom60@gmail.com")
        print("="*70)
        return False
    
    # Save license
    if validator.save_license(license_data):
        print("\n" + "="*70)
        print("✅ LICENSE ACTIVATED SUCCESSFULLY!")
        print("="*70)
        print(f"   License Key: {license_data['license_key']}")
        print(f"   Expires: {license_data['expiry_date'][:10]}")
        print(f"   Machine ID: {license_data['machine_id']}")
        print("="*70)
        return True
    else:
        print("\n⚠️ License validated but could not save to file")
        return True


# ==================== CACHE CONTROL MIDDLEWARE ====================
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        
        # Never cache HTML files
        if request.url.path.endswith('.html') or request.url.path == '/':
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Cache JS/CSS for 1 hour only
        elif request.url.path.endswith(('.js', '.css')):
            response.headers["Cache-Control"] = "public, max-age=3600"
        
        # Cache other static files for 1 week
        else:
            response.headers["Cache-Control"] = "public, max-age=604800"
        
        return response

# ==================== FASTAPI APP ====================
app = FastAPI(title="Taste Paradise API", version="1.0.0")
from routes.kot_printer import routes as kot_routes

api_router = APIRouter(prefix="/api")

# ✅ ADD THIS NEW MIDDLEWARE FOR API CACHE CONTROL
@app.middleware("http")
async def add_cache_control_headers(request, call_next):
    response = await call_next(request)
    # Never cache API responses
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# ADD MIDDLEWARE FIRST (before other middlewares)
app.add_middleware(NoCacheMiddleware)

app.include_router(payment_router)
app.include_router(kot_routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
        "http://127.0.0.1",
        "http://localhost",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# ==================== WEBSOCKET ENDPOINT ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages if needed
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    global mongo_client, db
    
    # Retry connection logic
    max_retries = 10
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            mongo_client = AsyncIOMotorClient(
                "mongodb://localhost:27017",
                serverSelectionTimeoutMS=30000,  # 30 second timeout
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                maxPoolSize=50,
                minPoolSize=5,
                retryWrites=True,
                retryReads=True,
                directConnection=True
            )
            
            # Test the connection
            await mongo_client.admin.command('ping')
            
            db = mongo_client.taste_paradise
            logger.info(f"Connected to database successfully (attempt {attempt + 1})")
            init_payment_routes(db)
            logger.info("Payment routes initialized successfully")

     # ============================================================
            # 🌐 CLOUD SYNC SERVICE INITIALIZATION
            # ============================================================
        
            try:
                from cloud_sync_service import init_cloud_sync
                from license_cloud_api import license_system
                
                # Get license key from local file
                local_license = license_system.load_local_license()
                if local_license:
                    license_key = local_license.get('key')
                    logger.info(f"Initializing cloud sync for license: {license_key[:20]}...")
                    
                    # Initialize cloud sync service
                    cloud_sync = init_cloud_sync(license_key)
                    logger.info("✅ Cloud sync service started successfully")
                else:
                    logger.warning("⚠️ No license found - cloud sync disabled")
            except Exception as e:
                logger.warning(f"⚠️ Cloud sync initialization failed: {e}")
                # Continue without cloud sync (non-critical)
            # ============================================================                    
            break
        
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {e}")
                raise

    
    # Start scheduler - check if already exists
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
        logger.info("Scheduler started - daily reset scheduled for midnight")

@app.on_event("shutdown")
async def shutdown():
    global _app_started
    try:
        if scheduler.running:
            scheduler.shutdown()
        if mongo_client:
            mongo_client.close()
        stop_mongodb()
        _app_started = False  # Reset flag on shutdown
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def daily_reset():
    try:
        logger.info("Running daily reset...")
        today = datetime.now(timezone.utc).date().isoformat()
        await db.daily_reports.delete_one({"date": today})
        logger.info(f"Daily reset completed for {today}")
    except Exception as e:
        logger.error(f"Error in daily reset: {str(e)}")

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

# ============== EXCEL IMPORT/EXPORT ENDPOINTS ==============

@api_router.get("/menu/template")
async def download_template():
    """Download Excel template for bulk menu import"""
    try:
        # Create sample data
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
            'preparationtime': [20, 30, 25, 10, 15]
        }
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        
        # Use openpyxl engine
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Menu Items', index=False)
        
        output.seek(0)
        
        # Return as response
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")
@api_router.post("/menu/import")
async def import_menu(file: UploadFile = File(...)):
    """Import menu items from Excel file"""
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Only Excel files (.xlsx, .xls) are allowed"
            )
        
        # Read Excel file
        contents = await file.read()
        logger.info(f"File size: {len(contents)} bytes")
        
        df = pd.read_excel(BytesIO(contents))
        logger.info(f"Excel read successfully. Rows: {len(df)}")
        
        # Validate required columns
        required_columns = ['name', 'category', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Process each row
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Check if item already exists
                existing_item = await db.menu_items.find_one({"name": row['name']})
                if existing_item:
                    skipped_count += 1
                    logger.info(f"Skipping duplicate: {row['name']}")
                    continue
                
                # Create menu item
                menu_item = {
                    "id": str(uuid.uuid4()),
                    "name": str(row['name']),
                    "description": str(row.get('description', '')),
                    "price": float(row['price']),
                    "category": str(row['category']),
                    "imageurl": str(row.get('imageurl', '')) if pd.notna(row.get('imageurl')) else None,
                    "isavailable": True,
                    "preparationtime": int(row.get('preparationtime', 15)),
                    "createdat": datetime.now(timezone.utc)
                }
                
                # Insert into database
                await db.menu_items.insert_one(prepare_for_mongo(menu_item))
                imported_count += 1
                logger.info(f"Imported: {row['name']}")
                
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@api_router.delete("/menu/{menu_item_id}")
async def delete_menu_item(menu_item_id: str):
    result = await db.menu_items.delete_one({"id": menu_item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"message": "Menu item deleted successfully"}

    
# ==================== ORDER ENDPOINTS ====================
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    # Calculate subtotal
    total_amount = sum(i.quantity * i.price for i in order_data.items)
    
    # Calculate GST if applicable
    gst_amount = 0.0
    final_amount = total_amount
    
    if order_data.gst_applicable:
        gst_amount = round(total_amount * 0.05, 2)  # 5% GST
        final_amount = round(total_amount + gst_amount, 2)
    
    # Calculate preparation time
    max_prep_time = 30
    for i in order_data.items:
        menu_item = await db.menu_items.find_one({"id": i.menu_item_id})
        if menu_item:
            max_prep_time = max(max_prep_time, menu_item.get('preparation_time', 15))
    
    estimated_completion = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=max_prep_time)
    
    # Create order with GST fields
    # Get current time in IST
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

    # Broadcast order creation to all connected clients
    await manager.broadcast({
        "type": "order_created",
        "order_id": order.id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return order
   


@api_router.get("/orders", response_model=List[Order])
async def get_orders():
    orders_cursor = db.orders.find().sort("_id", -1)
    orders = []
    async for order in orders_cursor:
        orders.append(Order(**parse_from_mongo(order)))
    return orders
@app.router.get("/fix-order-dates")
async def fix_order_dates():
    """Add createdat to orders that don't have it"""
    try:
        # Find all orders
        orders_cursor = db.orders.find()
        
        updated_count = 0
        async for order in orders_cursor:
            # Check if createdat exists and is not None
            if "createdat" not in order or order["createdat"] is None:
                # Set createdat to current time
                await db.orders.update_one(
                    {"_id": order["_id"]},
                    {"$set": {"createdat": datetime.now(timezone.utc).isoformat()}}
                )
                updated_count += 1
        
        return {"message": f"Updated {updated_count} orders with createdat field"}
    except Exception as e:
        logger.error(f"Error fixing order dates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@api_router.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, order_data: OrderUpdate = Body(...)):
    try:
        logger.info(f"DEBUG update_order {order_id} payload: {order_data}")
        
        order_dict = order_data.model_dump(exclude_unset=True)
        
        # Recalculate amounts if items or gst_applicable changed
        if "items" in order_dict or "gst_applicable" in order_dict:
            # Get current order
            current_order = await db.orders.find_one({"id": order_id})
            if not current_order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Use updated items or keep current
            items = order_dict.get("items", current_order.get("items", []))
            gst_applicable = order_dict.get("gst_applicable", current_order.get("gst_applicable", False))
            
            # Calculate subtotal
            total_amount = sum(item.get("quantity", 0) * item.get("price", 0) for item in items)
            
            # Calculate GST
            gst_amount = 0.0
            final_amount = total_amount
            
            if gst_applicable:
                gst_amount = round(total_amount * 0.05, 2)
                final_amount = round(total_amount + gst_amount, 2)
            
            order_dict["total_amount"] = total_amount
            order_dict["gst_amount"] = gst_amount
            order_dict["final_amount"] = final_amount
            order_dict["estimated_completion"] = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=30)
        
        logger.info(f"Calculated amounts: {order_dict}")
        order_dict["updated_at"] = datetime.now(timezone.utc)
        
        updated = await db.orders.find_one_and_update(
            {"id": order_id},
            {"$set": order_dict},
            return_document=True
        )
        
        if updated is None:
            raise HTTPException(status_code=404, detail="Order not found")
        
        logger.info(f"Order {order_id} updated successfully")
        await manager.broadcast({
            "type": "order_updated",
            "order_id": order_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
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
    logger.info(f"Payment request for order {order_id}: {payment_data}")
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
    logger.info(f"Order {order_id} payment updated successfully")
    await manager.broadcast({
        "type": "payment_updated",
        "order_id": order_id,
        "payment_status": payment_status,
        "payment_method": payment_method,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    logger.info(f"Broadcast sent for order {order_id}")  # Add logging to debug
    return {"message": "Payment processed and order marked as served", "order": parse_from_mongo(updated)}

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
    await manager.broadcast({
        "type": "kot_generated",
        "order_id": order_id,
        "kot_id": kot.id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return kot

@api_router.get("/kot", response_model=List[KOT])
async def get_kots():
    kots_cursor = db.kots.find().sort("created_at", -1)
    kots = []
    async for kot in kots_cursor:
        kots.append(KOT(**parse_from_mongo(kot)))
    return kots

# ==================== DASHBOARD ENDPOINT ====================
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
    
    kitchen_status = KitchenStatus.ACTIVE
    
    return DashboardStats(
        today_orders=orders_today,
        today_revenue=total_revenue,
        pending_orders=pending_orders,
        cooking_orders=cooking_orders,
        ready_orders=ready_orders,
        served_orders=served_orders,
        kitchen_status=kitchen_status,
        pending_payments=pending_payments,
    )
# ==================== PAYMENTS ENDPOINT ====================
@api_router.get("/payments/{date}")
async def get_payments_by_date(date: str):
    """Get all paid orders for a specific date with order_id"""
    try:
        # Parse the date
        target_date = datetime.fromisoformat(date).date()
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        logger.info(f"Fetching payments for {date}")
        
        # Query for paid orders
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
                "order_id": payment.get("order_id", "N/A"),  # ⭐ KEY FIX
                "_id": str(payment["_id"]),
                "final_amount": payment.get("finalamount") or payment.get("final_amount") or payment.get("totalamount") or payment.get("total_amount") or 0,
                "payment_method": payment.get("payment_method", "N/A"),
                "payment_status": payment.get("payment_status", "N/A"),
                "created_at": payment.get("created_at"),
                "customer_name": payment.get("customer_name", "Walk-in"),
                "table_number": payment.get("table_number"),
                "items": payment.get("items", []),  # Include order items
                "total_amount": payment.get("totalamount") or payment.get("total_amount") or 0,
                "gst_amount": payment.get("gstamount") or payment.get("gst_amount") or 0,
                "gst_applicable": payment.get("gst_applicable", False)
                
            })
        
        logger.info(f"Found {len(payments_list)} payments for {date}")
        return payments_list
        
    except Exception as e:
        logger.error(f"Error fetching payments for {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@api_router.get("/payments/pending/{date}")
async def get_pending_orders(date: str):
    """Get all pending payment orders for a specific date"""
    try:
        # Parse the date
        target_date = datetime.fromisoformat(date).date()
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        logger.info(f"Fetching pending orders for {date}")
        
        # Query for pending payment orders
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
                "total_amount": order.get("totalamount") or order.get("total_amount") or 0,
                "final_amount": order.get("finalamount") or order.get("final_amount") or order.get("totalamount") or 0,
                "payment_method": "pending",
                "payment_status": "pending",
                "created_at": order.get("created_at"),
                "customer_name": order.get("customer_name", "Walk-in"),
                "table_number": order.get("table_number"),
                "items": order.get("items", [])
            })
        
        logger.info(f"Found {len(pending_list)} pending orders for {date}")
        return pending_list
        
    except Exception as e:
        logger.error(f"Error fetching pending orders for {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TABLE ENDPOINTS ====================
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

# ==================== CUSTOMER ENDPOINTS ====================
# ================ CUSTOMER ENDPOINTS ================

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    try:
        # Check if phone already exists
        existing = await db.customers.find_one({"phone": customer.phone})
        if existing:
            raise HTTPException(status_code=400, detail="Customer with this phone number already exists")
        
        customer_dict = customer.dict()
        customer_dict["id"] = str(uuid.uuid4())
        customer_dict["customer_id"] = f"CUST-{str(uuid.uuid4())[:8]}"
        customer_dict["created_at"] = datetime.now(timezone.utc)
        customer_dict["updated_at"] = datetime.now(timezone.utc)
        customer_dict["order_history"] = {"total_orders": 0, "total_spent": 0.0, "average_order_value": 0.0, "last_order_date": None, "favorite_items": []}
        customer_dict["loyalty_points"] = 0
        customer_dict["status"] = "active"
        
        customer_dict = prepare_for_mongo(customer_dict)
        result = await db.customers.insert_one(customer_dict)
        
        created_customer = await db.customers.find_one({"_id": result.inserted_id})
        logger.info(f"Customer created: {customer.phone}")
        
        return Customer.parse_from_mongo(created_customer)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/customers/search", response_model=List[Customer])
async def search_customers(query: str):
    """Search customers by name or phone"""
    try:
        if not query or len(query) < 2:
            return []
        
        import re
        regex_pattern = re.compile(query, re.IGNORECASE)
        
        customers_cursor = db.customers.find({
            "$or": [
                {"name": {"$regex": regex_pattern}},
                {"phone": {"$regex": query}},
                {"email": {"$regex": regex_pattern}}
            ],
            "status": "active"
        }).limit(10)
        
        customers = []
        async for customer in customers_cursor:
            customers.append(Customer.parse_obj(customer))
        
        return customers
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        return []


@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get customer by ID"""
    try:
        customer = await db.customers.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer.parse_obj(customer)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/customers/{customer_id}/history")
async def get_customer_history(customer_id: str):
    """Get customer order history and spending statistics"""
    try:
        # Fetch customer info
        customer = await db.customers.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Fetch all orders for this customer
        all_orders_cursor = db.orders.find({"customer_id": customer_id}).sort("created_at", -1)
        all_orders = await all_orders_cursor.to_list(None)
        
        # Get recent orders (last 10)
        recent_orders_cursor = db.orders.find({"customer_id": customer_id}).sort("created_at", -1).limit(10)
        recent_orders_list = await recent_orders_cursor.to_list(10)
        
        # Calculate statistics
        total_orders = len(all_orders)
        total_spent = sum([order.get("final_amount", order.get("total_amount", 0)) for order in all_orders])
        average_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Format recent orders
        formatted_recent_orders = [
            {
                "order_id": order.get("order_id"),
                "created_at": order.get("created_at"),
                "final_amount": order.get("final_amount", order.get("total_amount", 0)),
                "status": order.get("status", "pending")
            }
            for order in recent_orders_list
        ]
        
        logger.info(f"Customer history fetched: {customer_id}, Orders: {total_orders}, Spent: {total_spent}")
        
        return {
            "customer": {
                "customer_id": customer.get("customer_id"),
                "name": customer.get("name"),
                "phone": customer.get("phone"),
                "email": customer.get("email")
            },
            "statistics": {
                "total_orders": total_orders,
                "total_spent": round(total_spent, 2),
                "average_order_value": round(average_order_value, 2)
            },
            "recent_orders": formatted_recent_orders
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching customer history: {str(e)}")


@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    """Update customer details"""
    try:
        update_data = {k: v for k, v in customer_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data = prepare_for_mongo(update_data)
        
        result = await db.customers.update_one(
            {"customer_id": customer_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        updated_customer = await db.customers.find_one({"customer_id": customer_id})
        return Customer.parse_obj(updated_customer)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/customers", response_model=List[Customer])
async def get_all_customers(skip: int = 0, limit: int = 50, active_only: bool = True):
    """Get all customers"""
    try:
        query = {"status": "active"} if active_only else {}
        customers_cursor = db.customers.find(query).skip(skip).limit(limit)
        customers = []
        async for customer in customers_cursor:
            customers.append(Customer.parse_obj(customer))
        return customers
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        return []



# ==================== REPORT ENDPOINTS ====================
@api_router.get("/report")
async def get_daily_report(date: str):
    try:
        target_date = datetime.fromisoformat(date).date()
        start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        logger.info(f"Generating report for date: {date}, range: {start_datetime} to {end_datetime}")
        
        orders_query = {
            "created_at": {
                "$gte": start_datetime.isoformat(),
                "$lt": end_datetime.isoformat()
            }
        }
        
        # Get ALL orders for this date
        orders_cursor = db.orders.find(orders_query)
        orders_list = []
        total_revenue = 0.0  # ✅ Calculate revenue from ALL orders
        
        async for order in orders_cursor:
            parsed_order = parse_from_mongo(order)
            orders_list.append(parsed_order)
            
            # Sum revenue from ALL orders (not just paid)
            if parsed_order.get("final_amount"):
                total_revenue += float(parsed_order.get("final_amount", 0))
        
        logger.info(f"Found {len(orders_list)} orders with total revenue: ₹{total_revenue}")
        
        # Get KOTs
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
        
        # Get bills (only PAID orders for bills section)
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
            revenue=total_revenue,  # ✅ Revenue from ALL orders
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
        
        result = await db.daily_reports.replace_one(
            {"date": date},
            report_dict,
            upsert=True
        )
        
        logger.info(f"Daily report saved for {date}. Revenue: ₹{total_revenue}, Orders: {len(orders_list)}")
        return daily_report.model_dump()
        
    except Exception as e:
        logger.error(f"Error generating daily report for {date}: {str(e)}")
        import traceback
        traceback.print_exc()
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
# ==================== PRINT INVOICE ENDPOINT ====================
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
        
        html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Invoice {invoice_no}</title>
<style>
@page{{size:A4;margin:15mm}}*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial,sans-serif;padding:20px}}.header{{text-align:center;margin-bottom:30px;border-bottom:3px solid #ea580c;padding-bottom:15px}}.header h1{{color:#ea580c;font-size:36px;margin-bottom:8px}}.header p{{font-size:13px;color:#555;margin:3px 0}}.invoice-info{{display:flex;justify-content:space-between;margin:30px 0}}.invoice-info h3{{font-size:14px;margin-bottom:10px}}.invoice-info p{{font-size:13px;margin:5px 0;color:#555}}table{{width:100%;border-collapse:collapse;margin:25px 0}}th,td{{border:1px solid #ddd;padding:12px;text-align:left}}th{{background-color:#f5f5f5;font-weight:bold}}.text-center{{text-align:center}}.text-right{{text-align:right}}.totals{{margin-top:30px;text-align:right}}.totals div{{padding:8px 0;font-size:14px}}.totals .total-line{{border-top:2px solid #ea580c;margin-top:10px;padding-top:10px;font-size:18px;font-weight:bold;color:#ea580c}}.footer{{margin-top:40px;text-align:center;font-size:12px;color:#666;border-top:1px solid #ddd;padding-top:15px}}
</style>
<script>window.onload=function(){{window.print();setTimeout(function(){{window.close()}},500)}};</script>
</head><body>
<div class="header"><h1>Taste Paradise</h1><p>Restaurant & Billing Service</p><p>123 Food Street, Flavor City, FC 12345</p><p>Phone: +91 98765 43210 | Email: info@tasteparadise.com</p></div>
<div class="invoice-info"><div><h3>Invoice #{invoice_no}</h3><p>Date: {datetime.now().strftime('%d/%m/%Y')}</p><p>Time: {datetime.now().strftime('%H:%M:%S')}</p></div><div><h3>Bill To</h3><p>{customer_name}</p><p>Table: {table_no}</p></div></div>
<table><thead><tr><th>Item</th><th class="text-center">Qty</th><th class="text-right">Rate (₹)</th><th class="text-right">Amount (₹)</th></tr></thead><tbody>
{"".join([f'<tr><td>{item.get("menuitemname", item.get("name", ""))}</td><td class="text-center">{item.get("quantity", 0)}</td><td class="text-right">₹{item.get("price", 0):.2f}</td><td class="text-right">₹{(item.get("quantity", 0) * item.get("price", 0)):.2f}</td></tr>' for item in items])}
</tbody></table>
<div class="totals"><div><strong>Subtotal:</strong> ₹{subtotal:.2f}</div><div><strong>GST (5%):</strong> ₹{gst:.2f}</div><div class="total-line">Total Amount: ₹{total:.2f}</div></div>
<div class="footer"><p><strong>Thank you for dining with us at Taste Paradise!</strong></p><p>GST No: 27AAAAA0000A1Z5 | FSSAI Lic: 12345678901234</p><p>This is a computer generated invoice.</p></div>
</body></html>"""
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error generating print invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# ==================== THERMAL PRINTER ENDPOINT ====================  ← ADD THIS
@api_router.post("/print-thermal")
async def print_thermal(invoice_data: Dict[str, Any] = Body(...)):
    """Print directly to Windows printer - FIXED VERSION"""
    try:
        import win32print
        
        # STEP 1: Check printers exist
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        if not printers:
            return {
                "status": "error",
                "message": "No printer installed",
                "action": "Install and connect a printer"
            }
        
        # STEP 2: Get default printer
        try:
            default_printer = win32print.GetDefaultPrinter()
            logger.info(f" Using printer: {default_printer}")
        except Exception as e:
            return {
                "status": "error",
                "message": "No default printer set",
                "available_printers": printers
            }
        
        # STEP 3: Check printer status
        try:
            hprinter = win32print.OpenPrinter(default_printer)
            printer_info = win32print.GetPrinter(hprinter, 2)
            status = printer_info['Status']
            
            # Check for critical errors only
            PRINTER_STATUS_OFFLINE = 0x00000080
            PRINTER_STATUS_ERROR = 0x00000002
            PRINTER_STATUS_PAPER_OUT = 0x00000010
            
            if status & PRINTER_STATUS_OFFLINE:
                win32print.ClosePrinter(hprinter)
                return {
                    "status": "error",
                    "message": "Printer is offline",
                    "action": "Turn ON printer and connect USB cable"
                }
            
            if status & PRINTER_STATUS_PAPER_OUT:
                win32print.ClosePrinter(hprinter)
                return {
                    "status": "error",
                    "message": "Printer is out of paper",
                    "action": "Load paper and try again"
                }
            
            if status & PRINTER_STATUS_ERROR:
                win32print.ClosePrinter(hprinter)
                return {
                    "status": "error",
                    "message": "Printer has an error",
                    "action": "Check printer display for error details"
                }
            
            win32print.ClosePrinter(hprinter)
            logger.info(f" Printer ready (status: {status})")
            
        except Exception as e:
            logger.error(f" Printer check failed: {e}")
            return {
                "status": "error",
                "message": "Cannot access printer",
                "details": str(e)
            }
        
        # STEP 4: Extract invoice data
        invoice_no = invoice_data.get('invoiceNo', 'N/A')
        customer = invoice_data.get('customerName', 'Walk-in')
        table = invoice_data.get('tableNo', 'N/A')
        items = invoice_data.get('items', [])
        subtotal = invoice_data.get('subtotal', 0)
        gst = invoice_data.get('gst', 0)
        total = invoice_data.get('total', 0)
        
        # STEP 5: Create receipt text
        receipt = "=" * 48 + "\n"
        receipt += "            TASTE PARADISE\n"
        receipt += "        Restaurant & Billing\n"
        receipt += "=" * 48 + "\n"
        receipt += f"Invoice: {invoice_no}\n"
        receipt += f"Date: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}\n"
        receipt += f"Customer: {customer}\n"
        receipt += f"Table: {table}\n"
        receipt += "-" * 48 + "\n"
        receipt += f"{'Item':<25}{'Qty':>5}{'Price':>8}{'Amount':>10}\n"
        receipt += "-" * 48 + "\n"
        
        for item in items:
            name = str(item.get('menuitemname', ''))[:23]
            qty = item.get('quantity', 0)
            price = item.get('price', 0)
            amount = qty * price
            receipt += f"{name:<25}{qty:>5}{price:>8.2f}{amount:>10.2f}\n"
        
        receipt += "-" * 48 + "\n"
        receipt += f"{'Subtotal:':<38}Rs.{subtotal:>8.2f}\n"
        receipt += f"{'GST (5%):':<38}Rs.{gst:>8.2f}\n"
        receipt += "=" * 48 + "\n"
        receipt += f"{'TOTAL:':<38}Rs.{total:>8.2f}\n"
        receipt += "=" * 48 + "\n\n"
        receipt += "      Thank you for dining with us!\n"
        receipt += "           Visit again soon!\n"
        receipt += "      GST No: 27AAAAA0000A1Z5\n"
        receipt += "\n\n\n"
        
        # STEP 6: Send to printer
        hprinter = win32print.OpenPrinter(default_printer)
        try:
            hjob = win32print.StartDocPrinter(hprinter, 1, (f"Receipt-{invoice_no}", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            bytes_written = win32print.WritePrinter(hprinter, receipt.encode('utf-8'))
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f" Receipt printed ({bytes_written} bytes)")
            
            return {
                "status": "success",
                "message": f"Receipt printed on {default_printer}",
                "printer": default_printer,
                "bytes_sent": bytes_written,
                "invoice": invoice_no
            }
            
        except Exception as e:
            logger.error(f" Print failed: {e}")
            return {
                "status": "error",
                "message": f"Print failed: {str(e)}"
            }
        finally:
            win32print.ClosePrinter(hprinter)
        
    except Exception as e:
        logger.error(f" Error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
        
        # STEP 4: Printer is verified ONLINE - Extract invoice data
        invoice_no = invoice_data.get('invoiceNo', 'N/A')
        customer = invoice_data.get('customerName', 'Walk-in')
        table = invoice_data.get('tableNo', 'N/A')
        items = invoice_data.get('items', [])
        subtotal = invoice_data.get('subtotal', 0)
        gst = invoice_data.get('gst', 0)
        total = invoice_data.get('total', 0)
        
        # STEP 5: Create receipt
        receipt = "=" * 48 + "\n"
        receipt += "            TASTE PARADISE\n"
        receipt += "        Restaurant & Billing\n"
        receipt += "=" * 48 + "\n"
        receipt += f"Invoice: {invoice_no}\n"
        receipt += f"Date: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}\n"
        receipt += f"Customer: {customer}\n"
        receipt += f"Table: {table}\n"
        receipt += "-" * 48 + "\n"
        receipt += f"{'Item':<25}{'Qty':>5}{'Price':>8}{'Amount':>10}\n"
        receipt += "-" * 48 + "\n"
        
        for item in items:
            name = str(item.get('menuitemname', ''))[:23]
            qty = item.get('quantity', 0)
            price = item.get('price', 0)
            amount = qty * price
            receipt += f"{name:<25}{qty:>5}{price:>8.2f}{amount:>10.2f}\n"
        
        receipt += "-" * 48 + "\n"
        receipt += f"{'Subtotal:':<38}Rs.{subtotal:>8.2f}\n"
        receipt += f"{'GST (5%):':<38}Rs.{gst:>8.2f}\n"
        receipt += "=" * 48 + "\n"
        receipt += f"{'TOTAL:':<38}Rs.{total:>8.2f}\n"
        receipt += "=" * 48 + "\n\n"
        receipt += "      Thank you for dining with us!\n"
        receipt += "           Visit again soon!\n"
        receipt += "      GST No: 27AAAAA0000A1Z5\n"
        receipt += "\n\n\n"
        
        # STEP 6: Send to printer (we already verified it's online)
        hprinter = win32print.OpenPrinter(default_printer)
        try:
            hjob = win32print.StartDocPrinter(hprinter, 1, (f"Receipt-{invoice_no}", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            bytes_written = win32print.WritePrinter(hprinter, receipt.encode('utf-8'))
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            
            logger.info(f" Receipt printed successfully ({bytes_written} bytes)")
            
            return {
                "status": "success",
                "message": f"Receipt printed successfully on {default_printer}",
                "printer": default_printer,
                "bytes_sent": bytes_written,
                "invoice": invoice_no
            }
            
        except Exception as print_error:
            logger.error(f" Print failed: {print_error}")
            return {
                "status": "error",
                "message": f"Print job failed: {str(print_error)}",
                "action": "Check printer and try again"
            }
        finally:
            win32print.ClosePrinter(hprinter)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f" Print system error: {error_msg}")
        return {
            "status": "error",
            "message": f"Print system error: {error_msg}"
        }

@api_router.get("/check-printer")
async def check_printer():
    """Check printer status and availability"""
    try:
        import win32print
        
        # Get all printers
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        
        if not printers:
            return {
                "status": "error",
                "message": "No printers detected",
                "printers": []
            }
        
        # Get default printer
        try:
            default_printer = win32print.GetDefaultPrinter()
        except:
            default_printer = None
        
        # Check default printer status
        printer_status = "Unknown"
        if default_printer:
            try:
                hprinter = win32print.OpenPrinter(default_printer)
                info = win32print.GetPrinter(hprinter, 2)
                status_code = info['Status']
                
                if status_code == 0:
                    printer_status = "Ready"
                else:
                    printer_status = "Not Ready"
                
                win32print.ClosePrinter(hprinter)
            except:
                printer_status = "Cannot access"
        
        return {
            "status": "success",
            "printers": printers,
            "default_printer": default_printer,
            "printer_status": printer_status,
            "total_printers": len(printers)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@api_router.get("/list-printers")            # ← ADD THIS TOO
async def list_printers():
    """List all Windows printers"""
    try:
        import win32print
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        return {"printers": printers}
    except Exception as e:
        return {"error": str(e), "printers": []}
# ==================== DIRECT PRINT ENDPOINT ====================
@api_router.get("/health")
async def api_health_check():
    return {"status": "ok", "message": "API is running"}
        
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}


# ================================
# ✨ NEW: AUTHENTICATION ROUTES
# ================================

@app.get("/api/auth/check-admin")
async def check_admin_exists():
    """Check if admin account exists"""
    try:
        admin = await db.admins.find_one({})
        return {"exists": admin is not None}
    except Exception as e:
        logger.error(f"Error checking admin: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/signup")
async def signup(admin: Admin):
    """Create first admin account"""
    try:
        # Check if admin already exists
        existing_admin = await db.admins.find_one({})
        if existing_admin:
            raise HTTPException(
                status_code=400, 
                detail="Admin already exists. Signup is disabled."
            )
        
        # Hash password
        hashed_password = hash_password(admin.password)
        
        # Save to database
        admin_data = {
            "admin_id": admin.admin_id,
            "password": hashed_password,
            "created_at": datetime.now()
        }
        
        result = await db.admins.insert_one(admin_data)
        logger.info(f"Admin account created: {admin.admin_id}")
        
        return {
            "message": "Admin created successfully",
            "admin_id": admin.admin_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(admin_id: str = Form(...), password: str = Form(...)):
    """Login with credentials"""
    try:
        # Find admin
        admin = await db.admins.find_one({"admin_id": admin_id})
        
        if not admin:
            raise HTTPException(
                status_code=401,
                detail="Invalid admin ID or password"
            )
        
        # Verify password
        if not verify_password(password, admin["password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid admin ID or password"
            )
        
        logger.info(f"Admin logged in: {admin_id}")
        return {
            "message": "Login successful",
            "admin_id": admin_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, details=str(e))

# Line 1352
# ==================== INCLUDE API ROUTER ====================
# ==================== INCLUDE API ROUTER ====================
app.include_router(api_router)
app.include_router(payments.router)


# ==================== STATIC FILES (BEFORE CATCH-ALL!) ====================

# Mount React build's static files FIRST (most specific)
app.mount("/static/js", StaticFiles(directory=str(APP_DIR / "frontend" / "build" / "static" / "js")), name="react_js")
app.mount("/static/css", StaticFiles(directory=str(APP_DIR / "frontend" / "build" / "static" / "css")), name="react_css")

# Mount auth static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== CATCH-ALL FOR REACT ROUTER (AFTER STATIC!) ====================
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all non-API, non-static routes"""
    # ✅ DON'T serve React for API paths!
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail=f"API route not found: {full_path}")
    
    # ✅ DON'T serve React for static files!
    if full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Static file not found")
    
    # Only serve React for actual front-end routes
    index_file = Path(APP_DIR) / "frontend" / "build" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="React build not found")



# Mount React HTML at root (ABSOLUTELY LAST!)
app.mount("/", StaticFiles(directory=str(APP_DIR / "frontend" / "build"), html=True), name="frontend")

# ================================

# ==================== SERVER ====================
def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

# ==================== MAIN ====================
def start_server():
    """Start FastAPI server in thread"""
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        log_level="error",
        access_log=False
    )
# ==================== CUSTOMER ENDPOINTS ====================
# ==================== CUSTOMER ENDPOINTS ====================

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    try:
        # Check if phone already exists
        existing = await db.customers.find_one({"phone": customer.phone})
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Customer with this phone number already exists"
            )
        
        customer_dict = customer.dict()
        customer_dict["id"] = str(uuid.uuid4())
        customer_dict["customer_id"] = f"CUST-{str(uuid.uuid4())[:8]}"
        customer_dict["created_at"] = datetime.now(timezone.utc)
        customer_dict["updated_at"] = datetime.now(timezone.utc)
        customer_dict["order_history"] = {
            "total_orders": 0,
            "total_spent": 0.0,
            "average_order_value": 0.0,
            "last_order_date": None,
            "favorite_items": []
        }
        customer_dict["loyalty_points"] = 0
        customer_dict["status"] = "active"
        
        # Convert datetime objects for MongoDB
        customer_dict = prepare_for_mongo(customer_dict)
        
        # Insert into database
        result = await db.customers.insert_one(customer_dict)
        
        # Fetch the created customer
        created_customer = await db.customers.find_one({"_id": result.inserted_id})
        
        # Parse and return
        return Customer(**parse_from_mongo(created_customer))
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/customers/search", response_model=List[Customer])
async def search_customers(query: str):
    """Search customers by name or phone"""
    try:
        if not query or len(query) < 2:
            return []
        
        import re
        regex_pattern = re.compile(query, re.IGNORECASE)
        
        customers_cursor = db.customers.find({
            "$or": [
                {"name": {"$regex": regex_pattern}},
                {"phone": {"$regex": query}},
                {"email": {"$regex": regex_pattern}}
            ],
            "status": "active"
        }).limit(10)
        
        customers = []
        async for customer in customers_cursor:
            customers.append(Customer(**parse_from_mongo(customer)))
        
        return customers
    
    except Exception as e:
        print(f"Error searching customers: {e}")
        return []


@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get customer by ID"""
    try:
        customer = await db.customers.find_one({"customer_id": customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer(**parse_from_mongo(customer))
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    



@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    """Update customer details"""
    try:
        update_data = {k: v for k, v in customer_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data = prepare_for_mongo(update_data)
        
        result = await db.customers.update_one(
            {"customer_id": customer_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        updated_customer = await db.customers.find_one({"customer_id": customer_id})
        return Customer(**parse_from_mongo(updated_customer))
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/customers", response_model=List[Customer])
async def get_all_customers(skip: int = 0, limit: int = 50, active_only: bool = True):
    """Get all customers"""
    try:
        query = {"status": "active"} if active_only else {}
        customers_cursor = db.customers.find(query).skip(skip).limit(limit)
        customers = []
        async for customer in customers_cursor:
            customers.append(Customer(**parse_from_mongo(customer)))
        return customers
    
    except Exception as e:
        print(f"Error getting customers: {e}")
        return []


# ==================== UPDATE ORDER CREATION ====================
# Modify your existing create_order endpoint to handle new fields:
# Find your @api_router.post("/orders") endpoint and update it to:

@api_router.post("/orders-enhanced", response_model=Order)
async def create_order_enhanced(order_data: OrderCreate):
    """Enhanced order creation with customer and discount support"""
    # Calculate subtotal
    total_amount = sum(i.quantity * i.price for i in order_data.items)
    
    # Calculate discount
    discount_amount = 0.0
    discount_obj = None
    
    if hasattr(order_data, 'discount') and order_data.discount:
        if order_data.discount.type == "percentage":
            discount_amount = (total_amount * order_data.discount.value) / 100
        elif order_data.discount.type == "fixed":
            discount_amount = order_data.discount.value
        
        discount_amount = min(discount_amount, total_amount)
        
        discount_obj = {
            "type": order_data.discount.type,
            "value": order_data.discount.value,
            "reason": order_data.discount.reason or "",
            "amount": discount_amount
        }
    
    # Calculate GST on (subtotal - discount)
    taxable_amount = total_amount - discount_amount
    gst_amount = 0.0
    final_amount = taxable_amount
    
    if order_data.gst_applicable:
        gst_amount = round(taxable_amount * 0.05, 2)
        final_amount = round(taxable_amount + gst_amount, 2)
    
    # Create order
    now_ist = datetime.now(IST)
    order_dict = order_data.dict()
    order_dict["id"] = str(uuid.uuid4())
    order_dict["order_id"] = generate_order_id()
    order_dict["total_amount"] = round(total_amount, 2)
    order_dict["discount"] = discount_obj
    order_dict["gst_amount"] = gst_amount
    order_dict["final_amount"] = final_amount
    order_dict["status"] = OrderStatus.PENDING.value
    order_dict["payment_status"] = PaymentStatus.PENDING.value
    order_dict["created_at"] = now_ist
    order_dict["updated_at"] = now_ist
    order_dict["estimated_completion"] = now_ist + timedelta(minutes=30)
    order_dict["kot_generated"] = False
    
    order_dict = prepare_for_mongo(order_dict)
    await db.orders.insert_one(order_dict)
    
    # Update customer order history if customer_id provided
    if order_dict.get("customer_id"):
        await update_customer_order_history(order_dict["customer_id"], final_amount)
    
    # Update table status if table_number provided
    if order_dict.get("table_number"):
        await db.tables.update_one(
            {"table_number": order_dict["table_number"]},
            {"$set": {"status": "occupied", "current_order_id": order_dict["id"]}}
        )
    
    return Order(**parse_from_mongo(order_dict))

async def update_customer_order_history(customer_id: str, order_total: float):
    """Update customer's order history"""
    customer = await db.customers.find_one({"customer_id": customer_id})
    if customer:
        order_history = customer.get("order_history", {})
        total_orders = order_history.get("total_orders", 0) + 1
        total_spent = order_history.get("total_spent", 0.0) + order_total
        avg_order_value = total_spent / total_orders
        
        await db.customers.update_one(
            {"customer_id": customer_id},
            {
                "$set": {
                    "order_history.total_orders": total_orders,
                    "order_history.total_spent": round(total_spent, 2),
                    "order_history.average_order_value": round(avg_order_value, 2),
                    "order_history.last_order_date": datetime.now(timezone.utc),
                    "loyalty_points": customer.get("loyalty_points", 0) + int(order_total / 10),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )


# ==================== LOGIN/SIGNUP WINDOW (FILE-BASED USER CHECK) ====================
if __name__ == "__main__":
    import argparse
    import threading
    import time
    import webbrowser
    import socket

    print("\n" + "="*70)
    print("                    TASTE PARADISE")
    print("               Restaurant Management System")
    print("="*70)
    
    # ============================================================
    # OFFLINE LICENSE CHECK
    # ============================================================
    if not verify_license():
        print("\n" + "="*70)
        print("❌ LICENSE VALIDATION FAILED")
        print("="*70)
        print("\n⚠️  Cannot start TasteParadise without a valid license.")
        print("\n" + "-"*70)
        print("📞 SUPPORT")
        print("-"*70)
        print("  📧 Email: gaurhariom60@gmail.com")
        print("  📱 Phone: +91 82183 55207")
        print("-"*70)
        print("🛒 PURCHASE A LICENSE")
        print("-"*70)
        print("  • Basic: ₹15,000/year")
        print("  • Pro: ₹30,000/year")
        print("  • Enterprise: ₹75,000 (10 years)")
        print("="*70)
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # License verified - continue startup
    print("\n✅ License verified! Initializing TasteParadise...")
    print("="*70)
    
    # ============================================================
    # START MONGODB
    # ============================================================
    if not start_mongodb():
        print("\n❌ Failed to start MongoDB!")
        print("TasteParadise cannot run without database.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("✅ MongoDB started successfully")
    
    # ============================================================
    # CONNECT TO MONGODB
    # ============================================================
    try:
        print("⏳ Connecting to MongoDB...")
        mongo_client = AsyncIOMotorClient("mongodb://127.0.0.1:27017/")
        db = mongo_client["taste_paradise"]
        
        # Test connection
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mongo_client.admin.command('ping'))
        
        print("✅ Connected to MongoDB")
        
        # Initialize payment routes with database
        init_payment_routes(db)
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        stop_mongodb()
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # ============================================================
    # START FASTAPI SERVER
    # ============================================================
    def start_server():
        """Start FastAPI server in background thread"""
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8002,
            log_level="error"
        )
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print("✅ FastAPI server starting...")
    time.sleep(2)  # Wait for server to start
    
    # ============================================================
    # CHECK IF SERVER IS RUNNING
    # ============================================================
    def check_server():
        """Check if server is responding"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 8002))
            sock.close()
            return result == 0
        except:
            return False
    
    max_retries = 10
    for i in range(max_retries):
        if check_server():
            print("✅ Server is ready!")
            break
        print(f"⏳ Waiting for server... ({i+1}/{max_retries})")
        time.sleep(1)
    else:
        print("❌ Server failed to start!")
        stop_mongodb()
        sys.exit(1)
    
    # ============================================================
    # OPEN IN BROWSER (DEFAULT MODE)
    # ============================================================
    try:
        url = "http://127.0.0.1:8002"
        
        # Open in default browser
        print(f"\n🌐 Opening TasteParadise in browser...")
        webbrowser.open(url)
        
        print("\n" + "="*70)
        print("✅ TASTEPARADISE IS RUNNING")
        print("="*70)
        print(f"   🌐 URL: {url}")
        print(f"   📋 Access TasteParadise in your web browser")
        print(f"   🔄 Refresh the page if it doesn't load")
        print(f"\n   ⚠️  Press Ctrl+C to stop the server")
        print("="*70)
        
        # Keep server alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("⚠️ SHUTTING DOWN TASTEPARADISE")
            print("="*70)
            print("⏳ Stopping MongoDB...")
            stop_mongodb()
            print("✅ MongoDB stopped")
            print("✅ Server stopped")
            print("\n👋 Thank you for using TasteParadise!")
            print("="*70)
            sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n⏳ Cleaning up...")
        stop_mongodb()
        input("\nPress Enter to exit...")
        sys.exit(1)







