# routes/payment_routes.py

from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from datetime import datetime, timezone
import logging
from bson import ObjectId

from models.soundbox_models import (
    SoundboxConfigModel,
    SoundboxConfigCreate,
    SoundboxConfigUpdate,
    UnmatchedPaymentModel,
    PaymentMatchingSettings,
    SoundboxWebhookPayload
)

from services.payment_matcher import PaymentMatcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["payments"])

# This will be injected from main.py
db = None

def init_payment_routes(database):
    """Initialize routes with database connection"""
    global db
    db = database

# ============================================================================
# ✅ MONGODB TO DICT CONVERTER - CENTRALIZED SOLUTION
# ============================================================================
def mongo_to_dict(doc):
    """
    Convert MongoDB document to JSON-serializable dict
    Handles: ObjectId, datetime, nested dicts, lists
    This is the SINGLE source of truth for serialization
    """
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [mongo_to_dict(item) for item in doc]
    
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value) if isinstance(value, ObjectId) else value
            else:
                result[key] = mongo_to_dict(value)
        return result
    
    if isinstance(doc, ObjectId):
        return str(doc)
    
    if isinstance(doc, datetime):
        return doc.isoformat()
    
    return doc

# ============================================================================
# SOUNDBOX CONFIGURATION ENDPOINTS
# ============================================================================

@router.post("/soundbox/config", response_model=SoundboxConfigModel)
async def create_soundbox_config(config_data: SoundboxConfigCreate):
    """Create or update soundbox configuration"""
    try:
        # Check if config already exists
        existing_config = await db.soundbox_configs.find_one()
        
        if existing_config:
            # Update existing config
            config_dict = config_data.model_dump()
            config_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            await db.soundbox_configs.update_one(
                {"_id": existing_config["_id"]},
                {"$set": config_dict}
            )
            
            updated_config = await db.soundbox_configs.find_one({"_id": existing_config["_id"]})
            # ✅ Use mongo_to_dict for conversion
            updated_config = mongo_to_dict(updated_config)
            logger.info(f"✅ Soundbox config updated: {config_data.provider}")
            return SoundboxConfigModel(**updated_config)
        
        # Create new config
        config = SoundboxConfigModel(**config_data.model_dump())
        config_dict = config.model_dump()
        
        # Convert datetime to string
        for key, value in config_dict.items():
            if isinstance(value, datetime):
                config_dict[key] = value.isoformat()
        
        result = await db.soundbox_configs.insert_one(config_dict)
        config_dict["id"] = str(result.inserted_id)
        logger.info(f"✅ Soundbox config created: {config.provider}")
        return config
        
    except Exception as e:
        logger.error(f"Error creating soundbox config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/soundbox/config", response_model=SoundboxConfigModel)
async def get_soundbox_config():
    """Get current soundbox configuration"""
    try:
        config = await db.soundbox_configs.find_one()
        
        if not config:
            raise HTTPException(status_code=404, detail="Soundbox config not found")
        
        # ✅ Use mongo_to_dict for conversion
        config = mongo_to_dict(config)
        return SoundboxConfigModel(**config)
        
    except Exception as e:
        logger.error(f"Error fetching soundbox config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/soundbox/config", response_model=SoundboxConfigModel)
async def update_soundbox_config(config_data: SoundboxConfigUpdate):
    """Update soundbox configuration"""
    try:
        existing_config = await db.soundbox_configs.find_one()
        
        if not existing_config:
            raise HTTPException(status_code=404, detail="Soundbox config not found")
        
        # Update only provided fields
        update_data = config_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.soundbox_configs.update_one(
            {"_id": existing_config["_id"]},
            {"$set": update_data}
        )
        
        updated = await db.soundbox_configs.find_one({"_id": existing_config["_id"]})
        # ✅ Use mongo_to_dict for conversion
        updated = mongo_to_dict(updated)
        return SoundboxConfigModel(**updated)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating soundbox config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/soundbox/config")
