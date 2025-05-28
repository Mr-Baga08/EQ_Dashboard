# backend/app/models/trade.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class TradeType(enum.Enum):
    MTF = "MTF"
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"

class TradeStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"

class ExecutionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    
    # Trade Details
    trade_type = Column(Enum(TradeType), nullable=False)
    execution_type = Column(Enum(ExecutionType), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.ACTIVE)
    
    # Price and Quantity
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, default=0.0)
    
    # P&L Calculations
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    
    # Margin Details
    margin_required = Column(Float, default=0.0)
    margin_blocked = Column(Float, default=0.0)
    
    # Order execution details
    executed_quantity = Column(Integer, default=0)
    pending_quantity = Column(Integer, default=0)
    
    # Motilal API Response
    motilal_order_id = Column(String(100))
    motilal_response = Column(Text)
    
    # Risk management
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)
    
    # Timestamps
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="trades")
    token = relationship("Token", back_populates="trades")