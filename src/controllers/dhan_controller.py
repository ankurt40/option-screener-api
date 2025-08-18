import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from services.dhan_service import DhanService
from models.option_models import Strike
from services.cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dhan", tags=["Dhan API"])

# Initialize Dhan service
dhan_service = DhanService()

async def _parse_dhan_response_to_strikes(dhan_response: dict, symbol: str, expiry: Optional[str] = None) -> List[Strike]:
    """
    Parse Dhan API response and convert to list of Strike objects
    """
    strikes = []

    try:
        # Use provided expiry or default
        expiry_date = expiry if expiry else "2025-08-28"

        # Convert expiry format if needed (from YYYY-MM-DD to DD-MMM-YYYY)
        formatted_expiry = expiry_date
        if expiry and len(expiry) == 10 and expiry.count('-') == 2:
            from datetime import datetime
            try:
                date_obj = datetime.strptime(expiry, "%Y-%m-%d")
                formatted_expiry = date_obj.strftime("%d-%b-%Y")
            except ValueError:
                formatted_expiry = expiry_date

        # Fetch lot size for the symbol
        from services.nse_service import nse_service
        lot_size = await nse_service.get_fno_lot_size(symbol)
        logger.info(f"📦 Fetched lot size for {symbol}: {lot_size}")

        # Get underlying value from response
        underlying_value = 0
        if 'data' in dhan_response and 'last_price' in dhan_response['data']:
            underlying_value = float(dhan_response['data']['last_price'])
            logger.info(f"🔍 Found underlying value: {underlying_value}")

        # Parse option chain data from Dhan format
        if 'data' in dhan_response and 'oc' in dhan_response['data']:
            option_chain = dhan_response['data']['oc']
            logger.info(f"🔍 Found option chain with {len(option_chain)} strike prices")

            for strike_price_str, strike_data in option_chain.items():
                try:
                    strike_price = float(strike_price_str)

                    # Process CE (Call) options
                    if 'ce' in strike_data and strike_data['ce']:
                        ce_data = strike_data['ce']
                        ce_strike = Strike(
                            strikePrice=strike_price,
                            expiryDate=formatted_expiry,
                            underlying=symbol.upper(),
                            identifier=f"OPTSCE{symbol.upper()}{formatted_expiry.replace('-', '')}CE{strike_price}",
                            openInterest=int(ce_data.get('oi', 0)),
                            changeinOpenInterest=int(ce_data.get('oi', 0) - ce_data.get('previous_oi', 0)),
                            pchangeinOpenInterest=0.0,  # Calculate if needed
                            totalTradedVolume=int(ce_data.get('volume', 0)),
                            impliedVolatility=float(ce_data.get('implied_volatility', 0)),
                            lastPrice=float(ce_data.get('last_price', 0)),
                            change=0.0,  # Calculate if needed
                            pChange=0.0,  # Calculate if needed
                            totalBuyQuantity=0,  # Not available in Dhan response
                            totalSellQuantity=0,  # Not available in Dhan response
                            bidQty=int(ce_data.get('top_bid_quantity', 0)),
                            bidprice=float(ce_data.get('top_bid_price', 0)),
                            askQty=int(ce_data.get('top_ask_quantity', 0)),
                            askPrice=float(ce_data.get('top_ask_price', 0)),
                            underlyingValue=underlying_value,
                            type="CE",
                            # Add lot size
                            lotSize=lot_size,
                            # Initialize analytics fields - will be calculated later
                            strikeGap=None,
                            strikeGapPercentage=None,
                            premiumPercentage=None
                        )
                        strikes.append(ce_strike)

                    # Process PE (Put) options
                    if 'pe' in strike_data and strike_data['pe']:
                        pe_data = strike_data['pe']
                        pe_strike = Strike(
                            strikePrice=strike_price,
                            expiryDate=formatted_expiry,
                            underlying=symbol.upper(),
                            identifier=f"OPTSPE{symbol.upper()}{formatted_expiry.replace('-', '')}PE{strike_price}",
                            openInterest=int(pe_data.get('oi', 0)),
                            changeinOpenInterest=int(pe_data.get('oi', 0) - pe_data.get('previous_oi', 0)),
                            pchangeinOpenInterest=0.0,  # Calculate if needed
                            totalTradedVolume=int(pe_data.get('volume', 0)),
                            impliedVolatility=float(pe_data.get('implied_volatility', 0)),
                            lastPrice=float(pe_data.get('last_price', 0)),
                            change=0.0,  # Calculate if needed
                            pChange=0.0,  # Calculate if needed
                            totalBuyQuantity=0,  # Not available in Dhan response
                            totalSellQuantity=0,  # Not available in Dhan response
                            bidQty=int(pe_data.get('top_bid_quantity', 0)),
                            bidprice=float(pe_data.get('top_bid_price', 0)),
                            askQty=int(pe_data.get('top_ask_quantity', 0)),
                            askPrice=float(pe_data.get('top_ask_price', 0)),
                            underlyingValue=underlying_value,
                            type="PE",
                            # Add lot size
                            lotSize=lot_size,
                            # Initialize analytics fields - will be calculated later
                            strikeGap=None,
                            strikeGapPercentage=None,
                            premiumPercentage=None
                        )
                        strikes.append(pe_strike)

                except ValueError as ve:
                    logger.warning(f"⚠️ Skipping invalid strike price: {strike_price_str} - {ve}")
                    continue
        else:
            logger.warning(f"⚠️ No option chain data found in Dhan response")

        logger.info(f"📊 Parsed {len(strikes)} strikes from Dhan response for {symbol} with lot size: {lot_size}")
        return strikes

    except Exception as e:
        logger.error(f"❌ Error parsing Dhan response to strikes: {e}")
        return []

