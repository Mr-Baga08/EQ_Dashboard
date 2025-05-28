# backend/app/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"

class OrderDuration(enum.Enum):
    DAY = "DAY"
    IOC = "IOC"
    GTC = "GTC"
    GTD = "GTD"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    
    # Order Details
    order_type = Column(Enum(OrderType), nullable=False)
    execution_type = Column(String(10), nullable=False)  # BUY/SELL
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    order_duration = Column(Enum(OrderDuration), default=OrderDuration.DAY)
    
    # Price and Quantity
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)  # Null for market orders
    trigger_price = Column(Float, nullable=True)  # For stop loss orders
    disclosed_quantity = Column(Integer, default=0)
    
    # Execution details
    executed_quantity = Column(Integer, default=0)
    executed_price = Column(Float, default=0.0)
    remaining_quantity = Column(Integer, default=0)
    
    # Product and trading details
    product_type = Column(String(20), default="NORMAL")
    amo_order = Column(Boolean, default=False)
    
    # Motilal API Details
    motilal_order_id = Column(String(100))
    motilal_response = Column(Text)
    
    # Order metadata
    tag = Column(String(50), nullable=True)
    algo_id = Column(String(20), nullable=True)
    participant_code = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="orders")
    token = relationship("Token", back_populates="orders")