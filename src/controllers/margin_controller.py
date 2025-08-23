"""
Margin Controller

Controller for margin calculation endpoints using AlgoTest API.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from services.margin_service import margin_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/margin", tags=["margin"])

class Position(BaseModel):
    Ticker: str
    Expiry: str  # DD-MMM-YY format (e.g., "25-Sep-25")
    Strike: float
    InstrumentType: str  # "CE" or "PE"
    NetQty: int

class MarginRequest(BaseModel):
    positions: List[Position]
    index_prices: Optional[Dict[str, float]] = None

class StrikePosition(BaseModel):
    symbol: str
    strikePrice: float
    expiryDate: str  # DD-MMM-YYYY format (e.g., "25-Sep-2025")
    type: str  # "CE" or "PE"

class StrikeMarginRequest(BaseModel):
    strikes: List[StrikePosition]
    quantity: int = 1

@router.post("/calculate")
async def calculate_margin(request: MarginRequest):
    """
    Calculate margin requirements for a list of positions

    Args:
        request: MarginRequest containing positions and optional index prices

    Returns:
        Margin calculation results from AlgoTest API
    """
    try:
        logger.info(f"📊 Received margin calculation request for {len(request.positions)} positions")

        # Convert Pydantic models to dictionaries
        positions = [pos.dict() for pos in request.positions]

        result = await margin_service.calculate_margin(
            positions=positions,
            index_prices=request.index_prices
        )

        return {
            "success": True,
            "message": "Margin calculated successfully",
            "data": result,
            "positions_count": len(request.positions)
        }

    except Exception as e:
        logger.error(f"❌ Error in margin calculation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-strikes")
async def calculate_margin_for_strikes(request: StrikeMarginRequest):
    """
    Calculate margin for option strikes with standardized format

    Args:
        request: StrikeMarginRequest containing strikes and quantity

    Returns:
        Margin calculation results from AlgoTest API
    """
    try:
        logger.info(f"📊 Received strike margin calculation request for {len(request.strikes)} strikes")

        # Convert Pydantic models to dictionaries
        strikes = [strike.dict() for strike in request.strikes]

        result = await margin_service.calculate_margin_for_strikes(
            strikes=strikes,
            quantity=request.quantity
        )

        return {
            "success": True,
            "message": "Margin calculated successfully for strikes",
            "data": result,
            "strikes_count": len(request.strikes),
            "quantity": request.quantity
        }

    except Exception as e:
        logger.error(f"❌ Error in strike margin calculation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-single")
async def calculate_single_position_margin(
    ticker: str = Query(..., description="Stock symbol (e.g., ABCAPITAL)"),
    expiry: str = Query(..., description="Expiry date in DD-MMM-YY format (e.g., 25-Sep-25)"),
    strike: float = Query(..., description="Strike price"),
    instrument_type: str = Query(..., description="Option type: CE or PE"),
    net_qty: int = Query(..., description="Net quantity (negative for short positions)"),
    nifty_price: Optional[float] = Query(None, description="Optional NIFTY index price"),
    banknifty_price: Optional[float] = Query(None, description="Optional BANKNIFTY index price")
):
    """
    Calculate margin for a single position

    Args:
        ticker: Stock symbol
        expiry: Expiry date in DD-MMM-YY format
        strike: Strike price
        instrument_type: Option type (CE or PE)
        net_qty: Net quantity
        nifty_price: Optional NIFTY index price
        banknifty_price: Optional BANKNIFTY index price

    Returns:
        Margin calculation results from AlgoTest API
    """
    try:
        logger.info(f"📊 Calculating margin for single position: {ticker} {strike} {instrument_type}")

        # Prepare index prices if provided
        index_prices = {}
        if nifty_price:
            index_prices["NIFTY"] = nifty_price
        if banknifty_price:
            index_prices["BANKNIFTY"] = banknifty_price

        result = await margin_service.calculate_single_position_margin(
            ticker=ticker,
            expiry=expiry,
            strike=strike,
            instrument_type=instrument_type,
            net_qty=net_qty,
            index_prices=index_prices if index_prices else None
        )

        return {
            "success": True,
            "message": "Single position margin calculated successfully",
            "data": result,
            "position": {
                "ticker": ticker,
                "expiry": expiry,
                "strike": strike,
                "instrument_type": instrument_type,
                "net_qty": net_qty
            }
        }

    except Exception as e:
        logger.error(f"❌ Error in single position margin calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def margin_service_health():
    """
    Health check endpoint for margin service
    """
    return {
        "service": "margin_service",
        "status": "healthy",
        "provider": "AlgoTest API",
        "endpoints": [
            "/calculate",
            "/calculate-strikes",
            "/calculate-single"
        ]
    }
