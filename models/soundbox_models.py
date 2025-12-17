"""Soundbox and Payment models for Taste Paradise"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SoundboxConfigModel(BaseModel):
    """Configuration model for Soundbox"""
    id: Optional[str] = None
    key_id: Optional[str] = None
    juspay_account_id: Optional[str] = None
    sandbox_mode: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SoundboxConfigCreate(BaseModel):
    """Model for creating Soundbox configuration"""
    key_id: str
    juspay_account_id: str
    sandbox_mode: bool = False


class SoundboxConfigUpdate(BaseModel):
    """Model for updating Soundbox configuration"""
    key_id: Optional[str] = None
    juspay_account_id: Optional[str] = None
    sandbox_mode: Optional[bool] = None


class UnmatchedPaymentModel(BaseModel):
    """Model for unmatched payments"""
    id: Optional[str] = None
    transaction_id: str
    amount: float
    currency: str = "INR"
    customer_id: Optional[str] = None
    payment_method: Optional[str] = None
    status: str = "unmatched"
    created_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentMatchingSettings(BaseModel):
    """Settings for payment matching"""
    auto_match: bool = True
    match_tolerance: float = 0.01  # 1 paise tolerance
    retry_failed_matches: bool = True
    webhook_enabled: bool = True


class SoundboxWebhookPayload(BaseModel):
    """Model for Soundbox webhook payloads"""
    event: str
    transaction_id: str
    amount: float
    status: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
