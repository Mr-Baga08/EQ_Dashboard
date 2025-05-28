# backend/app/services/scheduler.py
import asyncio
import logging
from datetime import datetime, time
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.client import Client
from app.models.token import Token
from app.models.trade import Trade, TradeStatus
from app.services.motilal_service import MotilalService
from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self.motilal_service = MotilalService()
        self.websocket_manager = WebSocketManager()
        self.running = False
        self.portfolio_task = None
        self.market_data_task = None
        
    async def start_portfolio_scheduler(self):
        """Start the portfolio update scheduler"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting portfolio scheduler...")
        
        self.portfolio_task = asyncio.create_task(self._portfolio_update_loop())
        
    async def stop_portfolio_scheduler(self):
        """Stop the portfolio update scheduler"""
        self.running = False
        
        if self.portfolio_task:
            self.portfolio_task.cancel()
            try:
                await self.portfolio_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Portfolio scheduler stopped")
        
    async def start_market_data_scheduler(self):
        """Start the market data scheduler"""
        logger.info("Starting market data scheduler...")
        
        self.market_data_task = asyncio.create_task(self._market_data_loop())
        
    async def stop_market_data_scheduler(self):
        """Stop the market data scheduler"""
        if self.market_data_task:
            self.market_data_task.cancel()
            try:
                await self.market_data_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Market data scheduler stopped")
        
    async def _portfolio_update_loop(self):
        """Main loop for portfolio updates"""
        while self.running:
            try:
                await self._update_client_portfolios()
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in portfolio update loop: {str(e)}")
                await asyncio.sleep(10)  # Wait longer on error
                
    async def _market_data_loop(self):
        """Main loop for market data updates"""
        while self.running:
            try:
                await self._update_token_prices()
                await asyncio.sleep(1)  # Update every second during market hours
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in market data loop: {str(e)}")
                await asyncio.sleep(5)  # Wait longer on error
                
    async def _update_client_portfolios(self):
        """Update portfolio data for all clients"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active clients
                result = await db.execute(
                    select(Client).where(Client.is_active == True)
                )
                clients = result.scalars().all()
                
                for client in clients:
                    try:
                        # Get positions and margin data
                        positions_data = await self.motilal_service.get_client_positions(client)
                        margin_data = await self.motilal_service.get_margin_summary(client)
                        
                        if positions_data.get("status") == "SUCCESS":
                            # Calculate total P&L
                            total_pnl = sum(
                                pos.get("marktomarket", 0) 
                                for pos in positions_data.get("data", [])
                            )
                            client.total_pnl = total_pnl
                            
                        if margin_data.get("status") == "SUCCESS":
                            # Update margin information
                            margin_summary = margin_data.get("data", [])
                            
                            # Extract margin values from the summary
                            for item in margin_summary:
                                if item.get("srno") == 102:  # Total Available Margin for Cash
                                    client.margin_available = item.get("amount", 0)
                                elif item.get("srno") == 301:  # Margin Usage Cash
                                    client.margin_used = item.get("amount", 0)
                        
                        # Broadcast portfolio update via WebSocket
                        portfolio_update = {
                            "type": "portfolio_update",
                            "client_id": client.id,
                            "data": {
                                "total_pnl": client.total_pnl,
                                "margin_used": client.margin_used,
                                "margin_available": client.margin_available,
                                "available_funds": client.available_funds,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        
                        await self.websocket_manager.broadcast(portfolio_update)
                        
                    except Exception as e:
                        logger.error(f"Error updating portfolio for client {client.id}: {str(e)}")
                        continue
                
                # Commit all changes
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error in portfolio update: {str(e)}")
            
    async def _update_token_prices(self):
        """Update LTP for all active tokens"""
        try:
            # Only update during market hours
            if not self._is_market_hours():
                await asyncio.sleep(60)  # Check again in 1 minute
                return
                
            async with AsyncSessionLocal() as db:
                # Get all active and tradeable tokens
                result = await db.execute(
                    select(Token).where(
                        Token.is_active == True,
                        Token.is_tradeable == True
                    ).limit(50)  # Limit to avoid API rate limits
                )
                tokens = result.scalars().all()
                
                # Update prices for each token
                for token in tokens:
                    try:
                        ltp_data = await self.motilal_service.get_ltp_data(token)
                        
                        if ltp_data.get("status") == "SUCCESS" and "data" in ltp_data:
                            data = ltp_data["data"]
                            
                            # Update token prices (convert from paisa to rupees)
                            token.ltp = data.get("ltp", 0) / 100
                            token.open_price = data.get("open", 0) / 100
                            token.high_price = data.get("high", 0) / 100
                            token.low_price = data.get("low", 0) / 100
                            token.close_price = data.get("close", 0) / 100
                            token.volume = data.get("volume", 0)
                            
                            # Broadcast price update
                            price_update = {
                                "type": "price_update",
                                "token_id": token.id,
                                "symbol": token.symbol,
                                "data": {
                                    "ltp": token.ltp,
                                    "open": token.open_price,
                                    "high": token.high_price,
                                    "low": token.low_price,
                                    "close": token.close_price,
                                    "volume": token.volume,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }
                            
                            await self.websocket_manager.broadcast(price_update)
                            
                    except Exception as e:
                        logger.error(f"Error updating price for token {token.symbol}: {str(e)}")
                        continue
                
                # Commit all changes
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error in token price update: {str(e)}")
            
    async def _update_trade_pnl(self):
        """Update P&L for all active trades"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active trades with their tokens
                result = await db.execute(
                    select(Trade)
                    .options(selectinload(Trade.token))
                    .where(Trade.status == TradeStatus.ACTIVE)
                )
                trades = result.scalars().all()
                
                for trade in trades:
                    try:
                        if trade.token:
                            # Update current price
                            trade.current_price = trade.token.ltp
                            
                            # Calculate unrealized P&L
                            if trade.execution_type.value == "BUY":
                                trade.unrealized_pnl = (trade.current_price - trade.avg_price) * trade.quantity
                            else:  # SELL
                                trade.unrealized_pnl = (trade.avg_price - trade.current_price) * trade.quantity
                            
                            # Update total P&L
                            trade.total_pnl = trade.realized_pnl + trade.unrealized_pnl
                            
                            # Broadcast trade update
                            trade_update = {
                                "type": "trade_update",
                                "trade_id": trade.trade_id,
                                "client_id": trade.client_id,
                                "data": {
                                    "current_price": trade.current_price,
                                    "unrealized_pnl": trade.unrealized_pnl,
                                    "total_pnl": trade.total_pnl,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }
                            
                            await self.websocket_manager.send_to_clients(
                                trade_update, [str(trade.client_id)]
                            )
                            
                    except Exception as e:
                        logger.error(f"Error updating P&L for trade {trade.trade_id}: {str(e)}")
                        continue
                
                # Commit all changes
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error in trade P&L update: {str(e)}")
            
    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        now = datetime.now().time()
        
        # NSE market hours: 9:15 AM to 3:30 PM
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        # Check if it's a weekday (Monday = 0, Sunday = 6)
        is_weekday = datetime.now().weekday() < 5
        
        return is_weekday and market_open <= now <= market_close
        
    async def setup_websocket_connections(self):
        """Setup WebSocket connections for all clients"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active clients
                result = await db.execute(
                    select(Client).where(Client.is_active == True)
                )
                clients = result.scalars().all()
                
                for client in clients:
                    try:
                        # Login client to Motilal API
                        login_result = await self.motilal_service.login_client(client)
                        
                        if login_result.get("status") == "SUCCESS":
                            # Setup WebSocket connection for real-time data
                            self.motilal_service.setup_websocket_connection(client)
                            logger.info(f"WebSocket setup completed for client: {client.motilal_client_id}")
                            
                        else:
                            logger.error(f"Failed to login client {client.motilal_client_id}: {login_result.get('message')}")
                            
                    except Exception as e:
                        logger.error(f"Error setting up WebSocket for client {client.id}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in WebSocket setup: {str(e)}")
            
    async def register_active_tokens(self):
        """Register all active tokens for real-time updates"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active trades to determine which tokens to register
                result = await db.execute(
                    select(Trade)
                    .options(selectinload(Trade.token), selectinload(Trade.client))
                    .where(Trade.status == TradeStatus.ACTIVE)
                )
                trades = result.scalars().all()
                
                # Group trades by client
                client_tokens = {}
                for trade in trades:
                    if trade.client_id not in client_tokens:
                        client_tokens[trade.client_id] = []
                    client_tokens[trade.client_id].append(trade.token)
                
                # Register tokens for each client
                for client_id, tokens in client_tokens.items():
                    try:
                        # Get client object
                        client_result = await db.execute(
                            select(Client).where(Client.id == client_id)
                        )
                        client = client_result.scalar_one_or_none()
                        
                        if client:
                            for token in tokens:
                                self.motilal_service.register_token_for_updates(client, token)
                                
                    except Exception as e:
                        logger.error(f"Error registering tokens for client {client_id}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in token registration: {str(e)}")

# Global scheduler instance
scheduler = BackgroundScheduler()

# Public functions for the main application
async def start_portfolio_scheduler():
    """Start the portfolio update scheduler"""
    await scheduler.start_portfolio_scheduler()
    await scheduler.setup_websocket_connections()
    await scheduler.register_active_tokens()

async def stop_portfolio_scheduler():
    """Stop the portfolio update scheduler"""
    await scheduler.stop_portfolio_scheduler()
    scheduler.motilal_service.close_websocket_connections()

async def start_market_data_scheduler():
    """Start the market data scheduler"""
    await scheduler.start_market_data_scheduler()

async def stop_market_data_scheduler():
    """Stop the market data scheduler"""
    await scheduler.stop_market_data_scheduler()

async def get_scheduler_status():
    """Get the status of all schedulers"""
    return {
        "portfolio_scheduler_running": scheduler.running,
        "market_data_scheduler_running": scheduler.market_data_task is not None and not scheduler.market_data_task.done(),
        "websocket_connections": len(scheduler.motilal_service.ws_connections),
        "authenticated_clients": len(scheduler.motilal_service.auth_tokens)
    }