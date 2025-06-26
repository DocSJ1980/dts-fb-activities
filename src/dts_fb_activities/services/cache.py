"""Cache service with TTL (Time To Live) functionality."""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cache entry with data and timestamp."""
    
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def time_until_expiry(self) -> int:
        """Get seconds until expiry (0 if already expired)."""
        if self.is_expired():
            return 0
        return int((self.expires_at - datetime.now()).total_seconds())


class CacheService:
    """In-memory cache service with TTL support."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, **kwargs) -> str:
        """Generate a cache key from keyword arguments."""
        # Sort kwargs to ensure consistent key generation
        sorted_kwargs = dict(sorted(kwargs.items()))
        key_string = json.dumps(sorted_kwargs, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get data from cache if exists and not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._hits += 1
                logger.info(f"Cache hit for key: {key[:8]}... (expires in {entry.time_until_expiry()}s)")
                return entry.data
            else:
                # Remove expired entry
                del self._cache[key]
                logger.info(f"Cache entry expired for key: {key[:8]}...")
        
        self._misses += 1
        logger.info(f"Cache miss for key: {key[:8]}...")
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set data in cache with TTL."""
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(data, ttl)
        logger.info(f"Cache set for key: {key[:8]}... (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """Delete a specific cache entry."""
        if key in self._cache:
            del self._cache[key]
            logger.info(f"Cache entry deleted for key: {key[:8]}...")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared ({count} entries removed)")
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries and return count of removed entries."""
        expired_keys = [
            key for key, entry in self._cache.items() 
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def get_or_set(self, key: str, fetch_function, ttl: Optional[int] = None) -> Any:
        """Get from cache or execute function and cache result."""
        # Try to get from cache first
        cached_data = self.get(key)
        if cached_data is not None:
            return cached_data
        
        # Not in cache, fetch new data
        logger.info(f"Fetching new data for key: {key[:8]}...")
        data = fetch_function()
        
        # Cache the result
        self.set(key, data, ttl)
        return data
    
    def create_key_for_surveillance_data(self, date: str, town_code: int, uc_code: int) -> str:
        """Create a specific cache key for surveillance data."""
        return self._generate_key(
            endpoint="surveillance_data",
            date=date,
            town_code=town_code,
            uc_code=uc_code
        )
    
    def create_key_for_towns(self) -> str:
        """Create a cache key for towns data."""
        return self._generate_key(endpoint="towns")
    
    def create_key_for_ucs(self, town_code: int) -> str:
        """Create a cache key for UCs data."""
        return self._generate_key(endpoint="ucs", town_code=town_code)

    def create_key_for_cookie(self) -> str:
        """Create a cache key for the authentication cookie."""
        return self._generate_key(endpoint="auth_cookie")


# Global cache instance
cache_service = CacheService(default_ttl=300)  # 5 minutes


# Background task to clean up expired entries
async def cleanup_expired_cache():
    """Background task to periodically clean up expired cache entries."""
    cache_service.cleanup_expired()
