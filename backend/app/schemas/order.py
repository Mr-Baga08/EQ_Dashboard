# backend/app/schemas/order.py
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class OrderTypeEnum(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class ExecutionTypeEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    EXIT = "EXIT"

class TradeTypeEnum(str, Enum):
    MTF = "MTF"
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"

class OrderCreate(BaseModel):
    client_id: int
    token_id: int
    execution_type: ExecutionTypeEnum
    order_type: OrderTypeEnum
    trade_type: TradeTypeEnum
    quantity: int = Field(..., gt=0)
    price: Optional[float] = None
    tag: Optional[str] = None

class ClientOrderQuantity(BaseModel):
    client_id: int
    quantity: int = Field(..., ge=0)  # 0 means skip this client

class BatchOrderCreate(BaseModel):
    token_id: int
    execution_type: ExecutionTypeEnum
    order_type: OrderTypeEnum
    trade_type: TradeTypeEnum
    price: Optional[float] = None
    client_orders: List[ClientOrderQuantity]

class OrderResponse(BaseModel):
    status: str
    message: str
    order_id: Optional[str] = None
    client_id: Optional[int] = None
    
    class Config:
        from_attributes = True