@router.post("/option-chain")
async def get_option_chain(
    underlying_scrip: int,
    underlying_seg: str = "NSE_FNO",
    expiry: Optional[str] = None
) -> List[Strike]:
    """
    Get option chain data from Dhan API using security ID

    Args:
        underlying_scrip: Security ID of the underlying asset
        underlying_seg: Segment (NSE_FNO, BSE_FNO)
        expiry: Expiry date in YYYY-MM-DD format (optional)
    """
    try:
        logger.info(f"🎯 Dhan option chain request for scrip: {underlying_scrip}")

        option_chain = await dhan_service.get_option_chain(
            underlying_scrip=str(underlying_scrip),
            underlying_seg=underlying_seg,
            expiry=expiry
        )

        # Convert to strikes with dynamic expiry
        strikes = await _parse_dhan_response_to_strikes(option_chain, f"SCRIP_{underlying_scrip}", expiry)

        # Calculate additional analytics for all strikes before returning
        strikes_with_analytics = dhan_service._calculate_strike_analytics(strikes)

        logger.info(f"✅ Successfully fetched {len(strikes_with_analytics)} strikes with analytics from Dhan for scrip: {underlying_scrip}")
        return strikes_with_analytics

    except Exception as e:
        logger.error(f"❌ Error in Dhan option chain endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/option-chain-by-symbol")
