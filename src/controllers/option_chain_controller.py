from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime

from models.option_models import OptionChainResponse, APIResponse, HealthResponse
from services.nse_service import nse_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router for option chain endpoints
router = APIRouter(
    prefix="/api",
    tags=["Option Chain"],
    responses={404: {"description": "Not found"}},
)

@router.get("/option-chain", response_model=OptionChainResponse)
async def get_option_chain(
    symbol: str = Query("RELIANCE", description="Stock symbol for option chain data")
):
    """
    Fetch option chain data for a given symbol from NSE

    - **symbol**: Stock symbol (e.g., RELIANCE, TCS, HDFCBANK)

    Returns complete option chain with calls and puts data including:
    - Strike prices
    - Open Interest (OI)
    - Volume
    - Implied Volatility (IV)
    - Last Traded Price (LTP)
    - Change and percentage change
    """
    try:
        logger.info(f"🎯 Option chain request received for symbol: {symbol}")

        # Validate symbol
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol parameter is required")

        symbol = symbol.upper().strip()
        logger.info(f"🔄 Processing option chain for: {symbol}")

        # Fetch data from NSE service
        option_data = await nse_service.fetch_option_chain(symbol)

        if not option_data:
            raise HTTPException(status_code=500, detail="Failed to fetch option chain data")

        logger.info(f"✅ Option chain data successfully retrieved for {symbol}")

        return JSONResponse(
            content=option_data,
            status_code=200,
            headers={
                "X-Data-Source": "NSE-India" if "records" in option_data else "Mock-Data",
                "X-Symbol": symbol,
                "X-Timestamp": datetime.now().isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in option chain controller: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching option chain for {symbol}"
        )

@router.get("/option-chain/symbols", response_model=APIResponse)
async def get_supported_symbols():
    """
    Get list of supported symbols for option chain data
    """
    try:
        supported_symbols = {
            "large_cap": [
                {"symbol": "RELIANCE", "name": "Reliance Industries", "price_range": "1200-1400"},
                {"symbol": "TCS", "name": "Tata Consultancy Services", "price_range": "4000-4500"},
                {"symbol": "HDFCBANK", "name": "HDFC Bank", "price_range": "1600-1800"},
                {"symbol": "INFY", "name": "Infosys", "price_range": "1700-1900"},
                {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "price_range": "2300-2600"}
            ],
            "mid_cap": [
                {"symbol": "ITC", "name": "ITC Limited", "price_range": "400-500"},
                {"symbol": "WIPRO", "name": "Wipro Limited", "price_range": "450-550"},
                {"symbol": "SBIN", "name": "State Bank of India", "price_range": "750-900"}
            ]
        }

        return APIResponse(
            success=True,
            message="Supported symbols retrieved successfully",
            data=supported_symbols,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"❌ Error fetching supported symbols: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch supported symbols")

@router.get("/option-chain/health", response_model=HealthResponse)
async def option_chain_health():
    """
    Health check endpoint for option chain service
    """
    try:
        # Test NSE service connectivity
        test_symbol = "RELIANCE"
        test_data = await nse_service.fetch_option_chain(test_symbol)

        service_status = "healthy" if test_data else "degraded"

        return HealthResponse(
            status=service_status,
            timestamp=datetime.now(),
            service="option-chain-api",
            version="1.0.0"
        )

    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            service="option-chain-api",
            version="1.0.0"
        )

@router.post("/option-chain/refresh")
async def refresh_session():
    """
    Manually refresh NSE session (useful when getting 401 errors)
    """
    try:
        logger.info("🔄 Manual session refresh requested")

        # Close existing session
        await nse_service.close_session()

        # Reset session
        nse_service.session = None
        nse_service.cookies = {}

        # Initialize new session
        await nse_service.get_session()

        return APIResponse(
            success=True,
            message="NSE session refreshed successfully",
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"❌ Error refreshing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh session")
