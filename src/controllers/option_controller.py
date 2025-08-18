"""
Option Controller using NSE service

FastAPI controller for NSE option chain data using the working NSE service.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Constants
SYMBOL_DESC = "Stock symbol"
EXPIRY_DESC = "Expiry date (YYYY-MM-DD format)"

router = APIRouter(
    prefix="/api/v1/options",
    tags=["Options"],
    responses={404: {"description": "Not found"}},
)

@router.get("/futures-expiry")
async def get_futures_expiry(symbol: str = Query(..., description=SYMBOL_DESC)):
    """
    Get futures expiry dates for a given symbol
    """
    try:
        logger.info(f"Fetching futures expiry for symbol: {symbol}")

        # Get option chain data using the working NSE service
        from services.nse_service import nse_service
        expiry_data = await nse_service.fetch_option_chain(symbol)

        if not expiry_data or "records" not in expiry_data:
            raise HTTPException(status_code=404, detail=f"No futures expiry data found for symbol: {symbol}")

        # Extract expiry dates from the response
        expiry_dates = []
        if "expiryDates" in expiry_data["records"]:
            expiry_dates = expiry_data["records"]["expiryDates"]

        return {
            "symbol": symbol,
            "expiry_dates": expiry_dates,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching futures expiry for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch futures expiry: {str(e)}")

@router.get("/fno-lots")
async def fno_lots(symbol: str = Query(..., description=SYMBOL_DESC)):
    """
    Get FNO lot size information for a given symbol
    """
    try:
        logger.info(f"Fetching FNO lot size for symbol: {symbol}")

        from services.nse_service import nse_service

        # Get lot size for the specific symbol
        lot_size = await nse_service.get_fno_lot_size(symbol)

        if lot_size is None:
            raise HTTPException(status_code=404, detail=f"No FNO lot data found for symbol: {symbol}")

        return {
            "symbol": symbol.upper(),
            "lotSize": lot_size,
            "instrumentType": "FNO"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching FNO lot size for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch FNO lot size: {str(e)}")


@router.get("/fno-lots-all")
async def fno_lots_all():
    """
    Get all FNO lot sizes for all symbols
    """
    try:
        logger.info("Fetching all FNO lot sizes")

        from services.nse_service import nse_service

        # Get all FNO lots data
        fno_lots_data = await nse_service.fetch_fno_lots()

        if not fno_lots_data:
            raise HTTPException(status_code=404, detail="No FNO lots data available")

        return {
            "data": fno_lots_data,
            "total": len(fno_lots_data),
            "status": "success",
            "message": f"Retrieved lot sizes for {len(fno_lots_data)} FNO symbols"
        }

    except Exception as e:
        logger.error(f"Error fetching all FNO lots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch FNO lots: {str(e)}")

@router.get("/option-chain")
async def option_chain(
    symbol: str = Query(..., description=SYMBOL_DESC),
    expiry: Optional[str] = Query(None, description=EXPIRY_DESC)
):
    """
    Get option chain data for a given symbol and expiry
    """
    try:
        logger.info(f"Fetching option chain for symbol: {symbol}, expiry: {expiry}")

        # Get option chain data using the working NSE service
        from nse import NSE
        nse = NSE(download_folder='/tmp')
        chain_data = nse.optionChain(symbol)

        if not chain_data:
            raise HTTPException(status_code=404, detail=f"No option chain data found for symbol: {symbol}")

        # Filter by expiry if provided
        if expiry and "records" in chain_data and "data" in chain_data["records"]:
            filtered_data = []
            for item in chain_data["records"]["data"]:
                if "expiryDate" in item and item["expiryDate"] == expiry:
                    filtered_data.append(item)
            chain_data["records"]["data"] = filtered_data

        return {
            "symbol": symbol,
            "expiry": expiry,
            "option_chain": chain_data,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching option chain for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch option chain: {str(e)}")

@router.get("/compile-option-chain")
async def compile_option_chain(
    symbol: str = Query(..., description=SYMBOL_DESC),
    expiry: Optional[str] = Query(None, description=EXPIRY_DESC)
):
    """
    Get compiled option chain data with additional calculations
    """
    try:
        logger.info(f"Compiling option chain for symbol: {symbol}, expiry: {expiry}")

        # Get option chain data using the working NSE service
        from ..services.nse_service import nse_service
        chain_data = await nse_service.fetch_option_chain(symbol)

        if not chain_data:
            raise HTTPException(status_code=404, detail=f"No option chain data found for symbol: {symbol}")

        # Filter by expiry if provided
        if expiry and "records" in chain_data and "data" in chain_data["records"]:
            filtered_data = []
            for item in chain_data["records"]["data"]:
                if "expiryDate" in item and item["expiryDate"] == expiry:
                    filtered_data.append(item)
            chain_data["records"]["data"] = filtered_data

        # Compile additional data
        compiled_data = _compile_option_data(chain_data)

        return {
            "symbol": symbol,
            "expiry": expiry,
            "compiled_option_chain": compiled_data,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error compiling option chain for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compile option chain: {str(e)}")

@router.get("/maxpain")
async def maxpain(
    symbol: str = Query(..., description=SYMBOL_DESC),
    expiry: Optional[str] = Query(None, description=EXPIRY_DESC)
):
    """
    Calculate max pain for a given symbol and expiry
    """
    try:
        logger.info(f"Calculating max pain for symbol: {symbol}, expiry: {expiry}")

        # Get option chain data using the working NSE service
        from nse import NSE
        nse = NSE(download_folder='/tmp')
        chain_data = nse.optionChain(symbol)

        if not chain_data:
            raise HTTPException(status_code=404, detail=f"No option chain data found for symbol: {symbol}")

        # Filter by expiry if provided
        if expiry and "records" in chain_data and "data" in chain_data["records"]:
            filtered_data = []
            for item in chain_data["records"]["data"]:
                if "expiryDate" in item and item["expiryDate"] == expiry:
                    filtered_data.append(item)
            chain_data["records"]["data"] = filtered_data

        # Calculate max pain
        max_pain_value = _calculate_max_pain(chain_data)

        return {
            "symbol": symbol,
            "expiry": expiry,
            "max_pain": max_pain_value,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error calculating max pain for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate max pain: {str(e)}")

def _compile_option_data(chain_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compile additional calculations from option chain data
    """
    try:
        compiled = {
            "total_call_oi": 0,
            "total_put_oi": 0,
            "total_call_volume": 0,
            "total_put_volume": 0,
            "pcr_oi": 0.0,
            "pcr_volume": 0.0,
            "strikes": []
        }

        if "records" in chain_data and "data" in chain_data["records"]:
            data = chain_data["records"]["data"]

            for strike_data in data:
                if "CE" in strike_data:
                    ce_data = strike_data["CE"]
                    compiled["total_call_oi"] += ce_data.get("openInterest", 0)
                    compiled["total_call_volume"] += ce_data.get("totalTradedVolume", 0)

                if "PE" in strike_data:
                    pe_data = strike_data["PE"]
                    compiled["total_put_oi"] += pe_data.get("openInterest", 0)
                    compiled["total_put_volume"] += pe_data.get("totalTradedVolume", 0)

                compiled["strikes"].append({
                    "strike": strike_data.get("strikePrice", 0),
                    "ce_oi": strike_data.get("CE", {}).get("openInterest", 0),
                    "pe_oi": strike_data.get("PE", {}).get("openInterest", 0),
                    "ce_volume": strike_data.get("CE", {}).get("totalTradedVolume", 0),
                    "pe_volume": strike_data.get("PE", {}).get("totalTradedVolume", 0)
                })

            # Calculate PCR ratios
            if compiled["total_call_oi"] > 0:
                compiled["pcr_oi"] = float(compiled["total_put_oi"]) / float(compiled["total_call_oi"])

            if compiled["total_call_volume"] > 0:
                compiled["pcr_volume"] = float(compiled["total_put_volume"]) / float(compiled["total_call_volume"])

        return compiled

    except Exception as e:
        logger.error(f"Error compiling option data: {str(e)}")
        return {}

