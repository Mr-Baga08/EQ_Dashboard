# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import asyncio
import logging
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
import json
from typing import Dict, Any

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.services.websocket_manager import WebSocketManager
from app.services.motilal_service import MotilalService
from app.services.scheduler import (
    start_portfolio_scheduler,
    stop_portfolio_scheduler,
    start_market_data_scheduler,
    stop_market_data_scheduler,
    get_scheduler_status
)
from app.utils.csv_loader import load_tokens_from_csv

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/app_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Global service instances
websocket_manager = WebSocketManager()
motilal_service = MotilalService()

# Register market data broadcast callback
async def market_data_callback(data_type: str, data: dict):
    """Callback function for broadcasting market data via WebSocket"""
    try:
        message = {
            "type": "market_data",
            "data_type": data_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await websocket_manager.broadcast(message)
        logger.debug(f"Broadcasted {data_type} data to all clients")
    except Exception as e:
        logger.error(f"Error broadcasting market data: {str(e)}")

# Register portfolio update callback
async def portfolio_update_callback(client_id: str, portfolio_data: dict):
    """Callback function for broadcasting portfolio updates"""
    try:
        message = {
            "type": "portfolio_update",
            "client_id": client_id,
            "data": portfolio_data,
            "timestamp": datetime.now().isoformat()
        }
        await websocket_manager.send_personal_message(json.dumps(message), client_id)
        logger.debug(f"Sent portfolio update to client {client_id}")
    except Exception as e:
        logger.error(f"Error sending portfolio update to {client_id}: {str(e)}")

# Register callbacks with Motilal service
motilal_service.register_broadcast_callback(market_data_callback)
motilal_service.register_portfolio_callback(portfolio_update_callback)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup tasks
    logger.info("🚀 Starting Multi-Client Trading Platform...")
    startup_success = False
    
    try:
        # Create logs directory
        import os
        os.makedirs("logs", exist_ok=True)
        
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
        
        # Load tokens from CSV
        tokens_loaded = await load_tokens_from_csv()
        logger.info(f"✅ {tokens_loaded} tokens loaded from CSV")
        
        # Start background schedulers
        if settings.ENABLE_PORTFOLIO_SCHEDULER:
            await start_portfolio_scheduler()
            logger.info("✅ Portfolio scheduler started")
        
        if settings.ENABLE_MARKET_DATA_SCHEDULER:
            await start_market_data_scheduler()
            logger.info("✅ Market data scheduler started")
        
        # Initialize Motilal service connections
        logger.info("🔌 Initializing Motilal API connections...")
        await motilal_service.initialize()
        
        startup_success = True
        logger.info("🎉 Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        if not startup_success:
            raise
    
    # Shutdown tasks
    logger.info("🛑 Shutting down application...")
    try:
        # Stop schedulers
        if settings.ENABLE_PORTFOLIO_SCHEDULER:
            await stop_portfolio_scheduler()
            logger.info("✅ Portfolio scheduler stopped")
        
        if settings.ENABLE_MARKET_DATA_SCHEDULER:
            await stop_market_data_scheduler()
            logger.info("✅ Market data scheduler stopped")
        
        # Disconnect all WebSocket connections
        await websocket_manager.disconnect_all()
        logger.info("✅ WebSocket connections closed")
        
        # Close Motilal service sessions
        await motilal_service.close_session()
        motilal_service.close_websocket_connections()
        logger.info("✅ Motilal service connections closed")
        
        logger.info("🏁 Application shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")

app = FastAPI(
    title="Multi-Client Trading Platform",
    description="Advanced trading platform with Motilal Oswal API integration and real-time portfolio management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (datetime.now() - start_time).total_seconds()
        
        # Log response
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error for {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation error",
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code} for {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception for {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error"
            }
        )

# API Routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time client communication"""
    await websocket_manager.connect(websocket, client_id)
    logger.info(f"🔌 WebSocket connected: {client_id}")
    
    try:
        # Send welcome message
        welcome_message = {
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "version": "1.0.0",
                "features": ["real_time_updates", "portfolio_tracking", "market_data"]
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.debug(f"📨 Received from {client_id}: {message.get('type', 'unknown')}")
                
                # Handle different message types
                await handle_websocket_message(client_id, message, websocket)
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {client_id}: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {client_id}")
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}")
        websocket_manager.disconnect(client_id)

async def handle_websocket_message(client_id: str, message: Dict[str, Any], websocket: WebSocket):
    """Handle incoming WebSocket messages"""
    try:
        message_type = message.get("type")
        
        if message_type == "ping":
            # Handle ping/pong for connection health
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
            
        elif message_type == "subscribe_market_data":
            # Handle market data subscription
            tokens = message.get("tokens", [])
            await motilal_service.subscribe_market_data(client_id, tokens)
            await websocket.send_text(json.dumps({
                "type": "subscription_success",
                "data_type": "market_data",
                "tokens": tokens
            }))
            
        elif message_type == "unsubscribe_market_data":
            # Handle market data unsubscription
            tokens = message.get("tokens", [])
            await motilal_service.unsubscribe_market_data(client_id, tokens)
            await websocket.send_text(json.dumps({
                "type": "unsubscription_success",
                "data_type": "market_data",
                "tokens": tokens
            }))
            
        elif message_type == "get_portfolio":
            # Handle portfolio data request
            try:
                portfolio_data = await motilal_service.get_client_portfolio_realtime(client_id)
                await websocket.send_text(json.dumps({
                    "type": "portfolio_data",
                    "data": portfolio_data,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Failed to get portfolio: {str(e)}"
                }))
                
        else:
            logger.warning(f"Unknown message type from {client_id}: {message_type}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message from {client_id}: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to process message"
        }))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Check database connection
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    # Check scheduler status
    scheduler_status = await get_scheduler_status()
    
    # Check Motilal service status
    motilal_status = await motilal_service.get_service_status()
    
    # Check WebSocket connections
    ws_connections = len(websocket_manager.active_connections)
    
    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": db_status,
            "motilal_api": motilal_status,
            "schedulers": scheduler_status,
            "websockets": {
                "status": "healthy",
                "active_connections": ws_connections
            }
        },
        "uptime": datetime.now().isoformat(),  # This would be calculated from startup time
        "environment": "development" if settings.DEBUG else "production"
    }
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return JSONResponse(content=health_data, status_code=status_code)

