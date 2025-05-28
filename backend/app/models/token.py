# backend/app/models/token.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    token_id = Column(Integer, unique=True, nullable=False)
    exchange = Column(String(20), nullable=False)  # NSE, BSE, NSEFO, etc.
    instrument_type = Column(String(20))  # EQ, FUT, OPT, etc.
    
    # Price data
    ltp = Column(Float, default=0.0)
    open_price = Column(Float, default=0.0)
    high_price = Column(Float, default=0.0)
    low_price = Column(Float, default=0.0)
    close_price = Column(Float, default=0.0)
    
    # Market data
    volume = Column(Integer, default=0)
    lot_size = Column(Integer, default=1)
    tick_size = Column(Float, default=0.05)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_tradeable = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trades = relationship("Trade", back_populates="token")
    orders = relationship("Order", back_populates="token")
