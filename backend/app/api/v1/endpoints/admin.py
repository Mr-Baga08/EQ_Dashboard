# backend/app/api/v1/endpoints/admin.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import asyncio
import logging

from app.core.database import get_database
from app.models.client import Client
from app.services.motilal_service import MotilalService
from app.services.websocket_manager import WebSocketManager

router = APIRouter()
motilal_service = MotilalService()
websocket_manager = WebSocketManager()
logger = logging.getLogger(__name__)

@router.post("/refresh-portfolio")
async def refresh_portfolio_data(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database)
):
    """
    Refresh portfolio data for all clients from Motilal API
    """
    try:
        # Get all active clients
        result = await db.execute(
            select(Client).where(Client.is_active == True)
        )
        clients = result.scalars().all()
        
        if not clients:
            return {
                "status": "SUCCESS",
                "message": "No active clients found",
                "data": {"clients": []}
            }
        
        # Refresh data for all clients
        refreshed_clients = []
        portfolio_updates = []
        
        for client in clients:
            try:
                # Get fresh data from Motilal API
                client_data = await refresh_client_portfolio(client)
                
                if client_data["status"] == "SUCCESS":
                    updated_client = client_data["client"]
                    refreshed_clients.append(updated_client)
                    
                    # Prepare WebSocket update
                    portfolio_update = {
                        "type": "portfolio_update",
                        "client_id": str(updated_client.id),
                        "data": {
                            "available_funds": updated_client.available_funds,
                            "margin_used": updated_client.margin_used,
                            "margin_available": updated_client.margin_available,
                            "total_pnl": updated_client.total_pnl,
                            "positions": client_data.get("positions", [])
                        },
                        "timestamp": client_data["timestamp"]
                    }
                    portfolio_updates.append(portfolio_update)
                    
                    logger.info(f"Successfully refreshed portfolio for client {client.motilal_client_id}")
                else:
                    logger.error(f"Failed to refresh portfolio for client {client.motilal_client_id}: {client_data['message']}")
                    refreshed_clients.append(client)  # Keep original data
                    
            except Exception as e:
                logger.error(f"Error refreshing client {client.motilal_client_id}: {str(e)}")
                refreshed_clients.append(client)  # Keep original data
        
        # Update database
        await db.commit()
        
        # Send WebSocket updates in background
        background_tasks.add_task(send_portfolio_updates, portfolio_updates)
        
        return {
            "status": "SUCCESS",
            "message": f"Portfolio data refreshed for {len(refreshed_clients)} clients",
            "data": {
                "clients": [
                    {
                        "id": client.id,
                        "name": client.name,
                        "motilal_client_id": client.motilal_client_id,
                        "available_funds": client.available_funds,
                        "total_pnl": client.total_pnl,
                        "margin_used": client.margin_used,  
                        "margin_available": client.margin_available,
                        "is_active": client.is_active,
                        "created_at": client.created_at.isoformat(),
                        "updated_at": client.updated_at.isoformat() if client.updated_at else None
                    }
                    for client in refreshed_clients
                ],
                "updated_count": len(portfolio_updates)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_portfolio_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing portfolio data: {str(e)}")

async def refresh_client_portfolio(client: Client) -> Dict[str, Any]:
    """
    Refresh portfolio data for a single client from Motilal API
    """
    try:
        from datetime import datetime
        
        # Get margin data
        margin_response = await motilal_service.get_margin_summary(client)
        
        # Get positions data
        positions_response = await motilal_service.get_client_positions(client)
        
        # Process margin data
        if margin_response.get("status") == "SUCCESS" and margin_response.get("data"):
            margin_data = margin_response["data"]
            
            # Extract key margin values
            available_margin = 0
            margin_used = 0
            
            for item in margin_data:
                if "Total Available Margin" in item.get("particulars", ""):
                    available_margin = item.get("amount", 0)
                elif "Margin Usage" in item.get("particulars", ""):
                    margin_used += item.get("amount", 0)
            
            # Update client object
            client.margin_available = available_margin
            client.margin_used = margin_used
            client.available_funds = available_margin - margin_used
        
        # Process positions data for P&L calculation
        total_pnl = 0
        positions = []
        
        if positions_response.get("status") == "SUCCESS" and positions_response.get("data"):
            positions_data = positions_response["data"]
            
            for position in positions_data:
                pnl = position.get("marktomarket", 0)
                total_pnl += pnl
                
                positions.append({
                    "symbol": position.get("symbol", ""),
                    "exchange": position.get("exchange", ""),
                    "quantity": position.get("buyquantity", 0) - position.get("sellquantity", 0),
                    "ltp": position.get("LTP", 0),
                    "pnl": pnl
                })
            
            client.total_pnl = total_pnl
        
        return {
            "status": "SUCCESS",
            "client": client,
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing client portfolio {client.motilal_client_id}: {str(e)}")
        return {
            "status": "FAILED",
            "message": str(e),
            "client": client,
            "timestamp": datetime.now().isoformat()
        }

async def send_portfolio_updates(updates: List[Dict[str, Any]]):
    """
    Send portfolio updates via WebSocket
    """
    try:
        for update in updates:
            await websocket_manager.broadcast(update)
            logger.info(f"Sent portfolio update for client {update['client_id']}")
    except Exception as e:
        logger.error(f"Error sending portfolio updates: {str(e)}")

@router.post("/refresh-client/{client_id}")
async def refresh_single_client_portfolio(
    client_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database)
):
    """
    Refresh portfolio data for a specific client
    """
    try:
        # Get client
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Refresh client data
        client_data = await refresh_client_portfolio(client)
        
        if client_data["status"] == "SUCCESS":
            await db.commit()
            
            # Send WebSocket update
            portfolio_update = {
                "type": "portfolio_update",
                "client_id": str(client.id),
                "data": {
                    "available_funds": client.available_funds,
                    "margin_used": client.margin_used,
                    "margin_available": client.margin_available,
                    "total_pnl": client.total_pnl,
                    "positions": client_data.get("positions", [])
                },
                "timestamp": client_data["timestamp"]
            }
            
            background_tasks.add_task(send_portfolio_updates, [portfolio_update])
            
            return {
                "status": "SUCCESS",
                "message": f"Portfolio refreshed for client {client.name}",
                "data": {
                    "client": {
                        "id": client.id,
                        "name": client.name,
                        "motilal_client_id": client.motilal_client_id,
                        "available_funds": client.available_funds,
                        "total_pnl": client.total_pnl,
                        "margin_used": client.margin_used,
                        "margin_available": client.margin_available,
                        "is_active": client.is_active
                    }
                }
            }
        else:
            raise HTTPException(status_code=400, detail=client_data["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing client portfolio: {str(e)}")

@router.get("/portfolio-stats")
async def get_portfolio_stats(db: AsyncSession = Depends(get_database)):
    """
    Get aggregated portfolio statistics
    """
    try:
        result = await db.execute(
            select(Client).where(Client.is_active == True)
        )
        clients = result.scalars().all()
        
        total_funds = sum(client.available_funds for client in clients)
        total_pnl = sum(client.total_pnl for client in clients)
        total_margin_used = sum(client.margin_used for client in clients)
        total_margin_available = sum(client.margin_available for client in clients)
        
        return {
            "status": "SUCCESS",
            "data": {
                "total_clients": len(clients),
                "active_clients": len([c for c in clients if c.is_active]),
                "total_funds": total_funds,
                "total_pnl": total_pnl,
                "total_margin_used": total_margin_used,
                "total_margin_available": total_margin_available,
                "margin_utilization": (total_margin_used / (total_margin_used + total_margin_available) * 100) if (total_margin_used + total_margin_available) > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting portfolio stats: {str(e)}")