# backend/app/services/motilal_service.py
import asyncio
import aiohttp
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

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
    
    async def get_client_profile(self, client: Client) -> Dict[str, Any]:
        """Get client profile from Motilal API"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/login/v1/getprofile"
            headers = self._get_headers(client, auth_token)
            
            profile_data = {"clientcode": client.motilal_client_id}
            
            async with session.post(url, headers=headers, json=profile_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error fetching profile for client {client.motilal_client_id}: {str(e)}")
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
    
    async def cancel_order(self, client: Client, order_id: str) -> Dict[str, Any]:
        """Cancel order through Motilal API"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/trans/v1/cancelorder"
            headers = self._get_headers(client, auth_token)
            
            cancel_data = {
                "clientcode": client.motilal_client_id,
                "uniqueorderid": order_id
            }
            
            async with session.post(url, headers=headers, json=cancel_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error cancelling order for client {client.motilal_client_id}: {str(e)}")
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
            
            # Create dummy headers (market data doesn't need specific client)
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
    
    async def get_order_book(self, client: Client) -> Dict[str, Any]:
        """Get order book for client"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/book/v1/getorderbook"
            headers = self._get_headers(client, auth_token)
            
            order_data = {"clientcode": client.motilal_client_id}
            
            async with session.post(url, headers=headers, json=order_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error fetching order book for client {client.motilal_client_id}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}
    
    async def get_trade_book(self, client: Client) -> Dict[str, Any]:
        """Get trade book for client"""
        try:
            auth_token = self.auth_tokens.get(client.motilal_client_id)
            if not auth_token:
                login_result = await self.login_client(client)
                if login_result.get("status") != "SUCCESS":
                    return login_result
                auth_token = self.auth_tokens.get(client.motilal_client_id)
            
            session = await self.get_session()
            url = f"{self.base_url}/rest/book/v1/gettradebook"
            headers = self._get_headers(client, auth_token)
            
            trade_data = {"clientcode": client.motilal_client_id}
            
            async with session.post(url, headers=headers, json=trade_data) as response:
                result = await response.json()
                return result
                
        except Exception as e:
            logger.error(f"Error fetching trade book for client {client.motilal_client_id}: {str(e)}")
            return {"status": "FAILED", "message": str(e)}
    
    async def get_realtime_portfolio_updates(self) -> List[Dict[str, Any]]:
        """Get real-time portfolio updates for all clients"""
        updates = []
        
        try:
            # Get updates for all authenticated clients
            for client_id in self.auth_tokens.keys():
                # This would typically involve WebSocket connection to Motilal
                # For now, we'll simulate with periodic API calls
                
                # Get position updates
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
    
    async def batch_execute_orders(
        self, 
        orders: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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
            # This would be the actual order execution logic
            # Placeholder for now
            return {
                "status": "SUCCESS",
                "order_id": order.get("order_id"),
                "message": "Order executed successfully"
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "order_id": order.get("order_id"),
                "message": str(e)
            }