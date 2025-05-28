# backend/app/api/v1/endpoints/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from app.core.database import get_database
from app.models.client import Client
from app.models.token import Token
from app.schemas.order import OrderCreate, BatchOrderCreate
from app.services.motilal_service import MotilalService

router = APIRouter()
motilal_service = MotilalService()

@router.post("/place")
async def place_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_database)
):
    """Place a single order"""
    # Get client
    client_result = await db.execute(select(Client).where(Client.id == order_data.client_id))
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get token
    token_result = await db.execute(select(Token).where(Token.id == order_data.token_id))
    token = token_result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    try:
        # Prepare order for Motilal API
        motilal_order = {
            "execution_type": order_data.execution_type,
            "order_type": order_data.order_type,
            "quantity": order_data.quantity,
            "price": order_data.price,
            "product_type": order_data.trade_type,
            "order_duration": "DAY",
            "disclosed_quantity": 0,
            "amo_order": "N",
            "tag": order_data.tag or ""
        }
        
        # Place order through Motilal API
        result = await motilal_service.place_order(client, token, motilal_order)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error placing order: {str(e)}")

@router.post("/execute-all")
async def execute_all_orders(
    batch_order: BatchOrderCreate,
    db: AsyncSession = Depends(get_database)
):
    """Execute orders for all clients with specified quantities"""
    
    # Get token
    token_result = await db.execute(select(Token).where(Token.id == batch_order.token_id))
    token = token_result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Prepare orders for batch execution
    orders_to_execute = []
    
    for client_order in batch_order.client_orders:
        if client_order.quantity > 0:  # Only execute if quantity > 0
            # Get client
            client_result = await db.execute(select(Client).where(Client.id == client_order.client_id))
            client = client_result.scalar_one_or_none()
            
            if client:
                order = {
                    "client": client,
                    "token": token,
                    "order_data": {
                        "execution_type": batch_order.execution_type,
                        "order_type": batch_order.order_type,
                        "quantity": client_order.quantity,
                        "price": batch_order.price,
                        "product_type": batch_order.trade_type,
                        "tag": f"BATCH_{batch_order.token_id}"
                    }
                }
                orders_to_execute.append(order)
    
    if not orders_to_execute:
        raise HTTPException(status_code=400, detail="No valid orders to execute")
    
    # Execute orders concurrently
    results = []
    for order in orders_to_execute:
        try:
            result = await motilal_service.place_order(
                order["client"], 
                order["token"], 
                order["order_data"]
            )
            results.append({
                "client_id": order["client"].id,
                "client_name": order["client"].name,
                "status": result.get("status"),
                "order_id": result.get("uniqueorderid"),
                "message": result.get("message")
            })
        except Exception as e:
            results.append({
                "client_id": order["client"].id,
                "client_name": order["client"].name,
                "status": "ERROR",
                "error": str(e)
            })
    
    return {
        "total_orders": len(orders_to_execute),
        "results": results
    }