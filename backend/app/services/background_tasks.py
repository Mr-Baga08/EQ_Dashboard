# backend/app/services/background_tasks.py
import asyncio
import logging
from datetime import datetime, time
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.client import Client
from app.services.motilal_service import MotilalService

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self.motilal_service = MotilalService()
        self.is_running = False
        self.refresh_interval = 300  # 5 minutes default
        
    async def start_periodic_tasks(self):
        """Start all background tasks"""
        if self.is_running:
            logger.warning("Background tasks already running")
            return
            
        self.is_running = True
        logger.info("Starting background tasks...")
        
        # Start multiple tasks concurrently
        tasks = [
            self._periodic_fund_refresh(),
            self._market_hours_check(),
            self._cleanup_old_data()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_periodic_tasks(self):
        """Stop all background tasks"""
        self.is_running = False
        logger.info("Stopping background tasks...")
        await self.motilal_service.close_session()
    
    async def _periodic_fund_refresh(self):
        """Periodically refresh client funds from Motilal API"""
        logger.info("Starting periodic fund refresh task")
        
        while self.is_running:
            try:
                # Only refresh during market hours or extended hours
                if await self._is_refresh_time():
                    await self._refresh_all_client_funds()
                else:
                    logger.debug("Outside refresh hours, skipping fund refresh")
                
                # Wait for next interval
                await asyncio.sleep(self.refresh_interval)
                
            except Exception as e:
                logger.error(f"Error in periodic fund refresh: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _refresh_all_client_funds(self):
        """Refresh funds for all active clients"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all active clients
                result = await db.execute(
                    select(Client).where(Client.is_active == True)
                )
                clients = result.scalars().all()
                
                if not clients:
                    logger.debug("No active clients found for fund refresh")
                    return
                
                logger.info(f"Refreshing funds for {len(clients)} clients")
                
                # Process clients in batches to avoid overwhelming the API
                batch_size = 5
                successful_updates = 0
                
                for i in range(0, len(clients), batch_size):
                    batch = clients[i:i + batch_size]
                    
                    # Process batch concurrently
                    tasks = []
                    for client in batch:
                        task = self._refresh_single_client_funds(client, db)
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Count successful updates
                    for result in results:
                        if not isinstance(result, Exception) and result:
                            successful_updates += 1
                    
                    # Small delay between batches
                    await asyncio.sleep(1)
                
                logger.info(f"Successfully updated {successful_updates}/{len(clients)} clients")
                
                # Commit all changes
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error refreshing all client funds: {e}")
    
    async def _refresh_single_client_funds(self, client: Client, db: AsyncSession) -> bool:
        """Refresh funds for a single client"""
        try:
            # Get financial summary from Motilal
            financial_summary = await self.motilal_service.get_client_financial_summary(client)
            
            # Update client in database
            await db.execute(
                update(Client)
                .where(Client.id == client.id)
                .values(
                    available_funds=financial_summary["available_funds"],
                    margin_used=financial_summary["margin_used"],
                    margin_available=financial_summary["margin_available"],
                    total_pnl=financial_summary["total_pnl"]
                )
            )
            
            logger.debug(f"Updated funds for client {client.motilal_client_id}: "
                        f"Available: ₹{financial_summary['available_funds']:,.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing funds for client {client.motilal_client_id}: {e}")
            return False
    
    async def _is_refresh_time(self) -> bool:
        """Check if it's appropriate time to refresh funds"""
        now = datetime.now()
        current_time = now.time()
        
        # Market hours: 9:15 AM to 3:30 PM (IST)
        # Extended hours: 8:00 AM to 6:00 PM (IST) for safety
        market_start = time(8, 0)  # 8:00 AM
        market_end = time(18, 0)   # 6:00 PM
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        is_weekday = now.weekday() < 5
        
        # Check if current time is within extended market hours
        is_market_hours = market_start <= current_time <= market_end
        
        return is_weekday and is_market_hours
    
    async def _market_hours_check(self):
        """Check market status and adjust refresh frequency"""
        while self.is_running:
            try:
                if await self._is_refresh_time():
                    # More frequent updates during market hours
                    self.refresh_interval = 300  # 5 minutes
                else:
                    # Less frequent updates outside market hours
                    self.refresh_interval = 1800  # 30 minutes
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in market hours check: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_data(self):
        """Clean up old logs and temporary data"""
        while self.is_running:
            try:
                # This is a placeholder for cleanup operations
                # You can add logic to clean up old log files, temporary data, etc.
                logger.debug("Running cleanup tasks...")
                
                # Example: Clean up old log entries (implement as needed)
                # await self._cleanup_old_logs()
                
                # Run cleanup once per day
                await asyncio.sleep(86400)  # 24 hours
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    async def refresh_client_funds_now(self, client_ids: List[int] = None):
        """Manually trigger fund refresh for specific clients or all clients"""
        try:
            async with AsyncSessionLocal() as db:
                if client_ids:
                    # Refresh specific clients
                    result = await db.execute(
                        select(Client).where(
                            Client.id.in_(client_ids),
                            Client.is_active == True
                        )
                    )
                else:
                    # Refresh all active clients
                    result = await db.execute(
                        select(Client).where(Client.is_active == True)
                    )
                
                clients = result.scalars().all()
                
                if not clients:
                    return {"updated": 0, "errors": []}
                
                # Process clients
                successful_updates = 0
                errors = []
                
                for client in clients:
                    try:
                        success = await self._refresh_single_client_funds(client, db)
                        if success:
                            successful_updates += 1
                    except Exception as e:
                        errors.append({
                            "client_id": client.id,
                            "error": str(e)
                        })
                
                await db.commit()
                
                return {
                    "updated": successful_updates,
                    "total": len(clients),
                    "errors": errors
                }
                
        except Exception as e:
            logger.error(f"Error in manual fund refresh: {e}")
            raise

# Global instance
background_task_manager = BackgroundTaskManager()