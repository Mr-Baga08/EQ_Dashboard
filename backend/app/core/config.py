# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Multi-Client Trading Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "trading_user"
    POSTGRES_PASSWORD: str = "trading_password"
    POSTGRES_DB: str = "trading_platform"
    POSTGRES_PORT: int = 5432
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # Motilal API
    MOTILAL_BASE_URL: str = "https://openapi.motilaloswaluat.com"
    MOTILAL_API_KEY: str = "your-motilal-api-key"
    MOTILAL_CLIENT_CODE: str = "your-client-code"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Environment
    DEBUG: bool = True
    TESTING: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    class Config:
        env_file = ".env"

settings = Settings()

# backend/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_database() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

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
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trades = relationship("Trade", back_populates="client", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")

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

# backend/app/models/trade.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
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
    
    # Motilal API Response
    motilal_order_id = Column(String(100))
    motilal_response = Column(String(1000))
    
    # Timestamps
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="trades")
    token = relationship("Token", back_populates="trades")

# backend/app/models/order.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"

class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIAL = "PARTIAL"

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
    
    # Price and Quantity
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)  # Null for market orders
    executed_quantity = Column(Integer, default=0)
    executed_price = Column(Float, default=0.0)
    
    # Motilal API Details
    motilal_order_id = Column(String(100))
    motilal_response = Column(String(1000))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="orders")
    token = relationship("Token", back_populates="orders")