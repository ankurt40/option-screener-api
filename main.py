"""
Option Screener API

A FastAPI application for screening stock options from NSE.
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime

from controllers.option_chain_controller import router as option_chain_router
from controllers.option_controller import router as option_router
from controllers.corporate_announcements_controller import router as corporate_router
from controllers.analytics_controller import router as analytics_router
from controllers.list_stocks_controller import router as list_stocks_router
from controllers.cache_controller import router as cache_router
from controllers.dhan_controller import router as dhan_router
from controllers.scheduler_controller import router as scheduler_router
from models.option_models import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Option Screener API",
    description="A Python API for screening stock options from NSE",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(option_chain_router)
app.include_router(option_router)
app.include_router(corporate_router)
app.include_router(analytics_router)
app.include_router(list_stocks_router)
app.include_router(cache_router)
app.include_router(dhan_router)
app.include_router(scheduler_router)

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        service="Option Screener API",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        service="Option Screener API",
        version="1.0.0"
    )

@app.on_event("startup")
async def startup_event():
    """Initialize services and start scheduler on application startup"""
    logger.info("🚀 Application startup - initializing services...")

    try:
        # Import and start the scheduler
        from scheduler.dhan_scheduler import dhan_scheduler
       # dhan_scheduler.start_scheduler()
        logger.info("✅ Dhan scheduler started automatically")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler on startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of services"""
    logger.info("🛑 Application shutdown - stopping services...")

    try:
        # Import and stop the scheduler
        from scheduler.dhan_scheduler import dhan_scheduler
       # dhan_scheduler.stop_scheduler()
        logger.info("✅ Dhan scheduler stopped gracefully")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler on shutdown: {e}")

def main():
    """Start the FastAPI server"""
    logger.info("🚀 Starting Option Screener API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
