"""
Scheduler Controller

API endpoints for managing the Dhan scheduler
"""

from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from typing import Dict, Any
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from scheduler.dhan_scheduler import dhan_scheduler

logger = logging.getLogger(__name__)

# Create router for scheduler management endpoints
router = APIRouter(
    prefix="/api/v1/scheduler",
    tags=["Scheduler Management"],
    responses={404: {"description": "Not found"}},
)

@router.post("/start")
async def start_scheduler() -> Dict[str, Any]:
    """
    Start the Dhan scheduler to refresh option data every 15 minutes
    """
    try:
        dhan_scheduler.start_scheduler()

        return {
            "success": True,
            "message": "Dhan scheduler started successfully",
            "interval_minutes": 55,
            "exchange": "NSE",
            "expiry": "2025-09-30",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/stop")
async def stop_scheduler() -> Dict[str, Any]:
    """
    Stop the Dhan scheduler
    """
    try:
        dhan_scheduler.stop_scheduler()

        return {
            "success": True,
            "message": "Dhan scheduler stopped successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@router.get("/status")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    Get current status of the Dhan scheduler
    """
    try:
        status = dhan_scheduler.get_scheduler_status()

        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/run-now")
async def run_scheduler_now() -> Dict[str, Any]:
    """
    Manually trigger a scheduler run to refresh option data immediately
    """
    try:
        logger.info("🔄 Manual scheduler run triggered")

        # Run the refresh task immediately
        await dhan_scheduler.refresh_all_symbols_option_data()

        return {
            "success": True,
            "message": "Manual option data refresh completed",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error in manual scheduler run: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run scheduler manually: {str(e)}")
