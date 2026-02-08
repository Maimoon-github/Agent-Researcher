"""
User agent rotation middleware
"""
import logging
import random
from typing import List


logger = logging.getLogger(__name__)


class UserAgentMiddleware:
    """
    Rotates user agents for requests
    """
    
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    def __init__(self, user_agents: List[str] = None):
        """
        Initialize user agent middleware
        
        Args:
            user_agents: List of user agent strings (optional)
        """
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS
        logger.info(f"User agent middleware initialized with {len(self.user_agents)} user agents")
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def add_user_agent(self, user_agent: str):
        """Add a user agent to the pool"""
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
    
    def remove_user_agent(self, user_agent: str):
        """Remove a user agent from the pool"""
        if user_agent in self.user_agents:
            self.user_agents.remove(user_agent)