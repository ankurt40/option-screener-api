"""
NSE Controller

Controller for NSE-specific endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime as dt
from services.nse_service import nse_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nse", tags=["NSE"])

@router.get("/fno-bhavcopy")
async def get_fno_bhavcopy() -> Dict[str, Any]:
    """
    Get FNO Bhavcopy data from NSE

    Returns:
        Dictionary containing FNO Bhavcopy data with metadata
    """
    try:
        logger.info("🎯 NSE FNO Bhavcopy request received")

        # Fetch FNO Bhavcopy data from NSE service
        bhavcopy_data = await nse_service.fetch_fno_bhavcopy()

        return {
            "success": True,
            "message": "FNO Bhavcopy data retrieved successfully",
            "data": bhavcopy_data,
            "timestamp": dt.now().isoformat(),
            "total_records": len(bhavcopy_data) if isinstance(bhavcopy_data, list) else len(bhavcopy_data) if isinstance(bhavcopy_data, dict) else 0
        }

    except Exception as e:
        logger.error(f"❌ Error in FNO Bhavcopy endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fno-lots")
async def get_fno_lots() -> Dict[str, Any]:
    """
    Get FNO lot sizes from NSE

    Returns:
        Dictionary containing FNO lot sizes data
    """
    try:
        logger.info("🎯 NSE FNO lots request received")

        # Fetch FNO lots data from NSE service
        lots_data = await nse_service.fetch_fno_lots()

        return {
            "success": True,
            "message": "FNO lots data retrieved successfully",
            "data": lots_data,
            "timestamp": dt.now().isoformat(),
            "total_symbols": len(lots_data) if lots_data else 0
        }

    except Exception as e:
        logger.error(f"❌ Error in FNO lots endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fno-stocks")
async def get_fno_stocks() -> Dict[str, Any]:
    """
    Get list of FNO stocks from NSE

    Returns:
        Dictionary containing FNO stocks list
    """
    try:
        logger.info("🎯 NSE FNO stocks request received")

        # Fetch FNO stocks data from NSE service
        stocks_data = await nse_service.list_fno_stocks()

        return {
            "success": True,
            "message": "FNO stocks list retrieved successfully",
            "data": stocks_data.get("data", []),
            "timestamp": dt.now().isoformat(),
            "total_stocks": stocks_data.get("total", 0)
        }

    except Exception as e:
        logger.error(f"❌ Error in FNO stocks endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def nse_service_health():
    """
    Health check endpoint for NSE service
    """
    return {
        "service": "nse_service",
        "status": "healthy",
        "provider": "NSE Library",
        "endpoints": [
            "/fno-bhavcopy",
            "/fno-lots",
            "/fno-stocks"
        ],
        "timestamp": dt.now().isoformat()
    }
