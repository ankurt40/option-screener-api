from typing import List, Dict, Any
import logging
import asyncio

from models.option_models import Strike
from services.nse_service import nse_service

# Set up logging
logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service class to handle analytics operations and option data processing"""

    def __init__(self):
        self.nse_service = nse_service

    async def get_volatile_options(self, symbol: str) -> List[Strike]:
        """
        Fetch and process option chain data to return volatile options sorted by implied volatility

        Args:
            symbol: Stock symbol to analyze

        Returns:
            List of Strike objects sorted by implied volatility (descending)

        Raises:
            ValueError: If option chain data cannot be fetched or processed
        """
        logger.info(f"🔄 Processing volatile options analysis for: {symbol}")

        # Fetch option chain data from NSE service
        option_data = await self.nse_service.fetch_option_chain(symbol)

        if not option_data or "records" not in option_data:
            raise ValueError("Failed to fetch option chain data from NSE")

        # Parse the option chain response into Strike objects
        strikes = self._parse_option_chain_to_strikes(option_data, symbol)

        # Sort by implied volatility in descending order to get most volatile options first
        strikes.sort(key=lambda x: x.impliedVolatility, reverse=True)

        logger.info(f"✅ Volatile options analysis completed for {symbol}. Found {len(strikes)} strike options")

        return strikes

    async def get_volatile_options_for_all_stocks(self) -> List[Strike]:
        """
        Fetch and process option chain data for all F&O stocks to return volatile options

        This function:
        - Retrieves all F&O stocks from cache
        - Analyzes option chains for each symbol with 2-second delay only when fetching fresh data
        - Returns combined list of Strike objects
        - Logs analytics data internally

        Returns:
            List of Strike objects sorted by implied volatility (descending)

        Raises:
            ValueError: If F&O stocks cannot be fetched or no stocks found
        """
        logger.info("🎯 All symbols volatile options analysis request received")

        # Get all F&O stocks from cache
        try:
            fno_stocks_data = await self.nse_service.list_fno_stocks()
            fno_stocks = fno_stocks_data.get("data", [])

            if not fno_stocks:
                raise ValueError("No F&O stocks found in cache")

            logger.info(f"📊 Found {len(fno_stocks)} F&O stocks to analyze")

        except Exception as e:
            logger.error(f"❌ Failed to fetch F&O stocks: {str(e)}")
            raise ValueError(f"Failed to fetch F&O stocks list: {str(e)}")

        # Collect all strikes from all symbols
        all_strikes = []
        successful_symbols = []
        failed_symbols = []
        cache_hits = 0
        api_calls = 0

        for i, stock in enumerate(fno_stocks):
            symbol = stock.get("symbol", "").upper().strip()

            if not symbol:
                continue

            try:
                logger.info(f"🔄 Processing {i+1}/{len(fno_stocks)}: {symbol}")

                # Check if data is in cache before making the call
                is_cached = self.nse_service._is_cache_valid(symbol)

                if is_cached:
                    cache_hits += 1
                    logger.info(f"🎯 Using cached data for {symbol} (no delay needed)")
                else:
                    api_calls += 1
                    logger.info(f"📡 Cache miss for {symbol}, will fetch from NSE")

                # Get volatile options for this symbol
                strikes = await self.get_volatile_options(symbol)
                all_strikes.extend(strikes)
                successful_symbols.append(symbol)

                logger.info(f"✅ Successfully processed {symbol}: {len(strikes)} strikes")

                # Add 2-second delay only if we made an actual API call (cache miss)
                # and it's not the last symbol
                if not is_cached and i < len(fno_stocks) - 1:
                    logger.info(f"⏱️ Adding 2-second delay after API call for {symbol}")
                    await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ Failed to process {symbol}: {str(e)}")
                failed_symbols.append({"symbol": symbol, "error": str(e)})
                continue

        # Sort all strikes by implied volatility in descending order
        all_strikes.sort(key=lambda x: x.impliedVolatility, reverse=True)

        # Log summary with cache performance and analytics data
        logger.info(f"🎯 Analysis completed: {len(successful_symbols)} successful, {len(failed_symbols)} failed")
        logger.info(f"📈 Total strikes found: {len(all_strikes)}")
        logger.info(f"🎯 Cache performance: {cache_hits} hits, {api_calls} API calls")

        # Log detailed analytics data
        analytics_data = {
            "total_symbols_processed": len(successful_symbols),
            "failed_symbols": failed_symbols,
            "cache_hits": cache_hits,
            "api_calls": api_calls,
            "total_strikes": len(all_strikes),
            "successful_symbols": successful_symbols
        }
        logger.info(f"📊 Analytics Data: {analytics_data}")

        return all_strikes

    def _parse_option_chain_to_strikes(self, option_data: Dict[str, Any], symbol: str) -> List[Strike]:
        """
        Parse NSE option chain response into Strike objects

        Args:
            option_data: Raw option chain data from NSE API
            symbol: Stock symbol

        Returns:
            List of Strike objects containing both CE and PE options
        """
        strikes = []
        records = option_data["records"]
        underlying_value = records.get("underlyingValue", 0)

        for option_strike in records.get("data", []):
            strike_price = option_strike.get("strikePrice", 0)
            expiry_date = option_strike.get("expiryDate", "")

            # Process CE (Call) options
            if "CE" in option_strike and option_strike["CE"]:
                ce_data = option_strike["CE"]
                ce_strike = self._create_strike_object(
                    strike_price=strike_price,
                    expiry_date=expiry_date,
                    symbol=symbol,
                    option_data=ce_data,
                    underlying_value=underlying_value,
                    option_type="CE"
                )
                strikes.append(ce_strike)

            # Process PE (Put) options
            if "PE" in option_strike and option_strike["PE"]:
                pe_data = option_strike["PE"]
                pe_strike = self._create_strike_object(
                    strike_price=strike_price,
                    expiry_date=expiry_date,
                    symbol=symbol,
                    option_data=pe_data,
                    underlying_value=underlying_value,
                    option_type="PE"
                )
                strikes.append(pe_strike)

        return strikes

    def _create_strike_object(
        self,
        strike_price: float,
        expiry_date: str,
        symbol: str,
        option_data: Dict[str, Any],
        underlying_value: float,
        option_type: str
    ) -> Strike:
        """
        Create a Strike object from option data

        Args:
            strike_price: Strike price of the option
            expiry_date: Expiry date of the option
            symbol: Stock symbol
            option_data: Option specific data (CE or PE)
            underlying_value: Current price of underlying asset
            option_type: "CE" for Call or "PE" for Put

        Returns:
            Strike object with all required attributes
        """
        return Strike(
            strikePrice=strike_price,
            expiryDate=expiry_date,
            underlying=symbol,
            identifier=f"OPTSTK{symbol}{expiry_date}{option_type}{strike_price:.2f}",
            openInterest=option_data.get("openInterest", 0),
            changeinOpenInterest=option_data.get("changeinOpenInterest", 0),
            pchangeinOpenInterest=option_data.get("pchangeinOpenInterest", 0.0),
            totalTradedVolume=option_data.get("totalTradedVolume", 0),
            impliedVolatility=option_data.get("impliedVolatility", 0.0),
            lastPrice=option_data.get("lastPrice", 0.0),
            change=option_data.get("change", 0.0),
            pChange=option_data.get("pChange", 0.0),
            totalBuyQuantity=option_data.get("totalBuyQuantity", 0),
            totalSellQuantity=option_data.get("totalSellQuantity", 0),
            bidQty=option_data.get("bidQty", 0),
            bidprice=option_data.get("bidprice", 0.0),
            askQty=option_data.get("askQty", 0),
            askPrice=option_data.get("askPrice", 0.0),
            underlyingValue=underlying_value,
            type=option_type
        )

    def _calculate_strike_analytics(self, strikes: List[Strike]) -> List[Strike]:
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

            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate analytics for strike {strike.strikePrice}: {e}")
                # Set default values if calculation fails
                strike.strikeGap = 0.0
                strike.strikeGapPercentage = 0.0
                strike.premiumPercentage = 0.0

        logger.info(f"✅ Strike analytics calculated successfully for {len(strikes)} strikes")
        return strikes

# Create a singleton instance
analytics_service = AnalyticsService()
