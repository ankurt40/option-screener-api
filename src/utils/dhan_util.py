"""
Dhan Utility Functions

Utility functions for processing Dhan API responses and converting them to Strike objects.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.option_models import Strike
from services.nse_service import nse_service
logger = logging.getLogger(__name__)

async def parse_dhan_response_to_strikes(dhan_response: dict, symbol: str, expiry: Optional[str] = None) -> List[Strike]:
    """
    Parse Dhan API response and convert to list of Strike objects

    Args:
        dhan_response: Raw response from Dhan API
        symbol: Stock symbol
        expiry: Expiry date in YYYY-MM-DD format (optional)

    Returns:
        List of Strike objects containing both CE and PE options
    """
    strikes = []

    try:
        # Use provided expiry or default
        expiry_date = expiry if expiry else "2025-08-28"
        formatted_expiry = _format_expiry_date(expiry_date)

        # Fetch lot size for the symbol
        lot_size = await nse_service.get_fno_lot_size(symbol)
        logger.info(f"📦 Fetched lot size for {symbol}: {lot_size}")

        # Get underlying value from response
        underlying_value = _extract_underlying_value(dhan_response)

        # Parse option chain data from Dhan format
        option_chain = _extract_option_chain(dhan_response)
        if not option_chain:
            logger.warning(f"⚠️ No option chain data found in Dhan response for {symbol}")
            return strikes

        logger.info(f"🔍 Found option chain with {len(option_chain)} strike prices for {symbol}")

        for strike_price_str, strike_data in option_chain.items():
            try:
                strike_price = float(strike_price_str)

                # Process CE (Call) options
                if 'ce' in strike_data and strike_data['ce']:
                    ce_strike = _create_call_strike(
                        strike_price=strike_price,
                        formatted_expiry=formatted_expiry,
                        symbol=symbol,
                        ce_data=strike_data['ce'],
                        underlying_value=underlying_value,
                        lot_size=lot_size
                    )
                    strikes.append(ce_strike)

                # Process PE (Put) options
                if 'pe' in strike_data and strike_data['pe']:
                    pe_strike = _create_put_strike(
                        strike_price=strike_price,
                        formatted_expiry=formatted_expiry,
                        symbol=symbol,
                        pe_data=strike_data['pe'],
                        underlying_value=underlying_value,
                        lot_size=lot_size
                    )
                    strikes.append(pe_strike)

            except ValueError as ve:
                logger.warning(f"⚠️ Skipping invalid strike price: {strike_price_str} - {ve}")
                continue

        logger.info(f"📊 Parsed {len(strikes)} strikes from Dhan response for {symbol} with lot size: {lot_size}")
        return strikes

    except Exception as e:
        logger.error(f"❌ Error parsing Dhan response to strikes: {e}")
        return []

def _format_expiry_date(expiry: str) -> str:
    """
    Convert expiry format from YYYY-MM-DD to DD-MMM-YYYY if needed

    Args:
        expiry: Expiry date string

    Returns:
        Formatted expiry date string
    """
    if expiry and len(expiry) == 10 and expiry.count('-') == 2:
        try:
            date_obj = datetime.strptime(expiry, "%Y-%m-%d")
            return date_obj.strftime("%d-%b-%Y")
        except ValueError:
            logger.warning(f"⚠️ Invalid expiry date format: {expiry}")
            return expiry
    return expiry

def _extract_underlying_value(dhan_response: dict) -> float:
    """
    Extract underlying asset value from Dhan response

    Args:
        dhan_response: Raw response from Dhan API

    Returns:
        Underlying asset value (price)
    """
    underlying_value = 0.0
    if 'data' in dhan_response and 'last_price' in dhan_response['data']:
        underlying_value = float(dhan_response['data']['last_price'])
        ##logger.info(f"🔍 Found underlying value: {underlying_value}")
    return underlying_value

def _extract_option_chain(dhan_response: dict) -> Optional[Dict[str, Any]]:
    """
    Extract option chain data from Dhan response

    Args:
        dhan_response: Raw response from Dhan API

    Returns:
        Option chain dictionary or None if not found
    """
    if 'data' in dhan_response and 'oc' in dhan_response['data']:
        return dhan_response['data']['oc']
    return None

def _create_call_strike(
    strike_price: float,
    formatted_expiry: str,
    symbol: str,
    ce_data: Dict[str, Any],
    underlying_value: float,
    lot_size: int
) -> Strike:
    """
    Create a Strike object for Call (CE) option

    Args:
        strike_price: Strike price of the option
        formatted_expiry: Formatted expiry date
        symbol: Stock symbol
        ce_data: Call option data from Dhan response
        underlying_value: Current price of underlying asset
        lot_size: Lot size for the option

    Returns:
        Strike object for Call option
    """
    # Extract Greeks from ce_data
    greeks = ce_data.get('greeks', {})

    return Strike(
        strikePrice=strike_price,
        expiryDate=formatted_expiry,
        underlying=symbol.upper(),
        identifier=f"OPTSCE{symbol.upper()}{formatted_expiry.replace('-', '')}CE{strike_price}",
        openInterest=int(ce_data.get('oi', 0)),
        changeinOpenInterest=int(ce_data.get('oi', 0) - ce_data.get('previous_oi', 0)),
        pchangeinOpenInterest=0.0,
        totalTradedVolume=int(ce_data.get('volume', 0)),
        impliedVolatility=float(ce_data.get('implied_volatility', 0)),
        lastPrice=float(ce_data.get('last_price', 0)),
        change=0.0,
        pChange=0.0,
        totalBuyQuantity=0,
        totalSellQuantity=0,
        bidQty=int(ce_data.get('top_bid_quantity', 0)),
        bidprice=float(ce_data.get('top_bid_price', 0)),
        askQty=int(ce_data.get('top_ask_quantity', 0)),
        askPrice=float(ce_data.get('top_ask_price', 0)),
        underlyingValue=underlying_value,
        type="CE",
        # Greeks
        delta=float(greeks.get('delta', 0)) if greeks.get('delta') is not None else None,
        theta=float(greeks.get('theta', 0)) if greeks.get('theta') is not None else None,
        gamma=float(greeks.get('gamma', 0)) if greeks.get('gamma') is not None else None,
        vega=float(greeks.get('vega', 0)) if greeks.get('vega') is not None else None,
        # Lot size
        lotSize=lot_size,
        strikeGap=None,
        strikeGapPercentage=None,
        premiumPercentage=None
    )

def _create_put_strike(
    strike_price: float,
    formatted_expiry: str,
    symbol: str,
    pe_data: Dict[str, Any],
    underlying_value: float,
    lot_size: int
) -> Strike:
    """
    Create a Strike object for Put (PE) option

    Args:
        strike_price: Strike price of the option
        formatted_expiry: Formatted expiry date
        symbol: Stock symbol
        pe_data: Put option data from Dhan response
        underlying_value: Current price of underlying asset
        lot_size: Lot size for the option

    Returns:
        Strike object for Put option
    """
    # Extract Greeks from pe_data
    greeks = pe_data.get('greeks', {})

    return Strike(
        strikePrice=strike_price,
        expiryDate=formatted_expiry,
        underlying=symbol.upper(),
        identifier=f"OPTSPE{symbol.upper()}{formatted_expiry.replace('-', '')}PE{strike_price}",
        openInterest=int(pe_data.get('oi', 0)),
        changeinOpenInterest=int(pe_data.get('oi', 0) - pe_data.get('previous_oi', 0)),
        pchangeinOpenInterest=0.0,
        totalTradedVolume=int(pe_data.get('volume', 0)),
        impliedVolatility=float(pe_data.get('implied_volatility', 0)),
        lastPrice=float(pe_data.get('last_price', 0)),
        change=0.0,
        pChange=0.0,
        totalBuyQuantity=0,
        totalSellQuantity=0,
        bidQty=int(pe_data.get('top_bid_quantity', 0)),
        bidprice=float(pe_data.get('top_bid_price', 0)),
        askQty=int(pe_data.get('top_ask_quantity', 0)),
        askPrice=float(pe_data.get('top_ask_price', 0)),
        underlyingValue=underlying_value,
        type="PE",
        # Greeks
        delta=float(greeks.get('delta', 0)) if greeks.get('delta') is not None else None,
        theta=float(greeks.get('theta', 0)) if greeks.get('theta') is not None else None,
        gamma=float(greeks.get('gamma', 0)) if greeks.get('gamma') is not None else None,
        vega=float(greeks.get('vega', 0)) if greeks.get('vega') is not None else None,
        # Lot size
        lotSize=lot_size,
        strikeGap=None,
        strikeGapPercentage=None,
        premiumPercentage=None
    )
