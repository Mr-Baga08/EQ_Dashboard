# backend/app/main.py - Enhanced Version
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.services.websocket_manager import EnhancedWebSocketManager
from app.services.motilal_service import EnhancedMotilalService
from app.services.market_data_service import MarketDataService
from app.utils.csv_loader import load_tokens_from_csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service instances
websocket_manager = EnhancedWebSocketManager()
motilal_service = EnhancedMotilalService()
market_data_service = MarketDataService(motilal_service, websocket_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Starting Multi-Client Trading Platform...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
    
    # Load tokens from CSV
    await load_tokens_from_csv()
    logger.info("Tokens loaded from CSV")
    
    # Start market data service
    await market_data_service.start()
    logger.info("Market data service started")
    
    # Start background tasks
    asyncio.create_task(portfolio_update_task())
    asyncio.create_task(client_login_task())
    
    logger.info("Multi-Client Trading Platform started successfully!")
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down Multi-Client Trading Platform...")
    await market_data_service.stop()
    await websocket_manager.disconnect_all()
    motilal_service.close_websocket_connections()
    await motilal_service.close_session()
    logger.info("Shutdown complete")

app = FastAPI(
    title="Multi-Client Trading Platform",
    description="Advanced trading platform with Motilal API integration",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.handle_client_message(client_id, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "motilal_api": "connected" if motilal_service.auth_tokens else "disconnected",
            "websocket": f"{len(websocket_manager.active_connections)} clients connected",
            "market_data": "running" if market_data_service.is_running else "stopped"
        }
    }

# API endpoint to get service status
@app.get("/api/v1/status")
async def get_service_status():
    return {
        "platform_status": "operational",
        "connected_clients": len(websocket_manager.active_connections),
        "authenticated_motilal_clients": len(motilal_service.auth_tokens),
        "active_websocket_connections": len(motilal_service.websocket_connections),
        "tracked_tokens": len(market_data_service.token_cache),
        "market_data_active": market_data_service.is_running
    }

# Endpoint to manually trigger client login
@app.post("/api/v1/admin/login-clients")
async def trigger_client_login():
    """Manually trigger login for all clients"""
    asyncio.create_task(login_all_clients())
    return {"message": "Client login process triggered"}

# Endpoint to start market data for specific token
@app.post("/api/v1/admin/start-market-data/{token_symbol}")
async def start_market_data_for_token(token_symbol: str):
    """Start market data collection for specific token"""
    try:
        # This would trigger WebSocket connection for the token
        return {"message": f"Market data started for {token_symbol}"}
    except Exception as e:
        return {"error": str(e)}

async def portfolio_update_task():
    """Background task to update portfolio data"""
    while True:
        try:
            # Update portfolio data for all connected clients
            for client_id in websocket_manager.active_connections.keys():
                try:
                    # Get client portfolio data and broadcast update
                    # This is a placeholder - you would implement actual portfolio fetching
                    portfolio_data = {
                        "timestamp": asyncio.get_event_loop().time(),
                        "total_pnl": 0.0,
                        "margin_used": 0.0,
                        "margin_available": 0.0
                    }
                    
                    await websocket_manager.broadcast_portfolio_update(client_id, portfolio_data)
                    
                except Exception as e:
                    logger.error(f"Error updating portfolio for client {client_id}: {e}")
            
            # Update every 30 seconds
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in portfolio update task: {e}")
            await asyncio.sleep(60)

async def client_login_task():
    """Background task to maintain client logins"""
    await asyncio.sleep(10)  # Wait for startup to complete
    await login_all_clients()
    
    # Re-login every 4 hours to maintain sessions
    while True:
        try:
            await asyncio.sleep(14400)  # 4 hours
            await login_all_clients()
        except Exception as e:
            logger.error(f"Error in client login task: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes

async def login_all_clients():
    """Login all active clients to Motilal API"""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.client import Client
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Client).where(Client.is_active == True)
            )
            clients = result.scalars().all()
            
            logger.info(f"Attempting to login {len(clients)} clients to Motilal API")
            
            for client in clients:
                try:
                    login_result = await motilal_service.login_client(client)
                    if login_result.get("status") == "SUCCESS":
                        logger.info(f"Successfully logged in client: {client.motilal_client_id}")
                        
                        # Start WebSocket connection for real-time data
                        motilal_service.start_websocket_connection(client)
                        
                    else:
                        logger.error(f"Failed to login client {client.motilal_client_id}: {login_result.get('message')}")
                        
                except Exception as e:
                    logger.error(f"Error logging in client {client.motilal_client_id}: {e}")
                
                # Small delay between logins to avoid rate limiting
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"Error in login_all_clients: {e}")

# Add dependency injection for services
def get_motilal_service() -> EnhancedMotilalService:
    return motilal_service

def get_websocket_manager() -> EnhancedWebSocketManager:
    return websocket_manager

def get_market_data_service() -> MarketDataService:
    return market_data_service

# Add these to your API endpoints that need them
app.dependency_overrides[EnhancedMotilalService] = get_motilal_service
app.dependency_overrides[EnhancedWebSocketManager] = get_websocket_manager
app.dependency_overrides[MarketDataService] = get_market_data_service

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )