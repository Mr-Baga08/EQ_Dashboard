# backend/app/services/websocket_manager.py
import asyncio
import json
from typing import Dict, List
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected to WebSocket")
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected_clients = []
            
            for client_id, connection in self.active_connections.items():
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    print(f"Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
    
    async def send_to_clients(self, message: dict, client_ids: List[str]):
        """Send message to specific clients"""
        message_str = json.dumps(message)
        
        for client_id in client_ids:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(message_str)
                except Exception as e:
                    print(f"Error sending to {client_id}: {e}")
                    self.disconnect(client_id)
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        for client_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[client_id].close()
            except:
                pass
            self.disconnect(client_id)