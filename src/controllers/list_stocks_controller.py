from fastapi import APIRouter, HTTPException, Query
import logging
from datetime import datetime
from typing import Optional

from models.option_models import FnoStocksResponse, APIResponse, FnoStock
from services.nse_service import nse_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router for list stocks endpoints
router = APIRouter(
    prefix="/api/v1/stocks",
    tags=["List Stocks"],
    responses={404: {"description": "Not found"}},
)

@router.get("/fno-stocks", response_model=FnoStocksResponse)
async def get_fno_stocks():
    """
    Fetch list of F&O (Futures and Options) stocks from NSE

    This endpoint provides a comprehensive list of all stocks available for
    Futures and Options trading on NSE, including:
    - Stock symbol
    - Company name
    - Lot size for trading

    Data is cached for 15 minutes to optimize performance and prevent rate limiting.
    """
    try:
        logger.info("📋 F&O stocks list request received")

        # Fetch F&O stocks from NSE service
        response_data = await nse_service.list_fno_stocks()

        # Parse the response data
        if "data" in response_data:
            stocks_data = response_data["data"]

            # Convert to FnoStock objects
            fno_stocks = []
            for stock in stocks_data:
                fno_stock = FnoStock(
                    symbol=stock.get("symbol", ""),
                    companyName=stock.get("companyName", ""),
                    lotSize=stock.get("lotSize", 0)
                )
                fno_stocks.append(fno_stock)

            logger.info(f"✅ Successfully retrieved {len(fno_stocks)} F&O stocks")

            return FnoStocksResponse(
                success=True,
                message=f"F&O stocks list retrieved successfully. Found {len(fno_stocks)} stocks.",
                data=fno_stocks,
                total=len(fno_stocks),
                timestamp=datetime.now()
            )
        else:
            logger.warning("⚠️ No data found in F&O stocks response")
            return FnoStocksResponse(
                success=False,
                message="No F&O stocks data available",
                data=[],
                total=0,
                timestamp=datetime.now()
            )

    except Exception as e:
        logger.error(f"❌ Error fetching F&O stocks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch F&O stocks list: {str(e)}"
        )

@router.get("/fno-stocks/search", response_model=FnoStocksResponse)
async def search_fno_stocks(
    query: str = Query(..., description="Search query for stock symbol or company name", min_length=1)
):
    """
    Search F&O stocks by symbol or company name

    - **query**: Search term to filter stocks (case-insensitive)

    Returns filtered list of F&O stocks matching the search criteria.
    """
    try:
        logger.info(f"🔍 F&O stocks search request for query: '{query}'")

        # Fetch all F&O stocks first
        response_data = await nse_service.list_fno_stocks()

        if "data" in response_data:
            stocks_data = response_data["data"]
            query_lower = query.lower()

            # Filter stocks based on search query
            filtered_stocks = []
            for stock in stocks_data:
                symbol = stock.get("symbol", "").lower()
                company_name = stock.get("companyName", "").lower()

                if query_lower in symbol or query_lower in company_name:
                    fno_stock = FnoStock(
                        symbol=stock.get("symbol", ""),
                        companyName=stock.get("companyName", ""),
                        lotSize=stock.get("lotSize", 0)
                    )
                    filtered_stocks.append(fno_stock)

            logger.info(f"✅ Found {len(filtered_stocks)} F&O stocks matching '{query}'")

            return FnoStocksResponse(
                success=True,
                message=f"Found {len(filtered_stocks)} F&O stocks matching '{query}'",
                data=filtered_stocks,
                total=len(filtered_stocks),
                timestamp=datetime.now()
            )
        else:
            logger.warning("⚠️ No data found in F&O stocks response for search")
            return FnoStocksResponse(
                success=False,
                message="No F&O stocks data available for search",
                data=[],
                total=0,
                timestamp=datetime.now()
            )

    except Exception as e:
        logger.error(f"❌ Error searching F&O stocks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search F&O stocks: {str(e)}"
        )

@router.get("/fno-stocks/{symbol}", response_model=APIResponse)
async def get_fno_stock_details(symbol: str):
    """
    Get details of a specific F&O stock by symbol

    - **symbol**: Stock symbol (e.g., RELIANCE, TCS, HDFCBANK)

    Returns detailed information about the specific F&O stock.
    """
    try:
        logger.info(f"📋 F&O stock details request for symbol: {symbol}")

        symbol = symbol.upper().strip()

        # Fetch all F&O stocks
        response_data = await nse_service.list_fno_stocks()

        if "data" in response_data:
            stocks_data = response_data["data"]

            # Find the specific stock
            for stock in stocks_data:
                if stock.get("symbol", "").upper() == symbol:
                    fno_stock = FnoStock(
                        symbol=stock.get("symbol", ""),
                        companyName=stock.get("companyName", ""),
                        lotSize=stock.get("lotSize", 0)
                    )

                    logger.info(f"✅ Found F&O stock details for {symbol}")

                    return APIResponse(
                        success=True,
                        message=f"F&O stock details retrieved for {symbol}",
                        data=fno_stock.dict(),
                        timestamp=datetime.now()
                    )

            # Stock not found
            logger.warning(f"⚠️ F&O stock not found: {symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"F&O stock '{symbol}' not found"
            )
        else:
            logger.warning("⚠️ No F&O stocks data available")
            raise HTTPException(
                status_code=500,
                detail="F&O stocks data not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching F&O stock details for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch F&O stock details for {symbol}: {str(e)}"
        )

@router.get("/health", response_model=APIResponse)
async def stocks_health():
    """
    Health check endpoint for stocks service
    """
    try:
        return APIResponse(
            success=True,
            message="List Stocks service is healthy",
            data={"service": "list_stocks", "version": "1.0.0"},
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"❌ Stocks health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Stocks service health check failed")
