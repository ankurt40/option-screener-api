import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DhanService:
    def __init__(self):
        self.base_url = "https://api.dhan.co/v2"
        self.access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU3MzI2MTU3LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwODA2NjUzMCJ9.YnPPDghUzQ7QORhK6DSflk12hNyJzydD59KnNHA6nFPmH8-3Tk20HkXXUTidMyvwdahOPoqL6XgnTMp2-ooQ0g"
        self.client_id = "1108066530"
        self.cache = {}
        self.cache_duration = timedelta(hours=1)

        # Load FNO symbols mapping
        self.load_fno_symbols()

    def load_fno_symbols(self):
        """Load FNO symbols from the JSON file"""
        try:
            with open('/Users/ankurtiwari/IdeaProjects/option-screener-api/src/data/fno-symbols-dhan.json', 'r') as f:
                self.fno_symbols = json.load(f)
            logger.info("✅ FNO symbols loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading FNO symbols: {e}")
            self.fno_symbols = {}

    def get_security_id_by_symbol(self, symbol: str, exchange: str = "NSE") -> Optional[str]:
        """Get security ID by symbol from the FNO symbols mapping"""
        try:
            exchange_key = "BSE" if exchange.upper() == "BSE" else "NSE"  # Use NSE as default

            if exchange_key in self.fno_symbols:
                for item in self.fno_symbols[exchange_key]:
                    if item["SYMBOL"].upper() == symbol.upper():
                        return item["SECURITY_ID"]

            logger.warning(f"⚠️ Symbol {symbol} not found in {exchange_key}")
            return None
        except Exception as e:
            logger.error(f"❌ Error finding security ID for {symbol}: {e}")
            return None

    def _get_cache_key(self, underlying_scrip: str, underlying_seg: str, expiry: str) -> str:
        """Generate cache key for option chain data"""
        return f"dhan_option_chain_{underlying_scrip}_{underlying_seg}_{expiry}"

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if 'timestamp' not in cache_entry:
            return False

        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        return datetime.now() - cache_time < self.cache_duration

    async def get_option_chain(self, underlying_scrip: str, underlying_seg: str = "NSE_FNO", expiry: str = None) -> Dict[str, Any]:
        """
        Fetch option chain from Dhan API

        Args:
            underlying_scrip: Security ID of the underlying asset
            underlying_seg: Segment (default: NSE_FNO)
            expiry: Expiry date in YYYY-MM-DD format
        """
        try:
            # Set default expiry if not provided (next Thursday)
            if not expiry:
                expiry = self._get_next_thursday().strftime("%Y-%m-%d")

            # Check cache first
            cache_key = self._get_cache_key(underlying_scrip, underlying_seg, expiry)
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
                logger.info(f"📦 Cache hit for Dhan option chain: {underlying_scrip}")
                return self.cache[cache_key]['data']

            logger.info(f"🔄 Fetching option chain from Dhan API for scrip: {underlying_scrip}")

            headers = {
                'access-token': self.access_token,
                'client-id': self.client_id,
                'content-type': 'application/json'
            }

            payload = {
                "UnderlyingScrip": int(underlying_scrip),
                "UnderlyingSeg": underlying_seg,
                "Expiry": expiry
            }

            # Log the request details
            logger.info(f"📤 Making POST request to: {self.base_url}/optionchain")
            logger.info(f"📤 Request headers: {dict(headers)}")
            logger.info(f"📤 Request payload: {payload}")

            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/optionchain",
                    headers=headers,
                    json=payload
                )

                # Log the response details
                logger.info(f"📥 Response status: {response.status_code}")
                logger.info(f"📥 Response headers: {dict(response.headers)}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"📥 Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

                    # Cache the response
                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }

                    logger.info(f"✅ Successfully fetched option chain for scrip: {underlying_scrip}")
                    return data
                else:
                    error_msg = f"Dhan API error {response.status_code}: {response.text}"
                    logger.error(f"❌ {error_msg}")
                    logger.error(f"📥 Response text: {response.text}")
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"❌ Error fetching option chain from Dhan: {e}")
            raise Exception(f"Failed to fetch option chain from Dhan: {str(e)}")

    async def get_option_chain_by_symbol(self, symbol: str, exchange: str = "NSE", expiry: str = None) -> Dict[str, Any]:
        """
        Fetch option chain by symbol name

        Args:
            symbol: Symbol name (e.g., RELIANCE)
            exchange: Exchange (NSE or BSE)
            expiry: Expiry date in YYYY-MM-DD format
        """
        try:
            # Get security ID from symbol
            security_id = self.get_security_id_by_symbol(symbol, exchange)
            if not security_id:
                raise Exception(f"Security ID not found for symbol: {symbol}")

            # Determine segment based on exchange
            underlying_seg = "BSE_FNO" if exchange.upper() == "BSE" else "NSE_FNO"

            return await self.get_option_chain(security_id, underlying_seg, expiry)

        except Exception as e:
            logger.error(f"❌ Error fetching option chain by symbol {symbol}: {e}")
            raise Exception(f"Failed to fetch option chain for {symbol}: {str(e)}")

    def _calculate_strike_analytics(self, strikes: List) -> List:
        """
        Calculate additional analytics for strikes list

        Calculates:
        - strike_gap = underlyingValue - strikePrice
        - strike_gap_percentage = (strike_gap / underlyingValue) * 100
        - premium_percentage = (lastPrice / underlyingValue) * 100

        Args:
            strikes: List of Strike objects to enhance with analytics

        Returns:
            List of Strike objects with analytics fields populated
        """
        logger.info(f"🔢 Calculating strike analytics for {len(strikes)} strikes")

        for strike in strikes:
            try:
                # Calculate strike gap (difference between underlying price and strike price)
                strike.strikeGap = strike.underlyingValue - strike.strikePrice

                # Calculate strike gap percentage
                if strike.underlyingValue > 0:
                    strike.strikeGapPercentage = (strike.strikeGap / strike.underlyingValue) * 100
                else:
                    strike.strikeGapPercentage = 0.0

                # Calculate premium percentage (option price as percentage of underlying)
                if strike.underlyingValue > 0:
                    strike.premiumPercentage = (strike.lastPrice / strike.underlyingValue) * 100
                else:
                    strike.premiumPercentage = 0.0

                logger.debug(f"📊 Strike {strike.strikePrice}: gap={strike.strikeGap:.2f}, gap%={strike.strikeGapPercentage:.2f}%, premium%={strike.premiumPercentage:.4f}%")

            except Exception as e:
                logger.warning(f"⚠️ Error calculating analytics for strike {strike.strikePrice}: {e}")
                # Set default values if calculation fails
                strike.strikeGap = 0.0
                strike.strikeGapPercentage = 0.0
                strike.premiumPercentage = 0.0

        logger.info(f"✅ Completed strike analytics calculation for {len(strikes)} strikes")
        return strikes

    def _get_next_thursday(self) -> datetime:
        """Get the next Thursday date for default expiry"""
        today = datetime.now()
        days_ahead = 3 - today.weekday()  # Thursday is 3
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days_ahead)

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("🗑️ Dhan service cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        cache_info = {}
        for key, entry in self.cache.items():
            cache_info[key] = {
                'timestamp': entry['timestamp'],
                'valid': self._is_cache_valid(entry),
                'size': len(str(entry['data']))
            }
        return cache_info
