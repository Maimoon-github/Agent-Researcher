"""
Caching middleware for scraped content
"""
import logging
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
import diskcache


logger = logging.getLogger(__name__)


class CacheMiddleware:
    """
    Caches scraped content to avoid re-scraping
    """
    
    def __init__(self, cache_dir: str = "data/cache/web_scraper", ttl_hours: int = 24):
        """
        Initialize cache middleware
        
        Args:
            cache_dir: Directory for cache storage
            ttl_hours: Time-to-live in hours
        """
        self.cache = diskcache.Cache(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)
        self.hits = 0
        self.misses = 0
        
        logger.info(f"Cache middleware initialized at {cache_dir} with TTL={ttl_hours}h")
    
    def _generate_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[Dict]:
        """
        Get cached content for URL
        
        Args:
            url: URL to look up
            
        Returns:
            Cached content dictionary or None
        """
        key = self._generate_key(url)
        
        try:
            cached = self.cache.get(key)
            if cached:
                # Check if still valid
                cache_time = cached.get('cache_timestamp')
                if cache_time:
                    cache_dt = datetime.fromisoformat(cache_time)
                    if datetime.now() - cache_dt < self.ttl:
                        self.hits += 1
                        logger.debug(f"Cache hit for {url}")
                        return cached.get('data')
                    else:
                        # Expired, remove from cache
                        self.cache.delete(key)
                        logger.debug(f"Cache expired for {url}")
            
            self.misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {url}: {e}")
            self.misses += 1
            return None
    
    def set(self, url: str, data: Dict):
        """
        Cache content for URL
        
        Args:
            url: URL to cache
            data: Content data to cache
        """
        key = self._generate_key(url)
        
        try:
            cached_data = {
                'url': url,
                'data': data,
                'cache_timestamp': datetime.now().isoformat()
            }
            self.cache.set(key, cached_data)
            logger.debug(f"Cached content for {url}")
            
        except Exception as e:
            logger.error(f"Cache set error for {url}: {e}")
    
    def delete(self, url: str):
        """
        Delete cached content for URL
        
        Args:
            url: URL to delete from cache
        """
        key = self._generate_key(url)
        try:
            self.cache.delete(key)
            logger.debug(f"Deleted cache for {url}")
        except Exception as e:
            logger.error(f"Cache delete error for {url}: {e}")
    
    def clear(self):
        """Clear all cached content"""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'cache_dir': self.cache.directory
        }