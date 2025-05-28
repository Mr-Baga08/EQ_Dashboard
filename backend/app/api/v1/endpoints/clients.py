# backend/app/api/v1/endpoints/clients.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_database
from app.models.client import Client
from app.schemas.client import ClientResponse, ClientCreate, ClientUpdate
from app.services.motilal_service import MotilalService

router = APIRouter()
motilal_service = MotilalService()

@router.get("/", response_model=List[ClientResponse])
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database)
):
    """Get all clients with their current portfolio data"""
    result = await db.execute(
        select(Client)
        .where(Client.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    clients = result.scalars().all()
    
    # Enrich with real-time data from Motilal API
    enriched_clients = []
    for client in clients:
        try:
            # Get margin data
            margin_data = await motilal_service.get_margin_summary(client)
            if margin_data.get("status") == "SUCCESS":
                # Update client with fresh data
                client.margin_available = margin_data.get("available_margin", 0)
                client.margin_used = margin_data.get("margin_used", 0)
            
            # Get positions for P&L calculation
            positions = await motilal_service.get_client_positions(client)
            if positions.get("status") == "SUCCESS":
                total_pnl = sum(pos.get("marktomarket", 0) for pos in positions.get("data", []))
                client.total_pnl = total_pnl
            
            enriched_clients.append(client)
            
        except Exception as e:
            print(f"Error enriching client {client.id}: {e}")
            enriched_clients.append(client)
    
    return enriched_clients

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get specific client details"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Enrich with real-time data
    try:
        profile_data = await motilal_service.get_client_profile(client)
        margin_data = await motilal_service.get_margin_summary(client)
        positions = await motilal_service.get_client_positions(client)
        
        if margin_data.get("status") == "SUCCESS":
            client.margin_available = margin_data.get("available_margin", 0)
            client.margin_used = margin_data.get("margin_used", 0)
        
        if positions.get("status") == "SUCCESS":
            total_pnl = sum(pos.get("marktomarket", 0) for pos in positions.get("data", []))
            client.total_pnl = total_pnl
            
    except Exception as e:
        print(f"Error enriching client {client_id}: {e}")
    
    return client

@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_database)
):
    """Create new client"""
    client = Client(**client_data.dict())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

@router.get("/{client_id}/portfolio")
async def get_client_portfolio(
    client_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get detailed portfolio for a client"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        positions = await motilal_service.get_client_positions(client)
        margin_data = await motilal_service.get_margin_summary(client)
        order_book = await motilal_service.get_order_book(client)
        trade_book = await motilal_service.get_trade_book(client)
        
        return {
            "client": client,
            "positions": positions.get("data", []),
            "margin": margin_data.get("data", []),
            "orders": order_book.get("data", []),
            "trades": trade_book.get("data", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")