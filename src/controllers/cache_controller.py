from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from typing import Dict, Any

from models.option_models import APIResponse
from services.cache_service import cache_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router for cache management endpoints
router = APIRouter(
    prefix="/api/v1/cache",
    tags=["Cache Management"],
    responses={404: {"description": "Not found"}},
)

@router.get("/info", response_model=Dict[str, Any])
async def get_cache_info():
    """
    Get detailed cache information including all entries and statistics

    Returns:
    - Cache entries with TTL and expiry information
    - Cache statistics (hits, misses, hit rate, etc.)
    - Memory usage information
    """
    try:
        cache_info = cache_service.get_cache_info()
        logger.info(f"📊 Cache info requested - {cache_info['stats']['total_entries']} entries")
        return cache_info
    except Exception as e:
        logger.error(f"❌ Error getting cache info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cache information")

@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """
    Get cache statistics summary

    Returns:
    - Hit rate percentage
    - Total hits and misses
    - Total cache operations
    - Current cache size
    """
    try:
        stats = cache_service.get_stats()
        logger.info(f"📈 Cache stats requested - Hit rate: {stats['hit_rate_percentage']}%")
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

@router.delete("/clear", response_model=APIResponse)
async def clear_cache():
    """
    Clear all cache entries

    This will remove all cached data including:
    - Option chain data for all symbols
    - F&O stocks list
    - Any other cached data
    """
    try:
        cleared_count = cache_service.clear()
        logger.info(f"🧹 Cache cleared - {cleared_count} entries removed")

        return APIResponse(
            success=True,
            message=f"Cache cleared successfully. {cleared_count} entries removed.",
            data={"cleared_entries": cleared_count},
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.delete("/cleanup", response_model=APIResponse)
async def cleanup_expired_cache():
    """
    Clean up only expired cache entries

    This will remove expired entries while keeping valid cached data
    """
    try:
        cleaned_count = await cache_service.cleanup_expired()
        logger.info(f"🧹 Cache cleanup completed - {cleaned_count} expired entries removed")

        return APIResponse(
            success=True,
            message=f"Cache cleanup completed. {cleaned_count} expired entries removed.",
            data={"cleaned_entries": cleaned_count},
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"❌ Error cleaning up cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup expired cache")

@router.delete("/delete/{cache_key}", response_model=APIResponse)
async def delete_cache_entry(cache_key: str):
    """
    Delete a specific cache entry by key

    Args:
        cache_key: The cache key to delete (e.g., 'RELIANCE', 'FNO_STOCKS')
    """
    try:
        deleted = cache_service.delete(cache_key)

        if deleted:
            logger.info(f"🗑️ Cache entry deleted: {cache_key}")
            return APIResponse(
                success=True,
                message=f"Cache entry '{cache_key}' deleted successfully.",
                data={"deleted_key": cache_key},
                timestamp=datetime.now()
            )
        else:
            logger.warning(f"⚠️ Cache entry not found: {cache_key}")
            return APIResponse(
                success=False,
                message=f"Cache entry '{cache_key}' not found.",
                data={"deleted_key": None},
                timestamp=datetime.now()
            )
    except Exception as e:
        logger.error(f"❌ Error deleting cache entry {cache_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete cache entry: {cache_key}")

@router.get("/keys", response_model=Dict[str, Any])
async def get_cache_keys():
    """
    Get all cache keys

    Returns list of all current cache keys (expired entries are automatically cleaned up)
    """
    try:
        keys = cache_service.get_keys()
        logger.info(f"🔑 Cache keys requested - {len(keys)} keys found")

        return {
            "keys": keys,
            "total_keys": len(keys),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error getting cache keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cache keys")
