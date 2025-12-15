from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)

# Global state
db = None
nlp_service = None
sessions = {}

class ChatMessage(BaseModel):
    message: str
    session_id: str
    table_number: Optional[str] = None
    customer_name: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    items: Optional[List[Dict]] = None
    order_id: Optional[str] = None
    order_summary: Optional[Dict] = None

async def process_chat_message(chat: ChatMessage):
    """Process a chat message"""
    try:
        logger.info(f"Got message: {chat.message}")
        
        # Simple response for now
        return ChatResponse(
            response=f"Received your message: {chat.message}",
            intent="test"
        )
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
