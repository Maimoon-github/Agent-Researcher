"""
Adaptive rate limiting middleware for Scrapy
"""
import logging
import time
from collections import defaultdict
from typing import Dict
from urllib.parse import urlparse
import random


logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """
    Dynamic rate limiting based on:
    1. Domain-specific constraints (robots.txt)
    2. Server response times and errors
    3. Historical success rates
    4. Concurrent capacity
    """
    
    def __init__(self, default_delay: float = 1.0):
        self.default_delay = default_delay
        self.domain_delays: Dict[str, float] = {}
        self.domain_last_request: Dict[str, float] = {}
        self.domain_errors: Dict[str, list] = defaultdict(list)
        self.domain_response_times: Dict[str, list] = defaultdict(list)
        
        self.concurrency_limits = {
            'default': 2,
            'high_traffic': 5,
            'low_traffic': 1
        }
        
        # Error rate thresholds
        self.error_rate_threshold = 0.1
        self.slow_response_threshold = 5000  # ms
        
    def get_base_delay(self, domain: str) -> float:
        """Get base delay for domain"""
        return self.domain_delays.get(domain, self.default_delay)
    
    def set_domain_delay(self, domain: str, delay: float):
        """Set specific delay for a domain"""
        self.domain_delays[domain] = delay
    
    def calculate_delay(self, domain: str) -> float:
        """
        Calculate optimal delay for next request to domain
        
        Args:
            domain: Domain name
            
        Returns:
            Delay in seconds
        """
        base_delay = self.get_base_delay(domain)
        
        # Calculate error rate
        errors = self.domain_errors.get(domain, [])
        recent_errors = [e for e in errors if time.time() - e < 300]  # Last 5 min
        error_rate = len(recent_errors) / max(10, len(errors)) if errors else 0
        
        # Calculate average response time
        response_times = self.domain_response_times.get(domain, [])
        avg_response_time = sum(response_times[-10:]) / len(response_times[-10:]) if response_times else 0
        
        # Adjust delay based on performance
        adjusted_delay = base_delay
        
        if error_rate > self.error_rate_threshold:
            # High error rate - increase delay
            adjusted_delay *= 1.5
            logger.info(f"Increasing delay for {domain} due to high error rate: {error_rate:.2%}")
        
        if avg_response_time > self.slow_response_threshold:
            # Slow server - increase delay
            adjusted_delay *= 2
            logger.info(f"Increasing delay for {domain} due to slow responses: {avg_response_time:.0f}ms")
        
        return adjusted_delay
    
    def wait_if_needed(self, domain: str):
        """
        Wait if necessary before making request to domain
        
        Args:
            domain: Domain name
        """
        delay = self.calculate_delay(domain)
        
        # Check last request time
        last_request = self.domain_last_request.get(domain, 0)
        time_since_last = time.time() - last_request
        
        if time_since_last < delay:
            wait_time = delay - time_since_last
            # Add small random jitter to avoid thundering herd
            wait_time += random.uniform(0, 0.1)
            logger.debug(f"Waiting {wait_time:.2f}s before requesting {domain}")
            time.sleep(wait_time)
        
        # Update last request time
        self.domain_last_request[domain] = time.time()
    
    def record_response(self, domain: str, response_time_ms: float, success: bool):
        """
        Record response metrics for adaptive rate limiting
        
        Args:
            domain: Domain name
            response_time_ms: Response time in milliseconds
            success: Whether request was successful
        """
        # Record response time
        self.domain_response_times[domain].append(response_time_ms)
        
        # Keep only recent response times (last 100)
        if len(self.domain_response_times[domain]) > 100:
            self.domain_response_times[domain] = self.domain_response_times[domain][-100:]
        
        # Record errors
        if not success:
            self.domain_errors[domain].append(time.time())
            
            # Keep only recent errors
            if len(self.domain_errors[domain]) > 100:
                self.domain_errors[domain] = self.domain_errors[domain][-100:]
    
    def get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc
    
    def increase_delay(self, domain: str, factor: float = 1.5):
        """Manually increase delay for a domain"""
        current_delay = self.get_base_delay(domain)
        new_delay = current_delay * factor
        self.set_domain_delay(domain, new_delay)
        logger.info(f"Increased delay for {domain} from {current_delay:.2f}s to {new_delay:.2f}s")
    
    def decrease_delay(self, domain: str, factor: float = 0.75):
        """Manually decrease delay for a domain"""
        current_delay = self.get_base_delay(domain)
        new_delay = max(0.5, current_delay * factor)  # Minimum 0.5s
        self.set_domain_delay(domain, new_delay)
        logger.info(f"Decreased delay for {domain} from {current_delay:.2f}s to {new_delay:.2f}s")
    
    def get_stats(self) -> Dict:
        """Get rate limiting statistics"""
        stats = {
            'domains_tracked': len(self.domain_delays),
            'domain_delays': dict(self.domain_delays),
            'domain_stats': {}
        }
        
        for domain in self.domain_delays.keys():
            errors = self.domain_errors.get(domain, [])
            response_times = self.domain_response_times.get(domain, [])
            
            stats['domain_stats'][domain] = {
                'current_delay': self.domain_delays[domain],
                'error_count': len(errors),
                'avg_response_time_ms': sum(response_times[-10:]) / len(response_times[-10:]) if response_times else 0,
                'requests_tracked': len(response_times)
            }
        
        return stats