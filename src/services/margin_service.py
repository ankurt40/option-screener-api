"""
Margin Service

Service for calculating margin requirements using AlgoTest API.
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MarginService:
    def __init__(self):
        self.base_url = "https://api.algotest.in/marginCalcAPI"
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en,en-US;q=0.9,en-GB;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://algotest.in',
            'Referer': 'https://algotest.in/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        self.cookies = '_gcl_au=1.1.1778817818.1755944627; _gid=GA1.2.1434533082.1755944627; ajs_anonymous_id=3ffef8e5-cb5a-4eb3-b199-dd217319de97; _fbp=fb.1.1755944628427.184085054680740094; mp_f7c3d9535820295f2d256c66e7c13599_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A198d674a899982-0399ad451466068-7e433c49-1fa400-198d674a899982%22%2C%22%24device_id%22%3A%20%22198d674a899982-0399ad451466068-7e433c49-1fa400-198d674a899982%22%2C%22%24search_engine%22%3A%20%22google%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.google.com%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%7D; _ga=GA1.2.698989224.1755944627; _ga_Y0EK98JRBT=GS2.1.s1755944626$o1$g1$t1755945141$j60$l0$h0'

    async def calculate_margin(
        self,
        positions: List[Dict[str, Any]],
        index_prices: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate margin requirements for a list of positions

        Args:
            positions: List of position dictionaries with keys:
                - Ticker: Stock symbol (e.g., "ABCAPITAL")
                - Expiry: Expiry date in DD-MMM-YY format (e.g., "25-Sep-25")
                - Strike: Strike price (e.g., 280)
                - InstrumentType: Option type "CE" or "PE"
                - NetQty: Net quantity (negative for short positions)
            index_prices: Optional dictionary of index prices

        Returns:
            Dictionary containing margin calculation results
        """
        try:
            # Prepare request payload
            payload = {
                "IndexPrices": index_prices or {},
                "ListOfPosition": positions
            }

            logger.info(f"🔢 Calculating margin for {len(positions)} positions")
            logger.debug(f"📊 Payload: {payload}")

            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/calculate_margin",
                    headers=self.headers,
                    cookies=self._parse_cookies(self.cookies),
                    json=payload
                )

                logger.info(f"📥 Margin API response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Successfully calculated margin")
                    logger.debug(f"📊 Margin result: {data}")
                    return data
                else:
                    error_msg = f"AlgoTest Margin API error {response.status_code}: {response.text}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)

        except Exception as e:
            logger.error(f"❌ Error calculating margin: {e}")
            raise Exception(f"Failed to calculate margin: {str(e)}")

    async def calculate_margin_for_strikes(
        self,
        strikes: List[Dict[str, Any]],
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate margin for option strikes with standardized format

        Args:
            strikes: List of strike dictionaries with keys:
                - symbol: Stock symbol
                - strikePrice: Strike price
                - expiryDate: Expiry date (will be converted to DD-MMM-YY format)
                - type: Option type "CE" or "PE"
            quantity: Net quantity (use negative for short positions)

        Returns:
            Dictionary containing margin calculation results
        """
        try:
            positions = []

            for strike in strikes:
                # Convert expiry date format from DD-MMM-YYYY to DD-MMM-YY
                expiry_date = self._convert_expiry_format(strike.get('expiryDate', ''))

                position = {
                    "Ticker": strike.get('symbol', '').upper(),
                    "Expiry": expiry_date,
                    "Strike": float(strike.get('strikePrice', 0)),
                    "InstrumentType": strike.get('type', 'CE'),
                    "NetQty": quantity
                }
                positions.append(position)

            return await self.calculate_margin(positions)

        except Exception as e:
            logger.error(f"❌ Error calculating margin for strikes: {e}")
            raise Exception(f"Failed to calculate margin for strikes: {str(e)}")

    def _convert_expiry_format(self, expiry_date: str) -> str:
        """
        Convert expiry date from DD-MMM-YYYY to DD-MMM-YY format

        Args:
            expiry_date: Date in DD-MMM-YYYY format (e.g., "25-Sep-2025")

        Returns:
            Date in DD-MMM-YY format (e.g., "25-Sep-25")
        """
        try:
            if not expiry_date or len(expiry_date) < 10:
                return expiry_date

            # Parse the date and convert to required format
            date_obj = datetime.strptime(expiry_date, "%d-%b-%Y")
            return date_obj.strftime("%d-%b-%y")
        except ValueError:
            logger.warning(f"⚠️ Invalid expiry date format: {expiry_date}")
            return expiry_date

    def _parse_cookies(self, cookie_string: str) -> Dict[str, str]:
        """
        Parse cookie string into dictionary

        Args:
            cookie_string: Raw cookie string

        Returns:
            Dictionary of cookie key-value pairs
        """
        cookies = {}
        if cookie_string:
            for cookie in cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key] = value
        return cookies

    async def calculate_single_position_margin(
        self,
        ticker: str,
        expiry: str,
        strike: float,
        instrument_type: str,
        net_qty: int,
        index_prices: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate margin for a single position

        Args:
            ticker: Stock symbol (e.g., "ABCAPITAL")
            expiry: Expiry date in DD-MMM-YY format (e.g., "25-Sep-25")
            strike: Strike price
            instrument_type: Option type "CE" or "PE"
            net_qty: Net quantity (negative for short positions)
            index_prices: Optional dictionary of index prices

        Returns:
            Dictionary containing margin calculation results
        """
        position = {
            "Ticker": ticker.upper(),
            "Expiry": expiry,
            "Strike": float(strike),
            "InstrumentType": instrument_type,
            "NetQty": net_qty
        }

        return await self.calculate_margin([position], index_prices)

# Create a global instance
margin_service = MarginService()
