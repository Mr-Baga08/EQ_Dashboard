# backend/app/api/v1/endpoints/tokens.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List

from app.core.database import get_database
from app.models.token import Token
from app.schemas.token import TokenResponse
from app.services.motilal_service import MotilalService

router = APIRouter()
motilal_service = MotilalService()

@router.get("/search", response_model=List[TokenResponse])
async def search_tokens(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_database)
):
    """Search tokens by symbol name"""
    result = await db.execute(
        select(Token)
        .where(
            and_(
                Token.is_active == True,
                or_(
                    Token.symbol.ilike(f"%{q}%"),
                    Token.symbol.ilike(f"{q}%")
                )
            )
        )
        .limit(limit)
    )
    tokens = result.scalars().all()
    
    # Enrich with real-time LTP data
    enriched_tokens = []
    for token in tokens:
        try:
            ltp_data = await motilal_service.get_ltp_data(token)
            if ltp_data.get("status") == "SUCCESS" and "data" in ltp_data:
                token.ltp = ltp_data["data"].get("ltp", 0) / 100  # Convert from paisa to rupees
                token.open_price = ltp_data["data"].get("open", 0) / 100
                token.high_price = ltp_data["data"].get("high", 0) / 100
                token.low_price = ltp_data["data"].get("low", 0) / 100
                token.close_price = ltp_data["data"].get("close", 0) / 100
                token.volume = ltp_data["data"].get("volume", 0)
        except Exception as e:
            print(f"Error enriching token {token.symbol}: {e}")
        
        enriched_tokens.append(token)
    
    return enriched_tokens

@router.get("/{token_id}", response_model=TokenResponse)
async def get_token(
    token_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get specific token details"""
    result = await db.execute(select(Token).where(Token.id == token_id))
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Enrich with real-time data
    try:
        ltp_data = await motilal_service.get_ltp_data(token)
        if ltp_data.get("status") == "SUCCESS" and "data" in ltp_data:
            token.ltp = ltp_data["data"].get("ltp", 0) / 100
            token.open_price = ltp_data["data"].get("open", 0) / 100
            token.high_price = ltp_data["data"].get("high", 0) / 100
            token.low_price = ltp_data["data"].get("low", 0) / 100
            token.close_price = ltp_data["data"].get("close", 0) / 100
            token.volume = ltp_data["data"].get("volume", 0)
    except Exception as e:
        print(f"Error enriching token {token.symbol}: {e}")
    
    return token

@router.get("/{token_id}/holders")
async def get_token_holders(
    token_id: int,
    db: AsyncSession = Depends(get_database)
):
    """Get all clients holding positions in this token"""
    from app.models.trade import Trade, TradeStatus
    
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.client))
        .where(
            and_(
                Trade.token_id == token_id,
                Trade.status == TradeStatus.ACTIVE
            )
        )
    )
    trades = result.scalars().all()
    
    # Group by client
    holders = {}
    for trade in trades:
        client_id = trade.client_id
        if client_id not in holders:
            holders[client_id] = {
                "client": trade.client,
                "total_quantity": 0,
                "total_value": 0,
                "avg_price": 0,
                "trades": []
            }
        
        holders[client_id]["total_quantity"] += trade.quantity
        holders[client_id]["total_value"] += trade.quantity * trade.avg_price
        holders[client_id]["trades"].append(trade)
    
    # Calculate average prices
    for holder in holders.values():
        if holder["total_quantity"] > 0:
            holder["avg_price"] = holder["total_value"] / holder["total_quantity"]
    
    return list(holders.values())
    