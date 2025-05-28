# backend/app/schemas/token.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TokenBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=50)
    token_id: int
    exchange: str = Field(..., min_length=1, max_length=20)
    instrument_type: Optional[str] = None

class TokenCreate(TokenBase):
    lot_size: int = 1
    tick_size: float = 0.05

class TokenResponse(TokenBase):
    id: int
    ltp: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    lot_size: int
    tick_size: float
    is_active: bool
    is_tradeable: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True