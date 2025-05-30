# backend/app/models/client.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    motilal_client_id = Column(String(100), unique=True, nullable=False)
    available_funds = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    margin_used = Column(Float, default=0.0)
    margin_available = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    
    # Motilal API specific fields
    api_key = Column(String(255))
    encrypted_password = Column(Text)
    two_fa = Column(String(50))
    totp = Column(String(10), nullable=True)
    
    # WebSocket and connection settings
    websocket_enabled = Column(Boolean, default=True)
    auto_login = Column(Boolean, default=True)
    max_orders_per_day = Column(Integer, default=1000)
    
    # Risk management
    max_position_size = Column(Float, default=1000000.0)  # Max position per stock
    max_daily_loss = Column(Float, default=50000.0)  # Max daily loss limit
    daily_loss_current = Column(Float, default=0.0)  # Current daily loss
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="client", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")