async def get_option_chain_by_symbol(
    symbol: str = Query(..., description="Symbol name (e.g., RELIANCE)"),
    exchange: str = Query("NSE", description="Exchange (NSE or BSE)"),
    expiry: Optional[str] = Query(None, description="Expiry date in YYYY-MM-DD format")
) -> List[Strike]:
    """
    Get option chain data from Dhan API using symbol name

    Args:
        symbol: Symbol name (e.g., RELIANCE)
        exchange: Exchange (NSE or BSE)
        expiry: Expiry date in YYYY-MM-DD format (optional)
    """
    try:
        logger.info(f"🎯 Dhan option chain request for symbol: {symbol} on {exchange}")

        # Use the new centralized method that handles everything
        strikes_with_analytics = await dhan_service.get_option_chain_with_analytics_by_symbol(
            symbol=symbol,
            exchange=exchange,
            expiry=expiry
        )

       # logger.info(f"✅ Successfully fetched {len(strikes_with_analytics)} strikes with analytics from Dhan for symbol: {symbol}")
        return strikes_with_analytics

    except Exception as e:
        logger.error(f"❌ Error in Dhan option chain by symbol endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_fno_symbols():
    """
    Get all available FNO symbols grouped by exchange
    """
    try:
        logger.info("📋 Fetching FNO symbols from Dhan service")
        return dhan_service.fno_symbols

    except Exception as e:
        logger.error(f"❌ Error fetching FNO symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbol-lookup")
async def lookup_symbol(
    symbol: str = Query(..., description="Symbol to lookup"),
    exchange: str = Query("NSE", description="Exchange (NSE or BSE)")
):
    """
    Lookup security ID for a given symbol
    """
    try:
        logger.info(f"🔍 Looking up symbol: {symbol} on {exchange}")

        security_id = dhan_service.get_security_id_by_symbol(symbol, exchange)

        if security_id:
            return {
                "symbol": symbol.upper(),
                "exchange": exchange.upper(),
                "security_id": security_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found on {exchange}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in symbol lookup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/info")
async def get_cache_info():
    """
    Get cache information for Dhan service
    """
    try:
        cache_info = dhan_service.get_cache_info()
        return {
            "cache_entries": len(cache_info),
            "details": cache_info
        }
    except Exception as e:
        logger.error(f"❌ Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache")
async def clear_cache():
    """
    Clear Dhan service cache
    """
    try:
        dhan_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_full_option_chain")
async def get_full_option_chain() -> Dict[str, Any]:
    """
    Get full option chain data for all NSE symbols for 2025-08-28 from cache only

    Returns:
        Dictionary containing option chain data for all cached symbols
    """
    try:
        logger.info("🎯 Full option chain request for all NSE symbols (2025-08-28) - CACHE ONLY")



        # Fixed expiry date
        expiry_date = "2025-08-28"

        # Get all FNO symbols for NSE
        nse_symbols = []
        if hasattr(dhan_service, 'fno_symbols') and 'NSE' in dhan_service.fno_symbols:
            nse_symbols = [stock['SYMBOL'] for stock in dhan_service.fno_symbols['NSE']]

        logger.info(f"📊 Found {len(nse_symbols)} NSE symbols to check in cache")

        # Collect cached data for all symbols
        cached_data = {}
        cache_hits = 0
        cache_misses = 0

        for symbol in nse_symbols:
            cache_key = f"{symbol.upper()}_{expiry_date}"
            cached_strikes = cache_service.get(cache_key)

            if cached_strikes:
                cache_hits += 1
                cached_data[symbol] = {
                    "symbol": symbol,
                    "expiry_date": expiry_date,
                    "strikes": cached_strikes,
                    "strike_count": len(cached_strikes)
                }
                logger.debug(f"📦 Cache hit for {symbol}: {len(cached_strikes)} strikes")
            else:
                cache_misses += 1
                logger.debug(f"📭 Cache miss for {symbol}")

        # Prepare response
        response_data = {
            "success": True,
            "message": f"Full option chain data retrieved from cache for {cache_hits} symbols",
            "expiry_date": expiry_date,
            "total_symbols_checked": len(nse_symbols),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "symbols_with_data": list(cached_data.keys()),
            "data": cached_data,
            "cache_hit_rate": round((cache_hits / len(nse_symbols) * 100), 2) if nse_symbols else 0,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ Full option chain request completed: {cache_hits}/{len(nse_symbols)} symbols found in cache")
        logger.info(f"📈 Cache hit rate: {response_data['cache_hit_rate']}%")

        return response_data

    except Exception as e:
        logger.error(f"❌ Error in get_full_option_chain endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
