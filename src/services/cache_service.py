"""
Global Cache Service

A centralized caching service that can be used across all components in the application.
Provides thread-safe caching with TTL (Time To Live) support and automatic cleanup.
"""

import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

class CacheService:
    """
    Global caching service with TTL support and automatic cleanup

    Features:
    - Thread-safe operations
    - TTL (Time To Live) support
    - Automatic cleanup of expired entries
    - Statistics tracking
    - Configurable default TTL
    """

    def __init__(self, default_ttl_minutes: int = 60):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._default_ttl = timedelta(minutes=default_ttl_minutes)
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "cleanups": 0
        }
        logger.info(f"🗄️ Cache service initialized with default TTL: {default_ttl_minutes} minutes")

    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired"""
        if "expires_at" not in cache_entry:
            return True

        return datetime.now() >= cache_entry["expires_at"]

    def _cleanup_expired_entries(self) -> int:
        """Remove expired entries from cache"""
        with self._lock:
            expired_keys = []

            for key, entry in self._cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                logger.debug(f"🗑️ Cleaned up expired cache entry: {key}")

            if expired_keys:
                self._stats["cleanups"] += len(expired_keys)
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                logger.debug(f"🚫 Cache miss: {key}")
                return None

            entry = self._cache[key]

            if self._is_expired(entry):
                del self._cache[key]
                self._stats["misses"] += 1
                logger.debug(f"⏰ Cache expired: {key}")
                return None

            self._stats["hits"] += 1
            logger.debug(f"✅ Cache hit: {key}")
            return entry["data"]

    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        """
        Set a value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl_minutes: Time to live in minutes (uses default if None)
        """
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self._default_ttl
        expires_at = datetime.now() + ttl

        with self._lock:
            self._cache[key] = {
                "data": value,
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "ttl_minutes": ttl_minutes or (self._default_ttl.total_seconds() / 60)
            }
            self._stats["sets"] += 1

        logger.debug(f"💾 Cached: {key} (expires: {expires_at.strftime('%H:%M:%S')})")

    def delete(self, key: str) -> bool:
        """
        Delete a specific cache entry

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                logger.debug(f"🗑️ Deleted cache entry: {key}")
                return True
            return False

    def clear(self) -> int:
        """
        Clear all cache entries

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🧹 Cleared all cache entries: {count} items")
            return count

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache and is not expired

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is not expired
        """
        return self.get(key) is not None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

            return {
                "total_entries": len(self._cache),
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "deletes": self._stats["deletes"],
                "cleanups": self._stats["cleanups"],
                "hit_rate_percentage": round(hit_rate, 2),
                "total_requests": total_requests
            }

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information including entry details

        Returns:
            Dictionary with detailed cache information
        """
        with self._lock:
            cache_info = {}

            for key, entry in self._cache.items():
                time_remaining = entry["expires_at"] - datetime.now()
                cache_info[key] = {
                    "created_at": entry["created_at"].isoformat(),
                    "expires_at": entry["expires_at"].isoformat(),
                    "ttl_minutes": entry["ttl_minutes"],
                    "time_remaining_seconds": max(0, int(time_remaining.total_seconds())),
                    "is_expired": self._is_expired(entry),
                    "data_size_bytes": len(str(entry["data"]))
                }

            return {
                "entries": cache_info,
                "stats": self.get_stats()
            }

    async def cleanup_expired(self) -> int:
        """
        Async method to cleanup expired entries

        Returns:
            Number of entries cleaned up
        """
        return self._cleanup_expired_entries()

    def get_keys(self) -> list:
        """
        Get all cache keys (expired entries are automatically cleaned up)

        Returns:
            List of cache keys
        """
        with self._lock:
            # Clean up expired entries first
            self._cleanup_expired_entries()
            return list(self._cache.keys())

# Global cache service instance
cache_service = CacheService(default_ttl_minutes=60)

# Convenience functions for direct usage
def get_cache(key: str) -> Optional[Any]:
    """Get value from global cache"""
    return cache_service.get(key)

def set_cache(key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
    """Set value in global cache"""
    cache_service.set(key, value, ttl_minutes)

def delete_cache(key: str) -> bool:
    """Delete value from global cache"""
    return cache_service.delete(key)

def clear_cache() -> int:
    """Clear all cache entries"""
    return cache_service.clear()

def cache_exists(key: str) -> bool:
    """Check if key exists in cache"""
    return cache_service.exists(key)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return cache_service.get_stats()

def get_cache_info() -> Dict[str, Any]:
    """Get detailed cache information"""
    return cache_service.get_cache_info()