def _calculate_max_pain(chain_data: Dict[str, Any]) -> float:
    """
    Calculate max pain point from option chain data
    """
    try:
        if "records" not in chain_data or "data" not in chain_data["records"]:
            return 0.0

        data = chain_data["records"]["data"]

        # Get all strike prices
        strikes = [strike_data.get("strikePrice", 0) for strike_data in data if "strikePrice" in strike_data]
        strikes.sort()

        if not strikes:
            return 0.0

        # Calculate pain at each strike
        max_pain_values = {}
        for test_strike in strikes:
            total_pain = _calculate_pain_at_strike(data, test_strike)
            max_pain_values[test_strike] = total_pain

        # Find strike with minimum pain
        if max_pain_values:
            max_pain_strike = min(max_pain_values.keys(), key=lambda k: max_pain_values[k])
            return float(max_pain_strike)

        return 0.0

    except Exception as e:
        logger.error(f"Error calculating max pain: {str(e)}")
        return 0.0

def _calculate_pain_at_strike(data: list, test_strike: float) -> float:
    """
    Calculate total pain at a specific strike price
    """
    total_pain = 0.0

    for strike_data in data:
        strike = strike_data.get("strikePrice", 0)

        # Calculate call option pain
        if "CE" in strike_data and strike < test_strike:
            ce_oi = strike_data["CE"].get("openInterest", 0)
            total_pain += (test_strike - strike) * ce_oi

        # Calculate put option pain
        if "PE" in strike_data and strike > test_strike:
            pe_oi = strike_data["PE"].get("openInterest", 0)
            total_pain += (strike - test_strike) * pe_oi

    return total_pain
