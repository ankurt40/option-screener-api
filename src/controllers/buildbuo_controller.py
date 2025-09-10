"""
BuildBuo Controller

Controller for fetching FNO price data from Motilal Oswal API
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
from services.buildbuo_service import buildbuo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/buildbuo", tags=["BuildBuo API"])

@router.get("/fno-price")
async def get_fno_price_data(
    date: str = Query("30-Sept-2025", description="Date in DD-MMM-YYYY format"),
    instrument_id: str = Query("2", description="Instrument ID")
) -> List[Dict[str, Any]]:
    """
    Get FNO price data from Motilal Oswal API

    Args:
        date: Date in format DD-MMM-YYYY (default: 30-Sept-2025)
        instrument_id: Instrument ID (default: 2)

    Returns:
        Raw FNO price data from Motilal Oswal API
    """
    try:
        logger.info(f"🎯 BuildBuo FNO price request for date: {date}, instrument: {instrument_id}")

        data = await buildbuo_service.get_fno_price_data(date=date, instrument_id=instrument_id)

        if data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch FNO price data from Motilal Oswal API"
            )

        # Use the service method to extract series data
        series_data = await buildbuo_service.extract_series_from_response(data)
        logger.info(f"✅ Successfully processed response and extracted {len(series_data)} series items")
        return series_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in BuildBuo FNO price endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fno-data")
async def get_fno_data_custom(
    date: Optional[str] = Query(None, description="Date in DD-MMM-YYYY format"),
    i: Optional[str] = Query(None, description="Instrument parameter"),
    **additional_params
) -> Dict[str, Any]:
    """
    Get FNO data with custom parameters from Motilal Oswal API

    Args:
        date: Date in format DD-MMM-YYYY
        i: Instrument parameter
        **additional_params: Any additional query parameters

    Returns:
        FNO data from Motilal Oswal API
    """
    try:
        # Build parameters dictionary
        params = {}
        if date:
            params['Date'] = date
        if i:
            params['i'] = i

        # Add any additional parameters
        params.update(additional_params)

        logger.info(f"🎯 BuildBuo custom FNO data request with params: {params}")

        data = await buildbuo_service.get_fno_data_with_custom_params(**params)

        if data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch FNO data from Motilal Oswal API"
            )

        response = {
            "success": True,
            "message": "FNO data retrieved successfully with custom parameters",
            "request_params": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ Successfully fetched custom FNO data")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in BuildBuo custom FNO data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def buildbuo_health_check():
    """
    Health check endpoint for BuildBuo service
    """
    try:
        return {
            "status": "healthy",
            "service": "BuildBuo",
            "message": "BuildBuo service is running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error in BuildBuo health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
