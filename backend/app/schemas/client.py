# backend/app/schemas/client.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    motilal_client_id: str = Field(..., min_length=1, max_length=100)
    api_key: Optional[str] = None
    encrypted_password: Optional[str] = None
    two_fa: Optional[str] = None
    totp: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    available_funds: Optional[float] = None
    is_active: Optional[bool] = None

class ClientResponse(ClientBase):
    id: int
    available_funds: float
    total_pnl: float
    margin_used: float
    margin_available: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True