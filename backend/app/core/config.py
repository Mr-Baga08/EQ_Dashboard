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
    
    # Motilal API Configuration
    MOTILAL_BASE_URL: str = "https://openapi.motilaloswaluat.com"
    MOTILAL_API_KEY: str = "your-motilal-api-key"
    MOTILAL_CLIENT_CODE: str = "your-client-code"
    
    # Motilal WebSocket Configuration
    MOTILAL_WS_URL: str = "wss://ws1feed.motilaloswal.com/jwebsocket/jwebsocket"
    MOTILAL_TRADE_WS_URL: str = "wss://openapi.motilaloswaluat.com/ws"
    MOTILAL_TCP_HOST: str = "mofeed.motilaloswal.com"
    MOTILAL_TCP_PORT: int = 18001
    
    # Market Data Settings
    MARKET_DATA_UPDATE_INTERVAL: int = 1  # seconds
    PORTFOLIO_UPDATE_INTERVAL: int = 5  # seconds
    MAX_BROADCAST_LIMIT: int = 200
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    # Trading Settings
    DEFAULT_ORDER_TYPE: str = "MARKET"
    DEFAULT_PRODUCT_TYPE: str = "NORMAL"
    DEFAULT_ORDER_DURATION: str = "DAY"
    MAX_ORDERS_PER_BATCH: int = 100
    ORDER_RETRY_ATTEMPTS: int = 3
    ORDER_TIMEOUT: int = 30  # seconds
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Environment
    DEBUG: bool = True
    TESTING: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
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