async def disconnect_soundbox():
    """Disconnect/deactivate soundbox configuration"""
    try:
        config = await db.soundbox_configs.find_one()
        
        if not config:
            raise HTTPException(status_code=404, detail="Soundbox config not found")
        
        # Set is_active to False
        await db.soundbox_configs.update_one(
            {"_id": config["_id"]},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info("✅ Soundbox disconnected successfully")
        
        # Return the updated config with is_active = False
        updated_config = await db.soundbox_configs.find_one({"_id": config["_id"]})
        # ✅ Use mongo_to_dict for conversion
        updated_config = mongo_to_dict(updated_config)
        
        return {
            "status": "success",
            "message": "Soundbox disconnected successfully",
            "connected": False,
            "is_active": False,
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting soundbox: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/soundbox/test-connection")
async def test_soundbox_connection():
    """Test soundbox connection"""
    try:
        config = await db.soundbox_configs.find_one()
        
        if not config:
            return {
                "status": "error",
                "message": "Soundbox not configured",
                "connected": False
            }
        
        # Update last_ping
        await db.soundbox_configs.update_one(
            {"_id": config["_id"]},
            {"$set": {"last_ping": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "status": "success",
            "message": "Soundbox connection test successful",
            "connected": True,
            "provider": config.get("provider", "unknown"),
            "merchant_upi_id": config.get("merchant_upi_id", "")
        }
        
    except Exception as e:
        logger.error(f"Error testing soundbox connection: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "connected": False
        }

# ============================================================================
# PAYMENT WEBHOOK ENDPOINTS
# ============================================================================

@router.post("/webhook/soundbox")
async def soundbox_webhook_simple(payload: dict):
    """
    Receive payment notifications from Paytm/PhonePe Soundbox
    Simplified version that works with basic payload structure
    """
    try:
        logger.info(f"📥 Payment webhook received: {payload}")
        
        # Extract payment details
        transaction_id = payload.get("transaction_id")
        amount = float(payload.get("amount", 0))
        upi_id = payload.get("upi_id", payload.get("payer_vpa", ""))
        payment_method = payload.get("payment_method", "upi")
        status = payload.get("status", "success")
        
        if not transaction_id or amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid payment data")
        
        # Check if payment already exists
        existing = await db.payments.find_one({"transaction_id": transaction_id})
        if existing:
            logger.warning(f"⚠️ Duplicate payment: {transaction_id}")
            return {"status": "duplicate", "message": "Payment already processed"}
        
        # Create payment record
        payment_record = {
            "transaction_id": transaction_id,
            "amount": amount,
            "upi_id": upi_id,
            "payment_method": payment_method,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "matched": False,
            "order_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save to database
        result = await db.payments.insert_one(payment_record)
        logger.info(f"💾 Payment saved: {transaction_id}")
        
        # Try to match with pending orders
        matched_order = await auto_match_payment(amount, transaction_id)
        
        if matched_order:
            logger.info(f"✅ Payment matched to order: {matched_order['order_id']}")
            return {
                "status": "success",
                "message": "Payment received and matched",
                "order_id": matched_order["order_id"],
                "matched": True
            }
        else:
            logger.warning(f"⚠️ No matching order found for ₹{amount}")
            return {
                "status": "success",
                "message": "Payment received, no matching order",
                "matched": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def auto_match_payment(amount: float, transaction_id: str):
    """Auto-match payment to pending order by amount"""
    try:
        logger.info(f"🔍 Attempting to match payment: ₹{amount} (TXN: {transaction_id})")
        
        # Find pending orders with matching amount (±2 tolerance)
        pending_orders = await db.orders.find({
            "payment_status": "pending",
            "final_amount": {"$gte": amount - 2, "$lte": amount + 2}
        }).sort("created_at", 1).to_list(length=10)
        
        if not pending_orders:
            logger.warning(f"⚠️ No matching pending orders found for ₹{amount}")
            return None
        
        # Match to oldest pending order
        order = pending_orders[0]
        order_id = order.get("order_id")
        logger.info(f"🎯 Matching to order: {order_id}")
        
        # Update order with correct field name
        update_result = await db.orders.update_one(
            {"order_id": order_id},
            {"$set": {
                "payment_status": "paid",
                "payment_method": "online",
                "transaction_id": transaction_id,
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "status": "served",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if update_result.modified_count == 0:
            logger.error(f"❌ Failed to update order {order_id}")
            return None
        
        # Update payment record
        await db.payments.update_one(
            {"transaction_id": transaction_id},
            {"$set": {
                "matched": True,
                "order_id": order_id,
                "matched_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"✅ Order {order_id} marked as PAID via ONLINE payment!")
        return order
        
    except Exception as e:
        logger.error(f"❌ Error matching payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@router.post("/webhook/soundbox/test")
async def test_webhook():
    """Test endpoint to simulate payment notification"""
    test_payload = {
        "transaction_id": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "amount": 250.0,
        "upi_id": "customer@paytm",
        "payment_method": "upi",
        "status": "success"
    }
    result = await soundbox_webhook_simple(test_payload)
    return result

# ============================================================================
# PAYMENT HISTORY ENDPOINTS
# ============================================================================

@router.get("/payments/history")
async def get_payment_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get payment history with filters"""
    try:
        query = {}
        
        # Add filters
        if status:
            query["status"] = status
        
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        
        # Fetch payments
        payments = await db.payments.find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
        
        # ✅ Convert all payments using mongo_to_dict
        payments = [mongo_to_dict(payment) for payment in payments]
        
        return {
            "payments": payments,
            "count": len(payments)
        }
        
    except Exception as e:
        logger.error(f"Error fetching payment history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payments/unmatched")
async def get_unmatched_payments():
    """Get all unmatched payments"""
    try:
        unmatched = await db.payments.find({"matched": False}).sort("timestamp", -1).to_list(length=100)
        
        # ✅ Convert all payments using mongo_to_dict
        unmatched = [mongo_to_dict(payment) for payment in unmatched]
        
        return {
            "unmatched_payments": unmatched,
            "count": len(unmatched)
        }
        
    except Exception as e:
        logger.error(f"Error fetching unmatched payments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payments/{payment_id}/match/{order_id}")
async def manual_match_payment(payment_id: str, order_id: str):
    """Manually match a payment to an order"""
    try:
        # Find payment
        payment = await db.payments.find_one({"transaction_id": payment_id})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Find order
        order = await db.orders.find_one({"order_id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order
        await db.orders.update_one(
            {"order_id": order_id},
            {"$set": {
                "payment_status": "paid",
                "transaction_id": payment_id,
                "paid_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update payment
        await db.payments.update_one(
            {"transaction_id": payment_id},
            {"$set": {
                "matched": True,
                "order_id": order_id,
                "matched_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"✅ Manually matched payment {payment_id} to order {order_id}")
        
        return {
            "status": "success",
            "message": "Payment matched successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ✅ PAYMENT STATISTICS - FIXED WITH mongo_to_dict()
# ============================================================================

@router.get("/payments/stats")
async def get_payment_stats(date: Optional[str] = None):
    """Get payment statistics - includes ALL paid orders"""
    try:
        # Use provided date or today
        if date:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        else:
            target_date = datetime.now(timezone.utc)
        
        # Get start and end of day
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        logger.info(f"📊 Fetching payment stats for: {start_of_day.date()}")
        
        # =====================================================================
        # GET ALL PAID ORDERS (This includes cash, online, and unknown)
        # =====================================================================
        all_paid_orders = await db.orders.find({
            "payment_status": "paid",
            "created_at": {
                "$gte": start_of_day.isoformat(),
                "$lte": end_of_day.isoformat()
            }
        }).to_list(length=1000)
        
        # ✅ CRITICAL FIX: Convert ALL orders using mongo_to_dict FIRST
        all_paid_orders = [mongo_to_dict(order) for order in all_paid_orders]
        
        # Separate by payment method (now safe to use)
        online_orders = [o for o in all_paid_orders if o.get("payment_method") == "online"]
        cash_orders = [o for o in all_paid_orders if o.get("payment_method") == "cash"]
        unknown_orders = [o for o in all_paid_orders if not o.get("payment_method")]
        
        # Calculate totals
        total_online = sum(float(o.get("final_amount", o.get("total", 0))) for o in online_orders)
        total_cash = sum(float(o.get("final_amount", o.get("total", 0))) for o in cash_orders)
        total_unknown = sum(float(o.get("final_amount", o.get("total", 0))) for o in unknown_orders)
        
        # Total amount
        total_amount = total_online + total_cash + total_unknown
        
        logger.info(f"💰 Online: ₹{total_online}, Cash: ₹{total_cash}, Unknown: ₹{total_unknown}")
        
        # =====================================================================
        # GET PENDING ORDERS (for matching dropdown)
        # =====================================================================
        pending_orders = await db.orders.find({
            "payment_status": {"$ne": "paid"},
            "created_at": {
                "$gte": start_of_day.isoformat(),
                "$lte": end_of_day.isoformat()
            }
        }).to_list(length=100)
        
        # ✅ Convert pending orders
        pending_orders = [mongo_to_dict(order) for order in pending_orders]
        
        # =====================================================================
        # GET WEBHOOK PAYMENTS (from soundbox/test webhook)
        # =====================================================================
        today_payments = await db.payments.find({
            "timestamp": {
                "$gte": start_of_day.isoformat(),
                "$lte": end_of_day.isoformat()
            }
        }).to_list(length=1000)
        
        # ✅ Convert webhook payments
        today_payments = [mongo_to_dict(payment) for payment in today_payments]
        
        # Count matched/unmatched webhook payments
        matched_count = sum(1 for p in today_payments if p.get("matched", False))
        unmatched_count = len(today_payments) - matched_count
        
        # Return plain dict (all ObjectIds converted to strings)
        return {
            "total_payments_today": len(all_paid_orders),  # Total ORDERS paid
            "total_amount": float(total_amount),
            "matched_payments": matched_count,  # Webhook payments matched
            "unmatched_payments": unmatched_count,  # Webhook payments unmatched
            "pending_orders": pending_orders,
            "today_online": float(total_online),
            "today_cash": float(total_cash),
            "today_unknown": float(total_unknown),
            "online_orders_count": len(online_orders),
            "cash_orders_count": len(cash_orders),
            "unknown_orders_count": len(unknown_orders),
            "date": start_of_day.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching payment stats: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
