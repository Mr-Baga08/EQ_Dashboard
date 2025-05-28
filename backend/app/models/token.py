# backend/app/models/token.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
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
    
    # Extended token information
    company_name = Column(String(255))
    sector = Column(String(100))
    industry = Column(String(100))
    
    # Price data
    ltp = Column(Float, default=0.0)
    open_price = Column(Float, default=0.0)
    high_price = Column(Float, default=0.0)
    low_price = Column(Float, default=0.0)
    close_price = Column(Float, default=0.0)
    prev_close = Column(Float, default=0.0)
    
    # Volume and market data
    volume = Column(Integer, default=0)
    value = Column(Float, default=0.0)
    average_price = Column(Float, default=0.0)
    
    # Trading specifications
    lot_size = Column(Integer, default=1)
    tick_size = Column(Float, default=0.05)
    upper_circuit = Column(Float, default=0.0)
    lower_circuit = Column(Float, default=0.0)
    
    # Options specific (if applicable)
    strike_price = Column(Float, nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    option_type = Column(String(2), nullable=True)  # CE, PE
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_tradeable = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    
    # Websocket registration
    websocket_registered = Column(Boolean, default=False)
    last_price_update = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trades = relationship("Trade", back_populates="token")
    orders = relationship("Order", back_populates="token")
