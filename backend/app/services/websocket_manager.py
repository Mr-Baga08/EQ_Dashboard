# backend/app/services/websocket_manager.py - Enhanced Version
import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class EnhancedWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of token symbols
        self.token_subscribers: Dict[str, Set[str]] = {}  # token symbol -> set of client_ids
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a client WebSocket"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"Client {client_id} connected to WebSocket")
        
    def disconnect(self, client_id: str):
        """Disconnect a client WebSocket"""
        if client_id in self.active_connections:
            # Remove from all token subscriptions
            subscribed_tokens = self.client_subscriptions.get(client_id, set())
            for token_symbol in subscribed_tokens:
                if token_symbol in self.token_subscribers:
                    self.token_subscribers[token_symbol].discard(client_id)
                    if not self.token_subscribers[token_symbol]:
                        del self.token_subscribers[token_symbol]
            
            # Clean up client data
            del self.active_connections[client_id]
            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]
            
            logger.info(f"Client {client_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected_clients = []
            
            for client_id, connection in self.active_connections.items():
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
    
    async def broadcast_to_clients(self, message: dict, client_ids: List[str]):
        """Send message to specific clients"""
        message_str = json.dumps(message)
        
        for client_id in client_ids:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(message_str)
                except Exception as e:
                    logger.error(f"Error sending to {client_id}: {e}")
                    self.disconnect(client_id)
    
    def subscribe_to_token(self, client_id: str, token_symbol: str):
        """Subscribe client to token updates"""
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()
        
        self.client_subscriptions[client_id].add(token_symbol)
        
        if token_symbol not in self.token_subscribers:
            self.token_subscribers[token_symbol] = set()
        
        self.token_subscribers[token_symbol].add(client_id)
        logger.info(f"Client {client_id} subscribed to {token_symbol}")
    
    def unsubscribe_from_token(self, client_id: str, token_symbol: str):
        """Unsubscribe client from token updates"""
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(token_symbol)
        
        if token_symbol in self.token_subscribers:
            self.token_subscribers[token_symbol].discard(client_id)
            if not self.token_subscribers[token_symbol]:
                del self.token_subscribers[token_symbol]
        
        logger.info(f"Client {client_id} unsubscribed from {token_symbol}")
    
    async def broadcast_market_data(self, token_symbol: str, market_data: dict):
        """Broadcast market data to subscribed clients"""
        if token_symbol not in self.token_subscribers:
            return
        
        subscribed_clients = list(self.token_subscribers[token_symbol])
        if subscribed_clients:
            message = {
                "type": "market_data",
                "token_symbol": token_symbol,
                "data": market_data,
                "timestamp": market_data.get("time")
            }
            await self.broadcast_to_clients(message, subscribed_clients)
    
    async def broadcast_portfolio_update(self, client_id: str, portfolio_data: dict):
        """Broadcast portfolio update to specific client"""
        message = {
            "type": "portfolio_update",
            "data": portfolio_data,
            "timestamp": portfolio_data.get("timestamp")
        }
        await self.send_personal_message(json.dumps(message), client_id)
    
    async def broadcast_trade_update(self, client_id: str, trade_data: dict):
        """Broadcast trade update to specific client"""
        message = {
            "type": "trade_update",
            "data": trade_data,
            "timestamp": trade_data.get("timestamp")
        }
        await self.send_personal_message(json.dumps(message), client_id)
    
    async def broadcast_order_update(self, client_id: str, order_data: dict):
        """Broadcast order update to specific client"""
        message = {
            "type": "order_update",
            "data": order_data,
            "timestamp": order_data.get("timestamp")
        }
        await self.send_personal_message(json.dumps(message), client_id)
    
    def get_token_subscribers(self, token_symbol: str) -> List[str]:
        """Get list of clients subscribed to a token"""
        return list(self.token_subscribers.get(token_symbol, set()))
    
    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """Get list of tokens a client is subscribed to"""
        return list(self.client_subscriptions.get(client_id, set()))
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                token_symbol = data.get("token_symbol")
                if token_symbol:
                    self.subscribe_to_token(client_id, token_symbol)
                    await self.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "token_symbol": token_symbol
                        }),
                        client_id
                    )
            
            elif action == "unsubscribe":
                token_symbol = data.get("token_symbol")
                if token_symbol:
                    self.unsubscribe_from_token(client_id, token_symbol)
                    await self.send_personal_message(
                        json.dumps({
                            "type": "unsubscription_confirmed",
                            "token_symbol": token_symbol
                        }),
                        client_id
                    )
            
            elif action == "ping":
                await self.send_personal_message(
                    json.dumps({"type": "pong"}),
                    client_id
                )
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from client {client_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        for client_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[client_id].close()
            except:
                pass
            self.disconnect(client_id)