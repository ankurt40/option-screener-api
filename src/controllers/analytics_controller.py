from fastapi import APIRouter, HTTPException, Query
import logging
from datetime import datetime

from models.option_models import VolatileOptionsResponse, APIResponse
from services.analytics_service import analytics_service

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

        # Calculate additional analytics for the strikes
        strikes_with_analytics = analytics_service._calculate_strike_analytics(strikes)

        return VolatileOptionsResponse(
            success=True,
            message=f"Top volatile options with analytics retrieved successfully for {symbol}",
            data=strikes_with_analytics,
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

@router.get("/health", response_model=APIResponse)
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

@router.get("/top-volatile-options-all", response_model=VolatileOptionsResponse)
async def get_top_volatile_options_all():
    """
    Fetch top volatile options for all F&O stocks by analyzing option chain data for each symbol

    This endpoint:
    - Retrieves all F&O stocks from cache
    - Analyzes option chains for each symbol with 2-second delay only when fetching fresh data
    - Returns combined list of Strike objects with detailed option data

    Returns aggregated list of Strike objects with:
    - Strike prices and expiry dates for all symbols
    - Open Interest and changes
    - Volume and Implied Volatility
    - Price data and market depth
    - Option type (PE/CE)
    """
    try:
        # Use analytics service to get volatile options for all stocks
        all_strikes = await analytics_service.get_volatile_options_for_all_stocks()

        # Calculate additional analytics for all strikes
        all_strikes_with_analytics = analytics_service._calculate_strike_analytics(all_strikes)

        return VolatileOptionsResponse(
            success=True,
            message=f"Top volatile options with analytics retrieved for all F&O stocks. Found {len(all_strikes_with_analytics)} total strikes.",
            data=all_strikes_with_analytics,
            timestamp=datetime.now()
        )

    except ValueError as e:
        logger.error(f"❌ Validation error in all symbols volatile options analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Unexpected error in all symbols volatile options analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while analyzing volatile options for all symbols"
        )

@router.get("/only-buyers", response_model=VolatileOptionsResponse)
async def get_only_buyers_options(
    symbol: str = Query("RELIANCE", description="Stock symbol for buyers-only options analysis")
):
    """
    Fetch options where only buyers are present (no sellers) for a given symbol

    Filters options where:
    - askQty or askPrice is not available (0 or None)
    - BUT bidPrice or bidQty is available (> 0)

    This indicates buyer interest without seller pressure

    - **symbol**: Stock symbol (e.g., RELIANCE, TCS, HDFCBANK)

    Returns list of Strike objects with detailed option data including:
    - Strike prices and expiry dates
    - Open Interest and changes
    - Volume and Implied Volatility
    - Price data and market depth
    - Option type (PE/CE)
    - Analytics fields (strike gap, percentages)
    """
    try:
        logger.info(f"🛒 Only-buyers options analysis request received for symbol: {symbol}")

        # Validate symbol
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol parameter is required")

        symbol = symbol.upper().strip()

        # Use analytics service to get volatile options for all stocks
        all_strikes = await analytics_service.get_volatile_options_for_all_stocks()

        # Filter strikes for only-buyers criteria
        only_buyers_strikes = []
        for strike in all_strikes:
            # Check if ask side is not available (no sellers)
            ask_not_available = (strike.askQty == 0 or strike.askQty is None) or (strike.askPrice == 0 or strike.askPrice is None)

            # Check if bid side is available (buyers present)
            bid_available = (strike.bidQty > 0) or (strike.bidprice > 0)

            # Include strike if ask is not available but bid is available
            if ask_not_available and bid_available:
                only_buyers_strikes.append(strike)
                logger.debug(f"🛒 Including strike {strike.strikePrice} {strike.type} - bidQty: {strike.bidQty}, bidPrice: {strike.bidprice}, askQty: {strike.askQty}, askPrice: {strike.askPrice}")

        logger.info(f"🛒 Filtered {len(only_buyers_strikes)} only-buyers strikes from {len(all_strikes)} total strikes for {symbol}")

        # Calculate additional analytics for the filtered strikes
        strikes_with_analytics = analytics_service._calculate_strike_analytics(only_buyers_strikes)

        return VolatileOptionsResponse(
            success=True,
            message=f"Only-buyers options with analytics retrieved successfully for {symbol}. Found {len(strikes_with_analytics)} strikes with buyer interest only.",
            data=strikes_with_analytics,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in only-buyers options analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while analyzing only-buyers options for {symbol}"
        )
