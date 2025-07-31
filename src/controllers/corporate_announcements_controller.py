"""
Corporate Announcements Controller using NSE library

FastAPI controller for NSE corporate announcements and actions data.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from nse import NSE

logger = logging.getLogger(__name__)

# Constants
SYMBOL_DESC = "Stock symbol"
DATE_DESC = "Date in YYYY-MM-DD format"

# Initialize NSE client with download folder
nse = NSE(download_folder='/tmp')

router = APIRouter(
    prefix="/api/v1/corporate",
    tags=["Corporate Announcements"],
    responses={404: {"description": "Not found"}},
)

@router.get("/actions")
async def actions(symbol: Optional[str] = Query(None, description=SYMBOL_DESC)):
    """
    Get corporate actions data for a given symbol or all symbols
    """
    try:
        logger.info(f"Fetching corporate actions for symbol: {symbol}")

        # Get corporate actions data from NSE
        if symbol:
            actions_data = nse.actions(symbol=symbol)
        else:
            actions_data = nse.actions()

        if not actions_data:
            raise HTTPException(status_code=404, detail=f"No corporate actions data found for symbol: {symbol}")

        return {
            "symbol": symbol,
            "actions": actions_data,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching corporate actions for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch corporate actions: {str(e)}")

@router.get("/announcements")
async def announcements(symbol: Optional[str] = Query(None, description=SYMBOL_DESC)):
    """
    Get corporate announcements data for a given symbol or all symbols
    """
    try:
        logger.info(f"Fetching corporate announcements for symbol: {symbol}")

        # Get corporate announcements data from NSE
        if symbol:
            announcements_data = nse.announcements(symbol=symbol)
        else:
            announcements_data = nse.announcements()

        if not announcements_data:
            raise HTTPException(status_code=404, detail=f"No announcements data found for symbol: {symbol}")

        return {
            "symbol": symbol,
            "announcements": announcements_data,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching announcements for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch announcements: {str(e)}")

@router.get("/board-meetings")
async def board_meetings(symbol: Optional[str] = Query(None, description=SYMBOL_DESC)):
    """
    Get board meetings data for a given symbol or all symbols
    """
    try:
        logger.info(f"Fetching board meetings for symbol: {symbol}")

        # Get board meetings data from NSE
        if symbol:
            meetings_data = nse.boardMeetings(symbol=symbol)
        else:
            meetings_data = nse.boardMeetings()

        if not meetings_data:
            raise HTTPException(status_code=404, detail=f"No board meetings data found for symbol: {symbol}")

        return {
            "symbol": symbol,
            "board_meetings": meetings_data,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching board meetings for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch board meetings: {str(e)}")

@router.get("/annual-reports")
async def annual_reports(symbol: str = Query(..., description=SYMBOL_DESC)):
    """
    Get annual reports data for a given symbol
    """
    try:
        logger.info(f"Fetching annual reports for symbol: {symbol}")

        # Get annual reports data from NSE
        reports_data = nse.annual_reports(symbol=symbol)

        if not reports_data:
            raise HTTPException(status_code=404, detail=f"No annual reports data found for symbol: {symbol}")

        return {
            "symbol": symbol,
            "annual_reports": reports_data,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error fetching annual reports for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch annual reports: {str(e)}")
