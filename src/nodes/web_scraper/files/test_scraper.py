"""
Basic tests for Web Scraper Engine
"""
import pytest
from src.nodes.web_scraper import WebScraperEngine
from src.nodes.web_scraper.utils import URLNormalizer, ContentCleaner, RobotsParser
from src.nodes.web_scraper.middlewares import AdaptiveRateLimiter, UserAgentMiddleware


class TestURLNormalizer:
    """Test URL normalization"""
    
    def test_normalize_url(self):
        normalizer = URLNormalizer()
        
        # Test basic normalization
        url = "HTTP://Example.COM/path"
        normalized = normalizer.normalize(url)
        assert normalized == "http://example.com/path"
    
    def test_remove_tracking_params(self):
        normalizer = URLNormalizer(remove_tracking=True)
        
        url = "https://example.com/page?utm_source=google&id=123"
        normalized = normalizer.normalize(url)
        assert "utm_source" not in normalized
        assert "id=123" in normalized
    
    def test_get_domain(self):
        normalizer = URLNormalizer()
        
        url = "https://www.example.com/path"
        domain = normalizer.get_domain(url)
        assert domain == "www.example.com"


class TestContentCleaner:
    """Test content cleaning"""
    
    def test_clean_text(self):
        cleaner = ContentCleaner()
        
        text = "  Multiple   spaces\n\n\nand newlines  "
        cleaned = cleaner.clean_text(text)
        assert "Multiple spaces" in cleaned
        assert "  " not in cleaned
    
    def test_html_to_text(self):
        cleaner = ContentCleaner()
        
        html = "<p>Hello <b>world</b>!</p><script>alert('evil')</script>"
        text = cleaner.html_to_text(html)
        assert "Hello world!" in text
        assert "alert" not in text


class TestAdaptiveRateLimiter:
    """Test rate limiter"""
    
    def test_get_base_delay(self):
        limiter = AdaptiveRateLimiter(default_delay=1.0)
        
        delay = limiter.get_base_delay("example.com")
        assert delay == 1.0
    
    def test_set_domain_delay(self):
        limiter = AdaptiveRateLimiter()
        
        limiter.set_domain_delay("example.com", 2.0)
        assert limiter.get_base_delay("example.com") == 2.0
    
    def test_record_response(self):
        limiter = AdaptiveRateLimiter()
        
        limiter.record_response("example.com", 1000, True)
        assert "example.com" in limiter.domain_response_times
        assert len(limiter.domain_response_times["example.com"]) == 1


class TestUserAgentMiddleware:
    """Test user agent middleware"""
    
    def test_get_random_user_agent(self):
        middleware = UserAgentMiddleware()
        
        ua = middleware.get_random_user_agent()
        assert isinstance(ua, str)
        assert len(ua) > 0
    
    def test_add_user_agent(self):
        middleware = UserAgentMiddleware()
        
        custom_ua = "CustomBot/1.0"
        middleware.add_user_agent(custom_ua)
        assert custom_ua in middleware.user_agents


class TestWebScraperEngine:
    """Test main engine"""
    
    def test_initialization(self):
        scraper = WebScraperEngine()
        assert scraper is not None
        assert scraper.stats['total_requests'] == 0
    
    def test_custom_config(self):
        config = {
            'default_delay_seconds': 2.0,
            'enable_caching': False
        }
        scraper = WebScraperEngine(config=config)
        assert scraper.config['default_delay_seconds'] == 2.0
        assert scraper.cache_middleware is None
    
    def test_get_metrics(self):
        scraper = WebScraperEngine()
        metrics = scraper.get_metrics()
        
        assert 'stats' in metrics
        assert 'rate_limiter' in metrics
        assert 'cache' in metrics


def test_integration_basic():
    """Basic integration test"""
    scraper = WebScraperEngine()
    
    # Test with a simple URL (this would normally make a real request)
    # For testing, we'd use mocks or fixtures
    url_batch = [
        {
            "url": "https://example.com",
            "domain": "example.com",
            "credibility_score": 0.9,
            "robots_allowed": True,
            "source_type": "web",
            "validation_timestamp": "2024-01-15T10:00:00Z",
            "metadata": {}
        }
    ]
    
    # In a real test, we'd mock the HTTP requests
    # For now, just ensure the engine can be initialized and configured
    assert scraper is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])