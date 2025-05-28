# backend/app/api/v1/endpoints/clients.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
import asyncio

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
    """Get all clients with their current portfolio data fetched from Motilal API"""
    result = await db.execute(
        select(Client)
        .where(Client.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    clients = result.scalars().all()
    
    # Enrich with real-time data from Motilal API
    enriched_clients = []
    
    # Process clients concurrently for better performance
    tasks = []
    for client in clients:
        task = _enrich_client_data(client, db)
        tasks.append(task)
    
    if tasks:
        enriched_clients = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_clients = []
        for i, result in enumerate(enriched_clients):
            if isinstance(result, Exception):
                print(f"Error enriching client {clients[i].id}: {result}")
                valid_clients.append(clients[i])  # Return original client data
            else:
                valid_clients.append(result)
        
        enriched_clients = valid_clients
    else:
        enriched_clients = clients
    
    return enriched_clients

async def _enrich_client_data(client: Client, db: AsyncSession) -> Client:
    """Enrich single client with real-time financial data"""
    try:
        # Get comprehensive financial summary from Motilal
        financial_summary = await motilal_service.get_client_financial_summary(client)
        
        # Update client object with fresh data
        client.available_funds = financial_summary["available_funds"]
        client.margin_used = financial_summary["margin_used"]
        client.margin_available = financial_summary["margin_available"]
        client.total_pnl = financial_summary["total_pnl"]
        
        # Optionally update the database with fresh data
        await db.execute(
            update(Client)
            .where(Client.id == client.id)
            .values(
                available_funds=client.available_funds,
                margin_used=client.margin_used,
                margin_available=client.margin_available,
                total_pnl=client.total_pnl
            )
        )
        await db.commit()
        
        return client
        
    except Exception as e:
        print(f"Error enriching client {client.id}: {e}")
        # Return original client data if enrichment fails
        return client

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get specific client details with real-time data"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Enrich with real-time data
    try:
        financial_summary = await motilal_service.get_client_financial_summary(client)
        
        # Update client with fresh data
        client.available_funds = financial_summary["available_funds"]
        client.margin_used = financial_summary["margin_used"]
        client.margin_available = financial_summary["margin_available"]
        client.total_pnl = financial_summary["total_pnl"]
        
        # Update database
        await db.execute(
            update(Client)
            .where(Client.id == client_id)
            .values(
                available_funds=client.available_funds,
                margin_used=client.margin_used,
                margin_available=client.margin_available,
                total_pnl=client.total_pnl
            )
        )
        await db.commit()
            
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

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_database)
):
    """Update client details"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Update only provided fields
    update_data = client_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    await db.commit()
    await db.refresh(client)
    return client

@router.get("/{client_id}/portfolio")
async def get_client_portfolio(
    client_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get detailed portfolio for a client from Motilal API"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        # Fetch all portfolio data concurrently
        tasks = [
            motilal_service.get_client_positions(client),
            motilal_service.get_margin_summary(client),
            motilal_service.get_order_book(client),
            motilal_service.get_trade_book(client),
        ]
        
        positions, margin_data, order_book, trade_book = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        
        # Handle exceptions
        def safe_get_data(result, default_value=None):
            if isinstance(result, Exception):
                print(f"Error fetching data: {result}")
                return {"status": "FAILED", "data": default_value or []}
            return result
        
        positions = safe_get_data(positions)
        margin_data = safe_get_data(margin_data)
        order_book = safe_get_data(order_book)
        trade_book = safe_get_data(trade_book)
        
        return {
            "client": client,
            "positions": positions.get("data", []),
            "margin": margin_data.get("data", []),
            "orders": order_book.get("data", []),
            "trades": trade_book.get("data", []),
            "financial_summary": {
                "available_funds": client.available_funds,
                "margin_used": client.margin_used,
                "margin_available": client.margin_available,
                "total_pnl": client.total_pnl
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolio: {str(e)}")

@router.post("/{client_id}/refresh-funds")
async def refresh_client_funds(
    client_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Manually refresh client's financial data from Motilal API"""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        # Force refresh financial data
        financial_summary = await motilal_service.get_client_financial_summary(client)
        
        # Update client with fresh data
        client.available_funds = financial_summary["available_funds"]
        client.margin_used = financial_summary["margin_used"] 
        client.margin_available = financial_summary["margin_available"]
        client.total_pnl = financial_summary["total_pnl"]
        
        # Update database
        await db.execute(
            update(Client)
            .where(Client.id == client_id)
            .values(
                available_funds=client.available_funds,
                margin_used=client.margin_used,
                margin_available=client.margin_available,
                total_pnl=client.total_pnl
            )
        )
        await db.commit()
        
        return {
            "status": "SUCCESS",
            "message": "Client financial data refreshed successfully",
            "data": {
                "available_funds": client.available_funds,
                "margin_used": client.margin_used,
                "margin_available": client.margin_available,
                "total_pnl": client.total_pnl
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing client funds: {str(e)}")

@router.post("/refresh-all-funds")
async def refresh_all_clients_funds(
    db: AsyncSession = Depends(get_database)
):
    """Refresh financial data for all active clients"""
    result = await db.execute(
        select(Client).where(Client.is_active == True)
    )
    clients = result.scalars().all()
    
    if not clients:
        return {
            "status": "SUCCESS",
            "message": "No active clients found",
            "data": {"updated_clients": 0}
        }
    
    updated_count = 0
    errors = []
    
    # Process clients concurrently
    tasks = []
    for client in clients:
        task = _refresh_single_client(client, db)
        tasks.append(task)
    
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "client_id": clients[i].id,
                    "error": str(result)
                })
            elif result:
                updated_count += 1
    
    return {
        "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
        "message": f"Updated {updated_count} out of {len(clients)} clients",
        "data": {
            "total_clients": len(clients),
            "updated_clients": updated_count,
            "errors": errors
        }
    }

async def _refresh_single_client(client: Client, db: AsyncSession) -> bool:
    """Refresh financial data for a single client"""
    try:
        financial_summary = await motilal_service.get_client_financial_summary(client)
        
        # Update database
        await db.execute(
            update(Client)
            .where(Client.id == client.id)
            .values(
                available_funds=financial_summary["available_funds"],
                margin_used=financial_summary["margin_used"],
                margin_available=financial_summary["margin_available"],
                total_pnl=financial_summary["total_pnl"]
            )
        )
        await db.commit()
        
        return True
        
    except Exception as e:
        print(f"Error refreshing client {client.id}: {e}")
        return False