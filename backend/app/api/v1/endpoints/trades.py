# backend/app/api/v1/endpoints/trades.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_database
from app.models.trade import Trade, TradeStatus
from app.models.client import Client
from app.models.token import Token
from app.schemas.trade import TradeResponse, TradeCreate
from app.services.motilal_service import MotilalService

router = APIRouter()
motilal_service = MotilalService()

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    client_id: Optional[int] = None,
    token_id: Optional[int] = None,
    status: Optional[TradeStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_database)
):
    """Get trades with optional filters"""
    query = select(Trade).options(
        selectinload(Trade.client),
        selectinload(Trade.token)
    )
    
    if client_id:
        query = query.where(Trade.client_id == client_id)
    if token_id:
        query = query.where(Trade.token_id == token_id)
    if status:
        query = query.where(Trade.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return trades

@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str,
    db: AsyncSession = Depends(get_database)
):
    """Get specific trade"""
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.client), selectinload(Trade.token))
        .where(Trade.trade_id == trade_id)
    )
    trade = result.scalar_one_or_none()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade

@router.post("/{trade_id}/exit")
async def exit_trade(
    trade_id: str,
    db: AsyncSession = Depends(get_database)
):
    """Exit a specific trade"""
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.client), selectinload(Trade.token))
        .where(Trade.trade_id == trade_id)
    )
    trade = result.scalar_one_or_none()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != TradeStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Trade is not active")
    
    try:
        # Prepare exit order
        exit_order = {
            "execution_type": "SELL" if trade.execution_type.value == "BUY" else "BUY",
            "order_type": "MARKET",
            "quantity": trade.quantity,
            "product_type": trade.trade_type.value,
            "tag": f"EXIT_{trade_id}"
        }
        
        # Place exit order through Motilal API
        result = await motilal_service.place_order(trade.client, trade.token, exit_order)
        
        if result.get("status") == "SUCCESS":
            # Update trade status
            trade.status = TradeStatus.CLOSED
            trade.motilal_response = str(result)
            await db.commit()
            
            return {"status": "SUCCESS", "message": "Trade exited successfully", "order_id": result.get("uniqueorderid")}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to exit trade: {result.get('message')}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exiting trade: {str(e)}")

@router.post("/exit-by-token/{token_id}")
async def exit_trades_by_token(
    token_id: int,
    client_ids: Optional[List[int]] = None,
    db: AsyncSession = Depends(get_database)
):
    """Exit all trades for a specific token (with optional client filter)"""
    query = select(Trade).options(
        selectinload(Trade.client),
        selectinload(Trade.token)
    ).where(
        and_(
            Trade.token_id == token_id,
            Trade.status == TradeStatus.ACTIVE
        )
    )
    
    if client_ids:
        query = query.where(Trade.client_id.in_(client_ids))
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        raise HTTPException(status_code=404, detail="No active trades found for this token")
    
    exit_results = []
    
    for trade in trades:
        try:
            # Prepare exit order
            exit_order = {
                "execution_type": "SELL" if trade.execution_type.value == "BUY" else "BUY",
                "order_type": "MARKET",
                "quantity": trade.quantity,
                "product_type": trade.trade_type.value,
                "tag": f"BATCH_EXIT_{trade.trade_id}"
            }
            
            # Place exit order through Motilal API
            order_result = await motilal_service.place_order(trade.client, trade.token, exit_order)
            
            if order_result.get("status") == "SUCCESS":
                trade.status = TradeStatus.CLOSED
                trade.motilal_response = str(order_result)
                
                exit_results.append({
                    "trade_id": trade.trade_id,
                    "client_id": trade.client_id,
                    "status": "SUCCESS",
                    "order_id": order_result.get("uniqueorderid")
                })
            else:
                exit_results.append({
                    "trade_id": trade.trade_id,
                    "client_id": trade.client_id,
                    "status": "FAILED",
                    "error": order_result.get("message")
                })
                
        except Exception as e:
            exit_results.append({
                "trade_id": trade.trade_id,
                "client_id": trade.client_id,
                "status": "ERROR",
                "error": str(e)
            })
    
    await db.commit()
    
    return {
        "total_trades": len(trades),
        "results": exit_results
    }