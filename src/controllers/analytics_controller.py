from fastapi import APIRouter, HTTPException, Query
import logging
from datetime import datetime

from models.option_models import VolatileOptionsResponse, APIResponse
from services.analytics_service import analytics_service
from services.nse_service import nse_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router for analytics endpoints
router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
    responses={404: {"description": "Not found"}},
)

@router.get("/top-volatile-options", response_model=VolatileOptionsResponse)
async def get_top_volatile_options(
    symbol: str = Query("RELIANCE", description="Stock symbol for volatile options analysis")
):
    """
    Fetch top volatile options for a given symbol by analyzing option chain data

    - **symbol**: Stock symbol (e.g., RELIANCE, TCS, HDFCBANK)

    Returns list of Strike objects with detailed option data including:
    - Strike prices and expiry dates
    - Open Interest and changes
    - Volume and Implied Volatility
    - Price data and market depth
    - Option type (PE/CE)
    """
    try:
        logger.info(f"🎯 Volatile options analysis request received for symbol: {symbol}")

        # Validate symbol
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol parameter is required")

        symbol = symbol.upper().strip()

        # Use analytics service to get volatile options
        strikes = await analytics_service.get_volatile_options(symbol)

        return VolatileOptionsResponse(
            success=True,
            message=f"Top volatile options retrieved successfully for {symbol}",
            data=strikes,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in volatile options analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while analyzing volatile options for {symbol}"
        )

@router.get("/analytics/health", response_model=APIResponse)
async def analytics_health():
    """
    Health check endpoint for analytics service
    """
    try:
        return APIResponse(
            success=True,
            message="Analytics service is healthy",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"❌ Analytics health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Analytics service health check failed")

@router.get("/cache/status")
async def get_cache_status():
    """
    Get current cache status showing cached symbols and their expiry times
    """
    try:
        cache_info = []

        for symbol, cache_entry in nse_service._cache.items():
            timestamp = cache_entry["timestamp"]
            expires_at = timestamp + nse_service._cache_duration
            time_remaining = expires_at - datetime.now()

            cache_info.append({
                "symbol": symbol,
                "cached_at": timestamp.isoformat(),
                "expires_at": expires_at.isoformat(),
                "minutes_remaining": max(0, int(time_remaining.total_seconds() / 60)),
                "is_valid": nse_service._is_cache_valid(symbol)
            })

        return APIResponse(
            success=True,
            message=f"Cache status retrieved. {len(cache_info)} symbols cached.",
            data={
                "cache_duration_minutes": int(nse_service._cache_duration.total_seconds() / 60),
                "cached_symbols": cache_info,
                "total_cached": len(cache_info)
            },
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"❌ Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(symbol: str = Query(None, description="Symbol to clear from cache (optional)")):
    """
    Clear cache for a specific symbol or all symbols

    - **symbol**: Optional symbol to clear. If not provided, clears entire cache
    """
    try:
        if symbol:
            symbol = symbol.upper().strip()
            if symbol in nse_service._cache:
                del nse_service._cache[symbol]
                logger.info(f"🗑️ Cleared cache for {symbol}")
                return APIResponse(
                    success=True,
                    message=f"Cache cleared for symbol: {symbol}",
                    data={"cleared_symbol": symbol},
                    timestamp=datetime.now()
                )
            else:
                return APIResponse(
                    success=True,
                    message=f"No cache found for symbol: {symbol}",
                    data={"symbol": symbol},
                    timestamp=datetime.now()
                )
        else:
            cleared_count = len(nse_service._cache)
            nse_service._cache.clear()
            logger.info(f"🗑️ Cleared entire cache ({cleared_count} symbols)")

            return APIResponse(
                success=True,
                message=f"Entire cache cleared. Removed {cleared_count} symbols.",
                data={"cleared_count": cleared_count},
                timestamp=datetime.now()
            )

    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics and performance metrics
    """
    try:
        total_symbols = len(nse_service._cache)
        valid_symbols = sum(1 for symbol in nse_service._cache.keys() if nse_service._is_cache_valid(symbol))
        expired_symbols = total_symbols - valid_symbols

        return APIResponse(
            success=True,
            message="Cache statistics retrieved successfully",
            data={
                "total_cached_symbols": total_symbols,
                "valid_cached_symbols": valid_symbols,
                "expired_symbols": expired_symbols,
                "cache_duration_minutes": int(nse_service._cache_duration.total_seconds() / 60),
                "cache_hit_efficiency": f"{(valid_symbols/max(1, total_symbols))*100:.1f}%" if total_symbols > 0 else "0%"
            },
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")
