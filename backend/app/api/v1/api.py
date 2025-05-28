# backend/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import clients, trades, orders, tokens

api_router = APIRouter()

api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])