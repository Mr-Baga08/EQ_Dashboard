# backend/app/schemas/trade.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TradeTypeEnum(str, Enum):
    MTF = "MTF"
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"

class ExecutionTypeEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    PENDING = "PENDING"

class TradeBase(BaseModel):
    trade_id: str = Field(..., min_length=1, max_length=100)
    client_id: int
    token_id: int
    trade_type: TradeTypeEnum
    execution_type: ExecutionTypeEnum
    quantity: int = Field(..., gt=0)
    avg_price: float = Field(..., gt=0)

class TradeCreate(TradeBase):
    pass

class TradeResponse(TradeBase):
    id: int
    status: TradeStatusEnum
    current_price: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    margin_required: float
    margin_blocked: float
    motilal_order_id: Optional[str]
    entry_time: datetime
    exit_time: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Nested objects
    client: Optional[dict] = None
    token: Optional[dict] = None
    
    class Config:
        from_attributes = True