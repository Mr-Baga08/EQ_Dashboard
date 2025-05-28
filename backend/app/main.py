# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.services.websocket_manager import WebSocketManager
from app.services.motilal_service import MotilalService
from app.utils.csv_loader import load_tokens_from_csv

# WebSocket manager instance
websocket_manager = WebSocketManager()
motilal_service = MotilalService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Load tokens from CSV
    await load_tokens_from_csv()
    
    # Initialize real-time data streaming
    asyncio.create_task(start_realtime_updates())
    
    yield
    
    # Shutdown tasks
    await websocket_manager.disconnect_all()

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

# Routes
app.include_router(api_router, prefix="/api/v1")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.send_personal_message(data, client_id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

async def start_realtime_updates():
    """Start real-time P/L and portfolio updates"""
    while True:
        try:
            # Fetch real-time data from Motilal API
            portfolio_updates = await motilal_service.get_realtime_portfolio_updates()
            
            # Broadcast updates to all connected clients
            for update in portfolio_updates:
                await websocket_manager.broadcast(update)
                
            await asyncio.sleep(1)  # Update every second
        except Exception as e:
            print(f"Error in real-time updates: {e}")
            await asyncio.sleep(5)  # Wait longer on error

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
