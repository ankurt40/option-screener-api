import httpx
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from nse import NSE

from services.cache_service import cache_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSEService:
    """Service class to handle NSE API interactions with global caching"""

    def __init__(self):
        self.session: Optional[httpx.AsyncClient] = None
        self.cookies: Dict[str, str] = {}
        self.base_url = "https://www.nseindia.com"
        # Initialize NSE client with download folder
        self.nse_client = NSE(download_folder='/tmp')

    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data for symbol is still valid"""
        return cache_service.exists(symbol)

    def _get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached data for symbol if valid"""
        cached_data = cache_service.get(symbol)
        if cached_data:
            logger.info(f"🎯 Using cached data for {symbol}")
        return cached_data

    def _store_in_cache(self, symbol: str, data: Dict[str, Any]) -> None:
        """Store data in cache with current timestamp"""
        cache_service.set(symbol, data, ttl_minutes=60)
        logger.info(f"💾 Cached data for {symbol} (expires in 60 minutes)")

    async def get_session(self) -> httpx.AsyncClient:
        """Initialize session with NSE website to get cookies"""
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

            # Get initial cookies by visiting NSE homepage
            try:
                ##  logger.info("🔄 Establishing session with NSE...")
                response = await self.session.get(self.base_url)
                if response.status_code == 200:
                    self.cookies.update(dict(response.cookies))
                    logger.info(f"✅ Session established with NSE, got {len(self.cookies)} cookies")
                else:
                    logger.warning(f"⚠️ Failed to establish session: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error establishing session: {e}")

        return self.session

    async def fetch_option_chain(self, symbol: str) -> Dict[str, Any]:
        """Fetch option chain data from NSE using nse library with caching"""
        logger.info(f"🔄 Fetching option chain for symbol: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            return cached_data

        logger.info(f"📡 Cache miss for {symbol}, fetching from NSE using nse library...")

        try:
            # Use the correct method name from NSE library
            option_chain_data = self.nse_client.optionChain(symbol.upper())

            # Add delay to prevent rate limiting
            await asyncio.sleep(2)

            if option_chain_data:
                logger.info(f"✅ Successfully fetched option chain for {symbol} using nse library")
                # Store in cache
                self._store_in_cache(symbol, option_chain_data)
                return option_chain_data
            else:
                logger.error(f"❌ No option chain data returned from nse library for {symbol}")
                raise Exception(f"No option chain data available for {symbol}")

        except Exception as e:
            logger.error(f"❌ Exception fetching option chain for {symbol} using nse library: {e}")
            raise Exception(f"Failed to fetch option chain for {symbol}: {str(e)}")

    async def list_fno_stocks(self) -> Dict[str, Any]:
        """Fetch list of F&O (Futures and Options) stocks from NSE using nse library"""
        logger.info("🔄 Fetching F&O stocks list from NSE using nse library")

        # Check cache first (using 'FNO_STOCKS' as cache key)
        cached_data = self._get_cached_data('FNO_STOCKS')
        if cached_data:
            return cached_data

        logger.info("📡 Cache miss for F&O stocks, fetching from NSE using nse library...")

        try:
            # Use the correct method to fetch F&O stocks
            # The listFnoStocks() method is deprecated, use listEquityStocksByIndex instead
            fno_data = self.nse_client.listEquityStocksByIndex(index='SECURITIES IN F&O')

            if fno_data and 'data' in fno_data:
                logger.info("✅ Successfully fetched F&O stocks using nse library")

                # Transform the data to our expected format
                stocks_list = fno_data['data']
                formatted_data = {
                    "data": stocks_list,
                    "total": len(stocks_list),
                    "message": "F&O stocks list retrieved successfully using nse library"
                }

                # Store in cache
                self._store_in_cache('FNO_STOCKS', formatted_data)
                return formatted_data
            else:
                logger.error("❌ No F&O stocks data returned from nse library")
                raise Exception("No F&O stocks data available")

        except Exception as e:
            logger.error(f"❌ Exception fetching F&O stocks using nse library: {e}")
            raise Exception(f"Failed to fetch F&O stocks: {str(e)}")

    async def _reset_session(self):
        """Reset the session and cookies - kept for backward compatibility"""
        if self.session:
            await self.session.aclose()
        self.session = None
        self.cookies = {}

    # Note: The _retry_fetch_option_chain method is no longer needed since we use nse library
    # Keeping the method signature for backward compatibility but redirecting to main method
    async def _retry_fetch_option_chain(self, symbol: str, api_url: str = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Legacy retry method - now redirects to main fetch_option_chain method"""
        logger.info(f"🔄 Legacy retry called for {symbol}, using nse library method...")
        return await self.fetch_option_chain(symbol)

    async def close_session(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            logger.info("🔒 NSE session closed")

# Global NSE service instance
nse_service = NSEService()
