"""
Dhan Scheduler

Scheduler that runs every 15 minutes to refresh option chain data for all NSE symbols.
This ensures that cached option data is regularly updated.
"""

import asyncio
import logging
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.dhan_service import DhanService

# Set up logging
logger = logging.getLogger(__name__)

class DhanScheduler:
    """Scheduler for periodic option chain data refresh"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.dhan_service = DhanService()
        self.is_running = False

        # Fixed parameters
        self.exchange = "NSE"
        self.expiry = "2025-08-28"

        logger.info("🕒 Dhan Scheduler initialized")

    async def refresh_all_symbols_option_data(self):
        """
        Refresh option chain data for all NSE symbols

        This method:
        1. Gets all NSE symbols from FNO symbols
        2. Calls dhan_service.get_option_chain_with_analytics_by_symbol for each
        3. Logs progress and statistics
        """
        try:
            start_time = datetime.now()
            logger.info(f"🔄 Starting scheduled option data refresh at {start_time.strftime('%H:%M:%S')}")

            # Get all NSE symbols
            nse_symbols = self._get_nse_symbols()
            if not nse_symbols:
                logger.warning("⚠️ No NSE symbols found for refresh")
                return

            logger.info(f"📊 Refreshing option data for {len(nse_symbols)} NSE symbols")

            # Statistics tracking
            successful_refreshes = 0
            failed_refreshes = 0
            failed_symbols = []

            # Process each symbol
            for i, symbol in enumerate(nse_symbols, 1):
                try:
                    logger.info(f"🔄 Processing {i}/{len(nse_symbols)}: {symbol}")

                    # Call the service method to get fresh data and cache it
                    strikes_with_analytics = await self.dhan_service.get_option_chain_with_analytics_by_symbol(
                        symbol=symbol,
                        exchange=self.exchange,
                        expiry=self.expiry
                    )

                    successful_refreshes += 1
                    logger.info(f"✅ Successfully refreshed {symbol}: {len(strikes_with_analytics)} strikes")

                    # Add delay between requests to avoid rate limiting
                    if i < len(nse_symbols):  # Don't delay after the last symbol
                        await asyncio.sleep(3)  # 3-second delay between symbols

                except Exception as e:
                    failed_refreshes += 1
                    failed_symbols.append({"symbol": symbol, "error": str(e)})
                    logger.error(f"❌ Failed to refresh {symbol}: {e}")
                    continue

            # Calculate completion time and log summary
            end_time = datetime.now()
            duration = end_time - start_time

            logger.info(f"🎯 Scheduled refresh completed in {duration.total_seconds():.1f} seconds")
            logger.info(f"📈 Success rate: {successful_refreshes}/{len(nse_symbols)} ({(successful_refreshes/len(nse_symbols)*100):.1f}%)")

            if failed_symbols:
                logger.warning(f"⚠️ Failed symbols: {[fs['symbol'] for fs in failed_symbols[:5]]}")  # Log first 5 failed symbols

        except Exception as e:
            logger.error(f"❌ Error in scheduled option data refresh: {e}")

    def _get_nse_symbols(self) -> List[str]:
        """
        Get all NSE symbols from FNO symbols data

        Returns:
            List of NSE symbol strings
        """
        try:
            if hasattr(self.dhan_service, 'fno_symbols') and 'NSE' in self.dhan_service.fno_symbols:
                symbols = [stock['SYMBOL'] for stock in self.dhan_service.fno_symbols['NSE']]
                logger.info(f"📋 Found {len(symbols)} NSE symbols for refresh")
                return symbols
            else:
                logger.warning("⚠️ No NSE symbols found in dhan_service.fno_symbols")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting NSE symbols: {e}")
            return []

    def start_scheduler(self):
        """Start the scheduler with 15-minute interval"""
        try:
            if self.is_running:
                logger.warning("⚠️ Scheduler is already running")
                return

            # Add the job to run every 15 minutes
            self.scheduler.add_job(
                func=self.refresh_all_symbols_option_data,
                trigger=IntervalTrigger(minutes=15),
                id='refresh_option_data',
                name='Refresh Option Chain Data',
                replace_existing=True
            )

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("🚀 Dhan Scheduler started - will refresh option data every 15 minutes")

            # Run immediately on startup
            asyncio.create_task(self.refresh_all_symbols_option_data())

        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {e}")

    def stop_scheduler(self):
        """Stop the scheduler"""
        try:
            if not self.is_running:
                logger.warning("⚠️ Scheduler is not running")
                return

            self.scheduler.shutdown()
            self.is_running = False
            logger.info("🛑 Dhan Scheduler stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping scheduler: {e}")

    def get_scheduler_status(self) -> dict:
        """
        Get current scheduler status and job information

        Returns:
            Dictionary with scheduler status
        """
        try:
            jobs = self.scheduler.get_jobs()
            next_run = None

            if jobs:
                next_run = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None

            return {
                "is_running": self.is_running,
                "job_count": len(jobs),
                "next_run_time": next_run,
                "interval_minutes": 15,
                "exchange": self.exchange,
                "expiry": self.expiry,
                "scheduler_state": "running" if self.is_running else "stopped"
            }

        except Exception as e:
            logger.error(f"❌ Error getting scheduler status: {e}")
            return {
                "is_running": False,
                "error": str(e)
            }

# Global scheduler instance
dhan_scheduler = DhanScheduler()
