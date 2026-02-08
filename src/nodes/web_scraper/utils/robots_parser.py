 
"""
Robots.txt parser and validator
"""
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from typing import Optional, Dict
import requests
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class RobotsParser:
    """
    Handles robots.txt parsing and caching
    """
    
    def __init__(self, cache_ttl_hours: int = 24):
        self.cache: Dict[str, tuple] = {}  # domain -> (parser, timestamp)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.user_agent = "WebScraperBot"
    
    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached robots.txt is still valid"""
        return datetime.now() - timestamp < self.cache_ttl
    
    def can_fetch(self, url: str, user_agent: Optional[str] = None) -> bool:
        """
        Check if URL can be fetched according to robots.txt
        
        Args:
            url: URL to check
            user_agent: User agent string (optional)
            
        Returns:
            True if URL can be fetched, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Check cache
            if domain in self.cache:
                parser, timestamp = self.cache[domain]
                if self.is_cache_valid(timestamp):
                    return parser.can_fetch(user_agent or self.user_agent, url)
            
            # Fetch and parse robots.txt
            parser = self._fetch_robots(url)
            if parser:
                self.cache[domain] = (parser, datetime.now())
                return parser.can_fetch(user_agent or self.user_agent, url)
            
            # If no robots.txt found, allow by default
            return True
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # On error, allow scraping
            return True
    
    def _fetch_robots(self, url: str) -> Optional[RobotFileParser]:
        """Fetch and parse robots.txt"""
        try:
            robots_url = self._get_robots_url(url)
            parser = RobotFileParser()
            parser.set_url(robots_url)
            parser.read()
            return parser
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt from {url}: {e}")
            return None
    
    def get_crawl_delay(self, url: str, user_agent: Optional[str] = None) -> Optional[float]:
        """
        Get crawl delay from robots.txt
        
        Args:
            url: URL to check
            user_agent: User agent string (optional)
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Check cache
            if domain in self.cache:
                parser, timestamp = self.cache[domain]
                if self._is_cache_valid(timestamp):
                    return parser.crawl_delay(user_agent or self.user_agent)
            
            # Fetch and parse robots.txt
            parser = self._fetch_robots(url)
            if parser:
                self.cache[domain] = (parser, datetime.now())
                delay = parser.crawl_delay(user_agent or self.user_agent)
                return float(delay) if delay else None
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting crawl delay for {url}: {e}")
            return None
    
    def clear_cache(self):
        """Clear the robots.txt cache"""
        self.cache.clear()