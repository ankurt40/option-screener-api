from typing import List, Dict, Any
import logging

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

# Create a singleton instance
analytics_service = AnalyticsService()
