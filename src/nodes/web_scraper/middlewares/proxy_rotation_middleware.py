"""
Proxy rotation management
"""
import logging
import time
import random
from typing import List, Dict, Optional
from collections import defaultdict


logger = logging.getLogger(__name__)


class ProxyRotationManager:
    """
    Manages proxy rotation with:
    - Health checking
    - Geographic distribution
    - Protocol support (HTTP/HTTPS/SOCKS)
    - Failure detection and blacklisting
    """
    
    def __init__(self, proxy_list: List[str] = None):
        """
        Initialize proxy rotation manager
        
        Args:
            proxy_list: List of proxy URLs (e.g., ['http://proxy1:8080', 'socks5://proxy2:1080'])
        """
        self.proxies = proxy_list or []
        self.health_scores: Dict[str, float] = {proxy: 1.0 for proxy in self.proxies}
        self.usage_count: Dict[str, int] = defaultdict(int)
        self.last_used: Dict[str, float] = {}
        self.failures: Dict[str, list] = defaultdict(list)
        self.blacklist: set = set()
        
        self.failure_threshold = 0.3  # Blacklist if >30% recent requests fail
        self.health_decay = 0.9  # Health decay factor per failure
        self.health_recovery = 0.05  # Health recovery per success
        
        logger.info(f"Proxy rotation manager initialized with {len(self.proxies)} proxies")
    
    def get_proxy(self, domain: Optional[str] = None) -> Optional[str]:
        """
        Get best proxy for given domain
        
        Args:
            domain: Domain name (optional, for domain-specific selection)
            
        Returns:
            Proxy URL or None if no healthy proxies available
        """
        if not self.proxies:
            return None
        
        # Get available (non-blacklisted) proxies
        available = self.get_healthy_proxies()
        if not available:
            logger.warning("No healthy proxies available")
            return None
        
        # Select proxy by strategy
        return self.select_by_strategy(available, domain)
    
    def get_healthy_proxies(self) -> List[str]:
        """Get list of healthy (non-blacklisted) proxies"""
        return [
            proxy for proxy in self.proxies
            if proxy not in self.blacklist and self.health_scores[proxy] > 0.2
        ]
    
    def select_by_strategy(self, available_proxies: List[str], domain: Optional[str] = None) -> str:
        """
        Select proxy using weighted random selection based on health scores
        
        Args:
            available_proxies: List of available proxy URLs
            domain: Domain name (optional)
            
        Returns:
            Selected proxy URL
        """
        # Prefer proxies not recently used for this domain
        if domain:
            domain_specific = [
                p for p in available_proxies
                if self.last_used.get(f"{domain}:{p}", 0) < time.time() - 60
            ]
            if domain_specific:
                available_proxies = domain_specific
        
        # Weight by health score
        weights = [self.health_scores[p] for p in available_proxies]
        total_weight = sum(weights)
        
        if total_weight == 0:
            # All proxies have 0 health, select randomly
            return random.choice(available_proxies)
        
        # Weighted random selection
        normalized_weights = [w / total_weight for w in weights]
        selected = random.choices(available_proxies, weights=normalized_weights, k=1)[0]
        
        # Update usage tracking
        self.usage_count[selected] += 1
        self.last_used[selected] = time.time()
        if domain:
            self.last_used[f"{domain}:{selected}"] = time.time()
        
        return selected
    
    def record_success(self, proxy: str):
        """
        Record successful request through proxy
        
        Args:
            proxy: Proxy URL
        """
        # Improve health score
        current_health = self.health_scores.get(proxy, 0.5)
        self.health_scores[proxy] = min(1.0, current_health + self.health_recovery)
        
        # Remove from blacklist if present
        if proxy in self.blacklist:
            self.blacklist.remove(proxy)
            logger.info(f"Proxy {proxy} removed from blacklist")
    
    def record_failure(self, proxy: str):
        """
        Record failed request through proxy
        
        Args:
            proxy: Proxy URL
        """
        # Record failure time
        self.failures[proxy].append(time.time())
        
        # Keep only recent failures (last hour)
        recent_failures = [
            f for f in self.failures[proxy]
            if time.time() - f < 3600
        ]
        self.failures[proxy] = recent_failures
        
        # Decrease health score
        current_health = self.health_scores.get(proxy, 1.0)
        self.health_scores[proxy] = max(0.0, current_health * self.health_decay)
        
        # Check if should be blacklisted
        total_requests = self.usage_count.get(proxy, 0)
        if total_requests > 10:  # Only blacklist after significant usage
            failure_rate = len(recent_failures) / total_requests
            if failure_rate > self.failure_threshold:
                self.blacklist.add(proxy)
                logger.warning(f"Proxy {proxy} blacklisted due to high failure rate: {failure_rate:.2%}")
    
    def add_proxy(self, proxy: str):
        """Add a new proxy to the pool"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.health_scores[proxy] = 1.0
            logger.info(f"Added proxy: {proxy}")
    
    def remove_proxy(self, proxy: str):
        """Remove a proxy from the pool"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.health_scores.pop(proxy, None)
            self.blacklist.discard(proxy)
            logger.info(f"Removed proxy: {proxy}")
    
    def clear_blacklist(self):
        """Clear the proxy blacklist"""
        self.blacklist.clear()
        logger.info("Proxy blacklist cleared")
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        return {
            'total_proxies': len(self.proxies),
            'healthy_proxies': len(self.get_healthy_proxies()),
            'blacklisted_proxies': len(self.blacklist),
            'proxy_health': dict(self.health_scores),
            'proxy_usage': dict(self.usage_count),
            'blacklist': list(self.blacklist)
        }