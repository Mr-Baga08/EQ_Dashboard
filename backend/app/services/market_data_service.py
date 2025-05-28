# backend/app/services/market_data_service.py
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from app.services.motilal_service import EnhancedMotilalService
from app.services.websocket_manager import EnhancedWebSocketManager
from app.models.token import Token
from app.models.client import Client
from app.core.database import AsyncSessionLocal
from sqlalchemy import select

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service to manage real-time market data and distribute updates"""
    
    def __init__(self, motilal_service: EnhancedMotilalService, websocket_manager: EnhancedWebSocketManager):
        self.motilal_service = motilal_service
        self.websocket_manager = websocket_manager
        self.token_cache: Dict[int, Token] = {}
        self.last_prices: Dict[str, float] = {}
        self.is_running = False
        
        # Add callback to motilal service for market data
        self.motilal_service.add_broadcast_callback(self.handle_market_data)
    
    async def start(self):
        """Start the market data service"""
        self.is_running = True
        logger.info("Market Data Service started")
        
        # Start background tasks
        asyncio.create_task(self.update_token_cache())
        asyncio.create_task(self.periodic_price_updates())
    
    async def stop(self):
        """Stop the market data service"""
        self.is_running = False
        logger.info("Market Data Service stopped")
    
    async def update_token_cache(self):
        """Update token cache from database"""
        while self.is_running:
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Token).where(Token.is_active == True)
                    )
                    tokens = result.scalars().all()
                    
                    self.token_cache = {token.token_id: token for token in tokens}
                    logger.debug(f"Updated token cache with {len(self.token_cache)} tokens")
                
                # Update every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error updating token cache: {e}")
                await asyncio.sleep(60)
    
    async def handle_market_data(self, packets: List[Dict], client: Client):
        """Handle market data from Motilal WebSocket"""
        try:
            for packet in packets:
                if not packet or 'scrip_code' not in packet:
                    continue
                
                scrip_code = packet['scrip_code']
                token = self.token_cache.get(scrip_code)
                
                if not token:
                    continue
                
                # Update token prices in memory
                if packet.get('type') == 'LTP':
                    new_price = packet.get('ltp_rate', 0)
                    if new_price > 0:
                        self.last_prices[token.symbol] = new_price
                        
                        # Update token in database periodically (not on every tick)
                        if self.should_update_db_price(token.symbol, new_price):
                            await self.update_token_price_in_db(token, new_price)
                
                # Broadcast to subscribed WebSocket clients
                await self.websocket_manager.broadcast_market_data(
                    token.symbol,
                    self.format_market_data(packet, token)
                )
                
        except Exception as e:
            logger.error(f"Error handling market data: {e}")
    
    def should_update_db_price(self, symbol: str, new_price: float) -> bool:
        """Determine if we should update database (reduce DB writes)"""
        # Only update DB if price changed significantly or periodically
        return True  # Simplified - you can add logic for price change threshold
    
    async def update_token_price_in_db(self, token: Token, new_price: float):
        """Update token price in database"""
        try:
            async with AsyncSessionLocal() as db:
                token.ltp = new_price
                token.updated_at = datetime.utcnow()
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error updating token price in DB: {e}")
    
    def format_market_data(self, packet: Dict, token: Token) -> Dict:
        """Format market data for WebSocket clients"""
        formatted = {
            'symbol': token.symbol,
            'token_id': token.token_id,
            'exchange': token.exchange,
            'timestamp': packet.get('time'),
            'type': packet.get('type'),
        }
        
        if packet.get('type') == 'LTP':
            formatted.update({
                'ltp': packet.get('ltp_rate'),
                'volume': packet.get('ltp_qty'),
                'avg_price': packet.get('avg_trade_price')
            })
        elif packet.get('type') == 'MarketDepth':
            formatted.update({
                'level': packet.get('level'),
                'bid_price': packet.get('bid_rate'),
                'bid_qty': packet.get('bid_qty'),
                'ask_price': packet.get('offer_rate'),
                'ask_qty': packet.get('offer_qty')
            })
        elif packet.get('type') == 'OHLC':
            formatted.update({
                'open': packet.get('open'),
                'high': packet.get('high'),
                'low': packet.get('low'),
                'close': packet.get('prev_close')
            })
        
        return formatted
    
    async def subscribe_client_to_token(self, client_id: str, token_symbol: str):
        """Subscribe client to token updates and start WebSocket if needed"""
        try:
            # Find token
            token = None
            for t in self.token_cache.values():
                if t.symbol == token_symbol:
                    token = t
                    break
            
            if not token:
                logger.error(f"Token {token_symbol} not found for subscription")
                return False
            
            # Subscribe client to WebSocket updates
            self.websocket_manager.subscribe_to_token(client_id, token_symbol)
            
            # Send current price if available
            if token_symbol in self.last_prices:
                await self.websocket_manager.broadcast_market_data(
                    token_symbol,
                    {
                        'symbol': token_symbol,
                        'ltp': self.last_prices[token_symbol],
                        'type': 'current_price',
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing client {client_id} to token {token_symbol}: {e}")
            return False
    
    async def periodic_price_updates(self):
        """Periodically fetch and update prices for active tokens"""
        while self.is_running:
            try:
                # Get tokens that have active subscribers
                active_tokens = set()
                for token_symbol in self.websocket_manager.token_subscribers.keys():
                    active_tokens.add(token_symbol)
                
                if not active_tokens:
                    await asyncio.sleep(30)
                    continue
                
                # Fetch prices for active tokens
                for token_symbol in active_tokens:
                    token = None
                    for t in self.token_cache.values():
                        if t.symbol == token_symbol:
                            token = t
                            break
                    
                    if token:
                        try:
                            # Fetch LTP from Motilal API
                            ltp_data = await self.motilal_service.get_ltp_data(token)
                            if ltp_data.get("status") == "SUCCESS" and "data" in ltp_data:
                                ltp = ltp_data["data"].get("ltp", 0) / 100  # Convert paisa to rupees
                                
                                if ltp > 0:
                                    self.last_prices[token_symbol] = ltp
                                    
                                    # Broadcast update
                                    await self.websocket_manager.broadcast_market_data(
                                        token_symbol,
                                        {
                                            'symbol': token_symbol,
                                            'ltp': ltp,
                                            'volume': ltp_data["data"].get("volume", 0),
                                            'type': 'price_update',
                                            'timestamp': datetime.now().isoformat()
                                        }
                                    )
                        except Exception as e:
                            logger.error(f"Error fetching price for {token_symbol}: {e}")
                
                # Update every 5 seconds for active tokens
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in periodic price updates: {e}")
                await asyncio.sleep(30)
    
    async def get_token_holders_with_pnl(self, token_id: int) -> List[Dict]:
        """Get all clients holding positions in a token with current P&L"""
        try:
            from app.models.trade import Trade, TradeStatus
            from sqlalchemy.orm import selectinload
            
            async with AsyncSessionLocal() as db:
                # Get active trades for this token
                result = await db.execute(
                    select(Trade)
                    .options(selectinload(Trade.client), selectinload(Trade.token))
                    .where(Trade.token_id == token_id)
                    .where(Trade.status == TradeStatus.ACTIVE)
                )
                trades = result.scalars().all()
                
                # Group by client and calculate P&L
                holders = {}
                token = self.token_cache.get(token_id)
                current_price = self.last_prices.get(token.symbol, token.ltp) if token else 0
                
                for trade in trades:
                    client_id = trade.client_id
                    if client_id not in holders:
                        holders[client_id] = {
                            'client': {
                                'id': trade.client.id,
                                'name': trade.client.name,
                                'motilal_client_id': trade.client.motilal_client_id
                            },
                            'total_quantity': 0,
                            'total_investment': 0,
                            'current_value': 0,
                            'unrealized_pnl': 0,
                            'trades': []
                        }
                    
                    quantity = trade.quantity if trade.execution_type == ExecutionType.BUY else -trade.quantity
                    investment = quantity * trade.avg_price
                    current_val = quantity * current_price
                    pnl = current_val - investment
                    
                    holders[client_id]['total_quantity'] += quantity
                    holders[client_id]['total_investment'] += investment
                    holders[client_id]['current_value'] += current_val
                    holders[client_id]['unrealized_pnl'] += pnl
                    holders[client_id]['trades'].append({
                        'trade_id': trade.trade_id,
                        'quantity': trade.quantity,
                        'avg_price': trade.avg_price,
                        'execution_type': trade.execution_type.value,
                        'entry_time': trade.entry_time.isoformat()
                    })
                
                return list(holders.values())
                
        except Exception as e:
            logger.error(f"Error getting token holders with P&L: {e}")
            return []
    
    def get_current_price(self, token_symbol: str) -> float:
        """Get current price for a token"""
        return self.last_prices.get(token_symbol, 0.0)