# System info endpoint
@app.get("/info")
async def system_info():
    """Get system information"""
    import psutil
    import platform
    
    return {
        "application": {
            "name": "Multi-Client Trading Platform",
            "version": "1.0.0",
            "environment": "development" if settings.DEBUG else "production"
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available
        },
        "database": {
            "url": settings.DATABASE_URL.replace(settings.POSTGRES_PASSWORD, "***"),
            "pool_size": 20
        },
        "features": {
            "websocket_support": True,
            "real_time_updates": True,
            "market_data_streaming": True,
            "portfolio_tracking": True,
            "multi_client_support": True
        }
    }

# Metrics endpoint (for monitoring)
@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    scheduler_status = await get_scheduler_status()
    motilal_status = await motilal_service.get_service_status()
    
    return {
        "websocket_connections": len(websocket_manager.active_connections),
        "active_clients": list(websocket_manager.active_connections.keys()),
        "scheduler_status": scheduler_status,
        "motilal_service_status": motilal_status,
        "memory_usage": f"{psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB",
        "cpu_percent": psutil.Process().cpu_percent(),
        "timestamp": datetime.now().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multi-Client Trading Platform API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health_check": "/health",
        "websocket": "/ws/{client_id}",
        "api_endpoints": "/api/v1/",
        "timestamp": datetime.now().isoformat()
    }

# Startup event (for additional initialization if needed)
@app.on_event("startup")
async def startup_event():
    """Additional startup tasks"""
    logger.info("🎯 Application ready to accept requests")

# Shutdown event (for graceful cleanup)
@app.on_event("shutdown")
async def shutdown_event():
    """Additional shutdown tasks"""
    logger.info("🛑 Application shutdown initiated")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        server_header=False,
        date_header=False
    )