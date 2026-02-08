"""
Robots.txt Parser - Handles robots.txt compliance checking
"""

from typing import Optional, Dict
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
import httpx
import logging
from datetime import datetime, timedelta
import asyncio


class RobotsParser:
    """Parses and validates against robots.txt files"""
    
    def __init__(
        self,
        user_agent: str = "ResearchAgent/1.0",
        cache_ttl_hours: int = 24,
        request_timeout: int = 10,
        logger: Optional[logging.Logger] = None
    ):
        self.user_agent = user_agent
        self.cache_ttl_hours = cache_ttl_hours
        self.request_timeout = request_timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache for robots.txt parsers
        self._cache: Dict[str, tuple[RobotFileParser, datetime]] = {}
    
    async def is_allowed_async(self, url: str) -> bool:
        """Asynchronous version of is_allowed"""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get or fetch robots.txt parser
            parser = await self._get_parser_async(base_url)
            
            if parser is None:
                self.logger.warning(f"Could not fetch robots.txt for {base_url}, defaulting to ALLOWED")
                return True
            
            allowed = parser.can_fetch(self.user_agent, url)
            self.logger.debug(f"Robots.txt check (async) for {url}: {'allowed' if allowed else 'disallowed'}")
            
            return allowed
            
        except Exception as e:
            self.logger.error(f"Error checking robots.txt async for {url}: {str(e)}")
            return False

    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed to be fetched according to robots.txt
        
        Args:
            url: The URL to check
            
        Returns:
            True if allowed, False if disallowed
        """
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get or fetch robots.txt parser
            parser = self._get_parser(base_url)
            
            if parser is None:
                # If we can't get robots.txt, default to allowed for research purposes
                # but log a warning. This avoids blocking legitimate sources on sites
                # that block robots.txt requests specifically.
                self.logger.warning(f"Could not fetch robots.txt for {base_url}, defaulting to ALLOWED")
                return True
            
            # Check if URL is allowed
            allowed = parser.can_fetch(self.user_agent, url)
            self.logger.debug(f"Robots.txt check for {url}: {'allowed' if allowed else 'disallowed'}")
            
            return allowed
            
        except Exception as e:
            self.logger.error(f"Error checking robots.txt for {url}: {str(e)}")
            # Default to conservative (disallow) on error
            return False
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt
        
        Args:
            url: The URL to check
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            parser = self._get_parser(base_url)
            if parser is None:
                return None
            
            # Try to get crawl delay
            delay = parser.crawl_delay(self.user_agent)
            return delay
            
        except Exception as e:
            self.logger.error(f"Error getting crawl delay for {url}: {str(e)}")
            return None
    
    async def _get_parser_async(self, base_url: str) -> Optional[RobotFileParser]:
        """Asynchronous version of _get_parser"""
        if base_url in self._cache:
            parser, cached_time = self._cache[base_url]
            if datetime.now() - cached_time < timedelta(hours=self.cache_ttl_hours):
                return parser
            else:
                del self._cache[base_url]
        
        return await self._fetch_and_parse_async(base_url)

    def _get_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """
        Get robots.txt parser for a base URL, using cache if available
        
        Args:
            base_url: The base URL (scheme + netloc)
            
        Returns:
            RobotFileParser instance or None if unavailable
        """
        # Check cache
        if base_url in self._cache:
            parser, cached_time = self._cache[base_url]
            
            # Check if cache is still valid
            if datetime.now() - cached_time < timedelta(hours=self.cache_ttl_hours):
                self.logger.debug(f"Using cached robots.txt for {base_url}")
                return parser
            else:
                # Cache expired
                del self._cache[base_url]
        
        # Fetch and parse robots.txt
        return self._fetch_and_parse(base_url)
    
    async def _fetch_and_parse_async(self, base_url: str) -> Optional[RobotFileParser]:
        """Asynchronous version of _fetch_and_parse"""
        robots_url = urljoin(base_url, '/robots.txt')
        
        try:
            self.logger.debug(f"Fetching robots.txt async from {robots_url}")
            
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                response = await client.get(
                    robots_url,
                    headers={'User-Agent': self.user_agent},
                    follow_redirects=True
                )
            
            parser = RobotFileParser()
            parser.set_url(robots_url)
            
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
                self._cache[base_url] = (parser, datetime.now())
                return parser
            elif response.status_code == 404:
                parser.parse([])
                self._cache[base_url] = (parser, datetime.now())
                return parser
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"Error fetching robots.txt async for {base_url}: {str(e)}")
            return None

    def _fetch_and_parse(self, base_url: str) -> Optional[RobotFileParser]:
        """
        Fetch and parse robots.txt file
        
        Args:
            base_url: The base URL to fetch robots.txt from
            
        Returns:
            RobotFileParser instance or None if fetch fails
        """
        robots_url = urljoin(base_url, '/robots.txt')
        
        try:
            self.logger.debug(f"Fetching robots.txt from {robots_url}")
            
            # Fetch robots.txt
            response = requests.get(
                robots_url,
                timeout=self.request_timeout,
                headers={'User-Agent': self.user_agent}
            )
            
            # Create parser
            parser = RobotFileParser()
            parser.set_url(robots_url)
            
            if response.status_code == 200:
                # Parse the content
                parser.parse(response.text.splitlines())
                
                # Cache the parser
                self._cache[base_url] = (parser, datetime.now())
                
                self.logger.debug(f"Successfully parsed robots.txt for {base_url}")
                return parser
            elif response.status_code == 404:
                # No robots.txt means everything is allowed
                self.logger.debug(f"No robots.txt found for {base_url} (404), allowing all")
                
                # Create a permissive parser
                parser.parse([])  # Empty robots.txt allows everything
                self._cache[base_url] = (parser, datetime.now())
                return parser
            else:
                self.logger.warning(f"Unexpected status code {response.status_code} for {robots_url}")
                return None
                
        except requests.Timeout:
            self.logger.warning(f"Timeout fetching robots.txt from {robots_url}")
            return None
        except requests.RequestException as e:
            self.logger.warning(f"Request error fetching robots.txt from {robots_url}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing robots.txt for {base_url}: {str(e)}")
            return None
    
    def clear_cache(self) -> None:
        """Clear the robots.txt cache"""
        self._cache.clear()
        self.logger.info("Robots.txt cache cleared")
    
    def get_cache_size(self) -> int:
        """Get the number of cached robots.txt entries"""
        return len(self._cache)