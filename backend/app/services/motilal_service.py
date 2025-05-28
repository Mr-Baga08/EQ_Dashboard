# backend/app/services/motilal_service.py
import asyncio
import aiohttp
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import websocket
import struct
import time
from threading import Thread
from queue import Queue

from app.core.config import settings
from app.models.client import Client
from app.models.trade import Trade, TradeType, ExecutionType
from app.models.token import Token

logger = logging.getLogger(__name__)

class MotilalService:
    def __init__(self):
        self.base_url = settings.MOTILAL_BASE_URL
        self.api_key = settings.MOTILAL_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_tokens: Dict[str, str] = {}
        
        # WebSocket connections for real-time data
        self.ws_connections: Dict[str, websocket.WebSocket] = {}
        self.broadcast_callbacks: List[callable] = []
        
        # Message queue for WebSocket data
        self.message_queue = Queue()
        self.response_packet_length = 30
        
    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _get_headers(self, client: Client, auth_token: str = None) -> Dict[str, str]:
        """Generate headers for Motilal API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "MOSL/V.1.1.0",
            "apikey": self.api_key,
            "macaddress": "00:00:00:00:00:00",
            "clientlocalip": "127.0.0.1",
            "sourceid": "WEB",
            "clientpublicip": "127.0.0.1",
            "osname": "Ubuntu 20.04.3 LTS",
            "osversion": "20.04",
            "devicemodel": "VMware Virtual Platform",
            "manufacturer": "unknown",
            "productname": "Investor",
            "productversion": "1",
            "latitude": "19.0760",
            "longitude": "72.8777",
            "sdkversion": "Python 3.0",
            "browsername": "Chrome",
            "browserversion": "105.0"
        }
        
        if auth_token:
            headers["Authorization"] = auth_token
            
        return headers
    
    async def login_client(self, client: Client) -> Dict[str, Any]:
        """Login client to Motilal API"""
        try:
            session = await self.get_session()
            
            # Create password hash
            password_api_combination = client.encrypted_password + self.api_key
            password_hash = hashlib.sha256(password_api_combination.encode("utf-8")).hexdigest()
            
            login_data = {
                "userid": client.motilal_client_id,
                "password": password_hash,
                "2FA": client.two_fa
            }
            
            if client.totp:
                login_data["totp"] = client.totp
            
            url = f"{self.base_url}/rest/login/v4/authdirectapi"
            headers = self._get_headers(client)
            
            async with session.post(url, headers=headers, json=login_data) as response:
                result = await response.json()
                
                if result.get("status") == "SUCCESS":
                    self.auth_tokens[client.motilal_client_id] = result.get("AuthToken")
                    logger.info(f"Successfully logged in client: {client.motilal_client_id}")
                    return result
                else:
                    logger.error(f"Login failed for client {client.motilal_client_id}: {result}")
                    return result
                    
        except Exception as e:
            logger.error(f"Error logging in client {client.motilal_client_id}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}
    
    async def place_order(
        self, 
        client: Client, 
        token: Token, 
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Place order through Motilal API"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/trans/v1/placeorder"
            headers = self._get_headers(client, auth_token)
            
            # Prepare order payload
            order_payload = {
                "clientcode": client.motilal_client_id,
                "exchange": token.exchange,
                "symboltoken": token.token_id,
                "buyorsell": order_data["execution_type"],
                "ordertype": order_data["order_type"],
                "producttype": order_data.get("product_type", "NORMAL"),
                "orderduration": order_data.get("order_duration", "DAY"),
                "quantityinlot": order_data["quantity"],
                "price": order_data.get("price", 0),
                "triggerprice": order_data.get("trigger_price", 0),
                "disclosedquantity": order_data.get("disclosed_quantity", 0),
                "amoorder": order_data.get("amo_order", "N"),
                "tag": order_data.get("tag", ""),
                "algoid": order_data.get("algo_id", ""),
                "goodtilldate": order_data.get("good_till_date", ""),
                "participantcode": order_data.get("participant_code", "")
            }
            
            async with session.post(url, headers=headers, json=order_payload) as response:
                result = await response.json()
                logger.info(f"Order placed for client {client.motilal_client_id}: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Error placing order for client {client.motilal_client_id}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}

    async def get_client_positions(self, client: Client) -> Dict[str, Any]:
        """Get client positions from Motilal API"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/book/v1/getposition"
            headers = self._get_headers(client, auth_token)
            
            position_data = {"clientcode": client.motilal_client_id}
            
            async with session.post(url, headers=headers, json=position_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error fetching positions for client {client.motilal_client_id}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}

    async def get_margin_summary(self, client: Client) -> Dict[str, Any]:
        """Get margin summary from Motilal API"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/report/v1/getreportmarginsummary"
            headers = self._get_headers(client, auth_token)
            
            margin_data = {"clientcode": client.motilal_client_id}
            
            async with session.post(url, headers=headers, json=margin_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error fetching margin for client {client.motilal_client_id}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}

    async def get_ltp_data(self, token: Token) -> Dict[str, Any]:
        """Get LTP data for a token"""
        try:
            # Use any logged-in client for LTP data (market data doesn't require specific client)
            if not self.auth_tokens:
                logger.error("No authenticated clients available for LTP data")
                return {"status": "FAILED", "message": "No authenticated clients"}
            
            client_id, auth_token = next(iter(self.auth_tokens.items()))
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/report/v1/getltpdata"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": auth_token,
                "User-Agent": "MOSL/V.1.1.0",
                "apikey": self.api_key,
                "macaddress": "00:00:00:00:00:00",
                "clientlocalip": "127.0.0.1",
                "sourceid": "WEB",
                "clientpublicip": "127.0.0.1",
                "sdkversion": "Python 3.0"
            }
            
            ltp_data = {
                "exchange": token.exchange,
                "scripcode": token.token_id
            }
            
            async with session.post(url, headers=headers, json=ltp_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error fetching LTP for token {token.symbol}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}

    # WebSocket Broadcasting Methods
    def setup_websocket_connection(self, client: Client):
        """Setup WebSocket connection for real-time data"""
        try:
            ws_url = "wss://ws1feed.motilaloswal.com/jwebsocket/jwebsocket"
            
            def on_open(ws):
                logger.info(f"WebSocket connection opened for client: {client.motilal_client_id}")
                self._send_login_packet(ws, client)
            
            def on_message(ws, message):
                self._process_websocket_message(message, client)
            
            def on_error(ws, error):
                logger.error(f"WebSocket error for client {client.motilal_client_id}: {error}")
                if "timed" in str(error) or "Connection" in str(error):
                    # Reconnect on connection errors
                    self.setup_websocket_connection(client)
            
            def on_close(ws, close_status_code, close_msg):
                logger.info(f"WebSocket connection closed for client: {client.motilal_client_id}")
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            self.ws_connections[client.motilal_client_id] = ws
            
            # Start WebSocket in a separate thread
            ws_thread = Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
        except Exception as e:
            logger.error(f"Error setting up WebSocket for client {client.motilal_client_id}: {str(e)}")

    def _send_login_packet(self, ws, client: Client):
        """Send login packet to WebSocket"""
        try:
            msg_type = "Q".encode()
            clientcode = client.motilal_client_id
            websocket_version = "VER 2.0"
            
            clientcode_buffer1 = clientcode.ljust(15, " ").encode()
            clientcode_buffer2 = clientcode.ljust(30, " ").encode()
            version_buffer = websocket_version.ljust(10, " ").encode()
            padding = (" " * 45).encode()
            
            login_packet = struct.pack(
                "=cHB15sB30sBBBB10sBBBBB45s",
                msg_type, 111, len(clientcode), clientcode_buffer1,
                len(clientcode), clientcode_buffer2, 1, 1, 1,
                len(websocket_version), version_buffer, 0, 0, 0, 0, 1, padding
            )
            
            ws.send(login_packet)
            logger.info(f"Login packet sent for client: {client.motilal_client_id}")
            
        except Exception as e:
            logger.error(f"Error sending login packet for client {client.motilal_client_id}: {str(e)}")

    def register_token_for_updates(self, client: Client, token: Token):
        """Register a token for real-time updates"""
        try:
            ws = self.ws_connections.get(client.motilal_client_id)
            if not ws:
                logger.error(f"No WebSocket connection for client: {client.motilal_client_id}")
                return
            
            # Map exchange names to codes
            exchange_map = {
                "NSECD": "C",
                "NCDEX": "D", 
                "BSEFO": "G"
            }
            
            exchange_code = exchange_map.get(token.exchange, token.exchange[0])
            
            msg_type = "D".encode()
            exchange = exchange_code.encode()
            exchangetype = "C".encode()  # Default to CASH
            script = token.token_id
            add_to_list = 1
            
            register_packet = struct.pack(
                "=cHcciB",
                msg_type, 7, exchange, exchangetype, script, add_to_list
            )
            
            ws.send(register_packet)
            logger.info(f"Token {token.symbol} registered for updates for client: {client.motilal_client_id}")
            
        except Exception as e:
            logger.error(f"Error registering token {token.symbol} for client {client.motilal_client_id}: {str(e)}")

    def _process_websocket_message(self, message, client: Client):
        """Process incoming WebSocket messages"""
        try:
            if len(message) % self.response_packet_length == 0:
                self._parse_websocket_packets(message, client)
            else:
                # Handle partial packets
                for byte in message:
                    self.message_queue.put(byte)
                    if self.message_queue.qsize() == 30:
                        packet_data = []
                        for _ in range(30):
                            packet_data.append(self.message_queue.get())
                        self._parse_websocket_packets(bytes(packet_data), client)
                        
        except Exception as e:
            logger.error(f"Error processing WebSocket message for client {client.motilal_client_id}: {str(e)}")

    def _parse_websocket_packets(self, message, client: Client):
        """Parse WebSocket packets and extract market data"""
        try:
            packets = []
            for i in range(0, len(message), self.response_packet_length):
                packet = message[i:i + self.response_packet_length]
                if len(packet) == self.response_packet_length:
                    packets.append(packet)
            
            for packet in packets:
                # Extract header information
                exchange = packet[:1].decode()
                scrip = int.from_bytes(packet[1:5], byteorder="little", signed=True)
                timestamp = int.from_bytes(packet[5:9], byteorder="little", signed=True)
                msg_type = packet[9:10].decode()
                body = packet[10:30]
                
                # Convert timestamp
                epoch_base = datetime(1980, 1, 1, 0, 0, 0).timestamp()
                actual_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp + epoch_base))
                
                # Process different message types
                if msg_type == "A":  # LTP
                    ltp_data = self._parse_ltp_packet(exchange, scrip, actual_time, body)
                    self._broadcast_market_data("LTP", ltp_data)
                elif msg_type in ["B", "C", "D", "E", "F"]:  # Market Depth
                    depth_data = self._parse_market_depth_packet(exchange, scrip, actual_time, msg_type, body)
                    self._broadcast_market_data("MarketDepth", depth_data)
                elif msg_type == "G":  # Day OHLC
                    ohlc_data = self._parse_ohlc_packet(exchange, scrip, actual_time, body)
                    self._broadcast_market_data("DayOHLC", ohlc_data)
                elif msg_type == "1":  # Heartbeat
                    self._send_heartbeat_response(client)
                    
        except Exception as e:
            logger.error(f"Error parsing WebSocket packets for client {client.motilal_client_id}: {str(e)}")

    def _parse_ltp_packet(self, exchange, scrip, time_str, body):
        """Parse LTP packet data"""
        rate = struct.unpack("f", body[:4])[0]
        qty = int.from_bytes(body[4:8], byteorder="little", signed=True)
        cumulative_qty = int.from_bytes(body[8:12], byteorder="little", signed=True)
        avg_price = struct.unpack("f", body[12:16])[0]
        open_interest = int.from_bytes(body[16:20], byteorder="little", signed=True)
        
        # Map exchange codes to names
        exchange_names = {
            "N": "NSE" if scrip <= 34999 or (888801 <= scrip <= 888820) else "NSEFO",
            "B": "BSE",
            "M": "MCX",
            "D": "NCDEX",
            "C": "NSECD",
            "G": "BSEFO"
        }
        
        return {
            "Exchange": exchange_names.get(exchange, exchange),
            "Scrip Code": scrip,
            "Time": time_str,
            "LTP_Rate": round(rate, 2),
            "LTP_Qty": qty,
            "LTP_Cumulative Qty": cumulative_qty,
            "LTP_AvgTradePrice": round(avg_price, 2),
            "LTP_Open Interest": open_interest
        }

    def _parse_market_depth_packet(self, exchange, scrip, time_str, msg_type, body):
        """Parse market depth packet data"""
        bid_rate = struct.unpack("f", body[:4])[0]
        bid_qty = int.from_bytes(body[4:8], byteorder="little", signed=True)
        bid_orders = int.from_bytes(body[8:10], byteorder="little", signed=True)
        offer_rate = struct.unpack("f", body[10:14])[0]
        offer_qty = int.from_bytes(body[14:18], byteorder="little", signed=True)
        offer_orders = int.from_bytes(body[18:20], byteorder="little", signed=True)
        
        level_map = {"B": 1, "C": 2, "D": 3, "E": 4, "F": 5}
        
        return {
            "Exchange": exchange,
            "Scrip Code": scrip,
            "Time": time_str,
            "BidRate": round(bid_rate, 2),
            "BidQty": bid_qty,
            "BidOrder": bid_orders,
            "OfferRate": round(offer_rate, 2),
            "OfferQty": offer_qty,
            "OfferOrder": offer_orders,
            "Level": level_map.get(msg_type, 1)
        }

    def _parse_ohlc_packet(self, exchange, scrip, time_str, body):
        """Parse OHLC packet data"""
        open_price = struct.unpack("f", body[:4])[0]
        high_price = struct.unpack("f", body[4:8])[0]
        low_price = struct.unpack("f", body[8:12])[0]
        prev_close = struct.unpack("f", body[12:16])[0]
        
        return {
            "Exchange": exchange,
            "Scrip Code": scrip,
            "Time": time_str,
            "Open": round(open_price, 2),
            "High": round(high_price, 2),
            "Low": round(low_price, 2),
            "PrevDayClose": round(prev_close, 2)
        }

    def _send_heartbeat_response(self, client: Client):
        """Send heartbeat response"""
        try:
            ws = self.ws_connections.get(client.motilal_client_id)
            if ws:
                msg_type = "1".encode()
                heartbeat_packet = struct.pack("=cH", msg_type, 0)
                ws.send(heartbeat_packet)
                logger.debug(f"Heartbeat response sent for client: {client.motilal_client_id}")
        except Exception as e:
            logger.error(f"Error sending heartbeat for client {client.motilal_client_id}: {str(e)}")

    def _broadcast_market_data(self, data_type: str, data: Dict[str, Any]):
        """Broadcast market data to all registered callbacks"""
        try:
            for callback in self.broadcast_callbacks:
                asyncio.create_task(callback(data_type, data))
        except Exception as e:
            logger.error(f"Error broadcasting market data: {str(e)}")

    def register_broadcast_callback(self, callback):
        """Register a callback for market data broadcasts"""
        self.broadcast_callbacks.append(callback)

    def unregister_broadcast_callback(self, callback):
        """Unregister a callback for market data broadcasts"""
        if callback in self.broadcast_callbacks:
            self.broadcast_callbacks.remove(callback)

    async def batch_execute_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple orders in batch"""
        results = []
        
        # Execute orders concurrently for better performance
        tasks = []
        for order in orders:
            if order["quantity"] > 0:  # Only execute if quantity > 0
                task = self._execute_single_order(order)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results

    async def _execute_single_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single order"""
        try:
            client = order["client"]
            token = order["token"]
            order_data = order["order_data"]
            
            result = await self.place_order(client, token, order_data)
            
            return {
                "status": result.get("status", "FAILED"),
                "order_id": result.get("uniqueorderid"),
                "client_id": client.id,
                "message": result.get("message", "Order execution completed")
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "order_id": order.get("order_id"),
                "client_id": order.get("client", {}).get("id"),
                "message": str(e)
            }

    async def get_realtime_portfolio_updates(self) -> List[Dict[str, Any]]:
        """Get real-time portfolio updates for all clients"""
        updates = []
        
        try:
            # Get updates for all authenticated clients
            for client_id in self.auth_tokens.keys():
                # Get position updates (this would typically come from WebSocket)
                position_update = {
                    "type": "portfolio_update",
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "positions": [],  # Would be populated from real API
                        "pnl": 0.0,
                        "margin_used": 0.0,
                        "margin_available": 0.0
                    }
                }
                updates.append(position_update)
                
        except Exception as e:
            logger.error(f"Error getting real-time updates: {str(e)}")
            
        return updates

    def close_websocket_connections(self):
        """Close all WebSocket connections"""
        try:
            for client_id, ws in self.ws_connections.items():
                try:
                    ws.close()
                    logger.info(f"WebSocket connection closed for client: {client_id}")
                except Exception as e:
                    logger.error(f"Error closing WebSocket for client {client_id}: {str(e)}")
            
            self.ws_connections.clear()
            logger.info("All WebSocket connections closed")
            
        except Exception as e:
            logger.error(f"Error closing WebSocket connections: {str(e)}")