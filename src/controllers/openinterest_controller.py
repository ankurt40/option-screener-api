"""
OpenInterest Controller

Controller for fetching FNO price data from Motilal Oswal API
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
from services.openinterest_service import openinterest_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/openinterest", tags=["OpenInterest API"])

@router.get("/fno-price")
async def get_fno_price_data(
    date: str = Query("30-Sept-2025", description="Date in DD-MMM-YYYY format"),
    instrument_id: str = Query("2", description="Instrument ID")
) -> Dict[str, Dict[str, Any]]:
    """
    Get FNO price data from Motilal Oswal API

    Args:
        date: Date in format DD-MMM-YYYY (default: 30-Sept-2025)
        instrument_id: Instrument ID (default: 2)

    Returns:
        Dictionary mapping nseCode to flattened FNO series data
    """
    try:
        logger.info(f"🎯 OpenInterest FNO price request for date: {date}, instrument: {instrument_id}")

        # Use the clean service method that handles everything internally
        series_data = await openinterest_service.get_fno_series_data(date=date, instrument_id=instrument_id)

        if not series_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch or extract FNO series data from Motilal Oswal API"
            )

        logger.info(f"✅ Successfully retrieved {len(series_data)} series items mapped by nseCode")
        return series_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in OpenInterest FNO price endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def openinterest_health_check():
    """
    Health check endpoint for OpenInterest service
    """
    try:
        return {
            "status": "healthy",
            "service": "OpenInterest",
            "message": "OpenInterest service is running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error in OpenInterest health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
