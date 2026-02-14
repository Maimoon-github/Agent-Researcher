"""
Test Suite for Source Discovery Agent
======================================

Comprehensive unit and integration tests for the Source Discovery Agent.

Run tests with:
    python test_source_discovery_agent.py

Or with pytest:
    pytest test_source_discovery_agent.py -v
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from source_discovery_agent import (
    CredibilityRequirements,
    SourceMetadata,
    SourceDiscoveryInput,
    SourceDiscoveryOutput,
    RobotsTxtChecker,
    CredibilityScorer,
    RelevanceScorer,
    PageFetcher,
    SourceDiscoveryAgent,
    run_source_discovery,
)


class TestCredibilityRequirements(unittest.TestCase):
    """Test CredibilityRequirements Pydantic model"""
    
    def test_default_values(self):
        """Test that default values are set correctly"""
        req = CredibilityRequirements()
        self.assertEqual(req.min_domain_authority, 0.5)
        self.assertEqual(req.max_age_days, 365)
        self.assertTrue(req.require_https)
        self.assertEqual(req.min_relevance_score, 0.3)
    
    def test_custom_values(self):
        """Test custom values validation"""
        req = CredibilityRequirements(
            min_domain_authority=0.8,
            max_age_days=180,
            trusted_domains=['edu', 'gov'],
            require_https=False
        )
        self.assertEqual(req.min_domain_authority, 0.8)
        self.assertEqual(req.max_age_days, 180)
        self.assertFalse(req.require_https)
        self.assertEqual(req.trusted_domains, ['edu', 'gov'])
    
    def test_validation_bounds(self):
        """Test that validation enforces bounds"""
        with self.assertRaises(Exception):
            CredibilityRequirements(min_domain_authority=1.5)  # > 1.0
        
        with self.assertRaises(Exception):
            CredibilityRequirements(min_domain_authority=-0.1)  # < 0.0


class TestSourceMetadata(unittest.TestCase):
    """Test SourceMetadata Pydantic model"""
    
    def test_valid_metadata(self):
        """Test creating valid SourceMetadata"""
        metadata = SourceMetadata(
            url="https://example.com/article",
            title="Test Article",
            description="A test article",
            domain="example.com",
            domain_authority_score=0.75,
            content_type="article",
            relevance_score=0.85,
            validation_status=True,
            is_https=True
        )
        self.assertEqual(metadata.url, "https://example.com/article")
        self.assertTrue(metadata.validation_status)
        self.assertIsInstance(metadata.discovered_at, datetime)
    
    def test_url_validation(self):
        """Test URL validation"""
        with self.assertRaises(Exception):
            SourceMetadata(
                url="invalid-url",  # Missing http:// or https://
                domain="example.com",
                domain_authority_score=0.5,
                relevance_score=0.5,
                validation_status=False,
                is_https=False
            )


class TestSourceDiscoveryInput(unittest.TestCase):
    """Test SourceDiscoveryInput Pydantic model"""
    
    def test_valid_input(self):
        """Test creating valid input"""
        input_data = SourceDiscoveryInput(
            topic="machine learning",
            max_results=20
        )
        self.assertEqual(input_data.topic, "machine learning")
        self.assertEqual(input_data.max_results, 20)
        self.assertIsInstance(input_data.credibility_requirements, CredibilityRequirements)
    
    def test_topic_validation(self):
        """Test topic length validation"""
        with self.assertRaises(Exception):
            SourceDiscoveryInput(topic="ab")  # Too short (< 3 chars)
        
        with self.assertRaises(Exception):
            SourceDiscoveryInput(topic="x" * 501)  # Too long (> 500 chars)


class TestRobotsTxtChecker(unittest.TestCase):
    """Test RobotsTxtChecker utility class"""
    
    def setUp(self):
        self.checker = RobotsTxtChecker()
    
    def test_can_fetch_allowed_url(self):
        """Test checking an allowed URL"""
        # Most sites allow general crawling
        can_fetch, delay = self.checker.can_fetch("https://www.python.org/")
        self.assertTrue(can_fetch)
    
    def test_can_fetch_with_invalid_url(self):
        """Test graceful handling of invalid URLs"""
        can_fetch, delay = self.checker.can_fetch("not-a-url")
        # Should default to allowed on error
        self.assertTrue(can_fetch)
    
    def test_cache_functionality(self):
        """Test that robots.txt responses are cached"""
        url1 = "https://www.python.org/page1"
        url2 = "https://www.python.org/page2"
        
        # First fetch
        self.checker.can_fetch(url1)
        
        # Second fetch from same domain should use cache
        # We can verify by checking the cache dict
        domain = "https://www.python.org"
        self.assertIn(domain, self.checker.cache)


class TestCredibilityScorer(unittest.TestCase):
    """Test CredibilityScorer utility class"""
    
    def setUp(self):
        self.scorer = CredibilityScorer()
    
    def test_edu_domain_high_score(self):
        """Test that .edu domains get high scores"""
        score = self.scorer.compute_domain_authority("https://mit.edu/research")
        self.assertGreaterEqual(score, 0.85)
    
    def test_gov_domain_high_score(self):
        """Test that .gov domains get high scores"""
        score = self.scorer.compute_domain_authority("https://usa.gov/info")
        self.assertGreaterEqual(score, 0.90)
    
    def test_https_bonus(self):
        """Test that HTTPS URLs get a bonus"""
        score_https = self.scorer.compute_domain_authority("https://example.com")
        score_http = self.scorer.compute_domain_authority("http://example.com")
        self.assertGreater(score_https, score_http)
    
    def test_trusted_domain_match(self):
        """Test matching against trusted domains list"""
        score = self.scorer.compute_domain_authority("https://arxiv.org/paper")
        # arxiv.org is in TRUSTED_DOMAINS with score 0.95
        self.assertEqual(score, 0.95)
    
    def test_generic_domain(self):
        """Test scoring for generic domains"""
        score = self.scorer.compute_domain_authority("https://example.com/page")
        # Should get base score + HTTPS bonus
        self.assertGreater(score, 0.5)
        self.assertLess(score, 0.7)
    
    def test_error_handling(self):
        """Test error handling with invalid URL"""
        score = self.scorer.compute_domain_authority("invalid://url")
        # Should return low default score
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestRelevanceScorer(unittest.TestCase):
    """Test RelevanceScorer utility class"""
    
    def test_keyword_extraction(self):
        """Test keyword extraction from text"""
        text = "machine learning artificial intelligence neural networks deep learning"
        keywords = RelevanceScorer.extract_keywords(text, max_keywords=5)
        
        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 5)
        self.assertIn("machine", keywords)
        self.assertIn("learning", keywords)
    
    def test_high_relevance_match(self):
        """Test high relevance when topic matches content"""
        score, keywords = RelevanceScorer.compute_relevance(
            topic="machine learning algorithms",
            title="Introduction to Machine Learning Algorithms",
            description="A comprehensive guide to machine learning algorithms and techniques"
        )
        self.assertGreater(score, 0.6)
        self.assertIn("machine", keywords)
        self.assertIn("learning", keywords)
    
    def test_low_relevance_mismatch(self):
        """Test low relevance when topic doesn't match content"""
        score, keywords = RelevanceScorer.compute_relevance(
            topic="quantum physics",
            title="Cooking Recipes for Beginners",
            description="Learn how to cook delicious meals"
        )
        self.assertLess(score, 0.5)
    
    def test_empty_content(self):
        """Test handling of empty content"""
        score, keywords = RelevanceScorer.compute_relevance(
            topic="test topic",
            title=None,
            description=None
        )
        self.assertEqual(score, 0.0)
        self.assertEqual(keywords, [])
    
    def test_title_boost(self):
        """Test that matching in title gives a boost"""
        score_with_title, _ = RelevanceScorer.compute_relevance(
            topic="machine learning",
            title="Machine Learning Guide",
            description="A general guide"
        )
        
        score_without_title, _ = RelevanceScorer.compute_relevance(
            topic="machine learning",
            title="A General Guide",
            description="A general guide"
        )
        
        self.assertGreater(score_with_title, score_without_title)


class TestPageFetcher(unittest.TestCase):
    """Test PageFetcher utility class"""
    
    def setUp(self):
        self.fetcher = PageFetcher()
    
    @patch('source_discovery_agent.requests.Session.get')
    def test_successful_fetch(self, mock_get):
        """Test successful page fetch and metadata extraction"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            'Content-Type': 'text/html',
            'Last-Modified': 'Wed, 15 Jan 2024 10:30:00 GMT'
        }
        mock_response.text = """
        <html>
        <head>
            <title>Test Page Title</title>
            <meta name="description" content="Test page description">
        </head>
        <body><article>Content here</article></body>
        </html>
        """
        mock_get.return_value = mock_response
        
        metadata = self.fetcher.fetch_metadata("https://example.com/test")
        
        self.assertEqual(metadata['title'], "Test Page Title")
        self.assertEqual(metadata['description'], "Test page description")
        self.assertEqual(metadata['content_type'], 'article')
        self.assertIsNone(metadata['error'])
    
    @patch('source_discovery_agent.requests.Session.get')
    def test_pdf_detection(self, mock_get):
        """Test PDF content type detection"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_get.return_value = mock_response
        
        metadata = self.fetcher.fetch_metadata("https://example.com/paper.pdf")
        
        self.assertEqual(metadata['content_type'], 'pdf')
        self.assertEqual(metadata['title'], 'paper.pdf')
    
    @patch('source_discovery_agent.requests.Session.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors"""
        mock_get.side_effect = Exception("Network error")
        
        metadata = self.fetcher.fetch_metadata("https://example.com/test")
        
        self.assertIsNotNone(metadata['error'])
        self.assertIn("Network error", metadata['error'])
    
    @patch('source_discovery_agent.requests.Session.get')
    def test_retry_logic(self, mock_get):
        """Test retry logic on failures"""
        # Fail twice, succeed on third attempt
        mock_get.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            self._create_success_response()
        ]
        
        metadata = self.fetcher.fetch_metadata("https://example.com/test")
        
        # Should succeed after retries
        self.assertEqual(metadata['title'], "Success")
        self.assertEqual(mock_get.call_count, 3)
    
    def _create_success_response(self):
        """Helper to create a successful mock response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = "<html><head><title>Success</title></head></html>"
        return mock_response


class TestSourceDiscoveryAgent(unittest.TestCase):
    """Test SourceDiscoveryAgent main class"""
    
    def setUp(self):
        self.agent = SourceDiscoveryAgent()
    
    @patch('source_discovery_agent.google_search')
    def test_search_web(self, mock_search):
        """Test web search functionality"""
        mock_search.return_value = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        urls = self.agent.search_web("test topic", max_results=3)
        
        self.assertEqual(len(urls), 3)
        self.assertIn("https://example1.com", urls)
    
    @patch('source_discovery_agent.google_search')
    def test_search_web_error_handling(self, mock_search):
        """Test search error handling"""
        mock_search.side_effect = Exception("Search failed")
        
        urls = self.agent.search_web("test topic")
        
        # Should return empty list on error
        self.assertEqual(urls, [])
    
    @patch.object(RobotsTxtChecker, 'can_fetch')
    @patch.object(PageFetcher, 'fetch_metadata')
    def test_validate_source_success(self, mock_fetch, mock_robots):
        """Test successful source validation"""
        # Mock robots.txt check
        mock_robots.return_value = (True, None)
        
        # Mock metadata fetch
        mock_fetch.return_value = {
            'title': 'Test Article',
            'description': 'About machine learning',
            'last_modified': None,
            'content_type': 'article',
            'error': None
        }
        
        requirements = CredibilityRequirements(
            min_domain_authority=0.5,
            min_relevance_score=0.3
        )
        
        source = self.agent.validate_source(
            url="https://example.com/article",
            topic="machine learning",
            requirements=requirements
        )
        
        self.assertTrue(source.validation_status)
        self.assertEqual(source.title, 'Test Article')
        self.assertTrue(source.robots_allowed)
    
    @patch.object(RobotsTxtChecker, 'can_fetch')
    def test_validate_source_robots_disallowed(self, mock_robots):
        """Test validation when robots.txt disallows"""
        mock_robots.return_value = (False, None)
        
        requirements = CredibilityRequirements()
        
        source = self.agent.validate_source(
            url="https://example.com/blocked",
            topic="test",
            requirements=requirements
        )
        
        self.assertFalse(source.robots_allowed)
        self.assertFalse(source.validation_status)
        self.assertIn("robots.txt", source.error_message.lower())
    
    @patch.object(RobotsTxtChecker, 'can_fetch')
    @patch.object(PageFetcher, 'fetch_metadata')
    def test_validate_source_fails_requirements(self, mock_fetch, mock_robots):
        """Test validation failure due to requirements"""
        mock_robots.return_value = (True, None)
        mock_fetch.return_value = {
            'title': 'Unrelated Article',
            'description': 'About cooking',
            'last_modified': None,
            'content_type': 'article',
            'error': None
        }
        
        # Strict requirements
        requirements = CredibilityRequirements(
            min_domain_authority=0.9,  # Very high
            min_relevance_score=0.8,   # Very high
            require_https=True
        )
        
        source = self.agent.validate_source(
            url="https://example.com/article",
            topic="quantum physics",
            requirements=requirements
        )
        
        self.assertFalse(source.validation_status)
        self.assertIsNotNone(source.error_message)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""
    
    @patch('source_discovery_agent.google_search')
    @patch.object(RobotsTxtChecker, 'can_fetch')
    @patch.object(PageFetcher, 'fetch_metadata')
    def test_full_workflow(self, mock_fetch, mock_robots, mock_search):
        """Test complete end-to-end workflow"""
        # Mock search results
        mock_search.return_value = [
            "https://mit.edu/ml",
            "https://example.com/article"
        ]
        
        # Mock robots.txt (allow both)
        mock_robots.return_value = (True, None)
        
        # Mock page fetches
        def fetch_side_effect(url):
            if 'mit.edu' in url:
                return {
                    'title': 'Machine Learning Course',
                    'description': 'Learn machine learning fundamentals',
                    'last_modified': datetime.utcnow(),
                    'content_type': 'article',
                    'error': None
                }
            else:
                return {
                    'title': 'Generic Article',
                    'description': 'Some content',
                    'last_modified': datetime.utcnow(),
                    'content_type': 'article',
                    'error': None
                }
        
        mock_fetch.side_effect = fetch_side_effect
        
        # Create input
        input_data = SourceDiscoveryInput(
            topic="machine learning",
            max_results=2,
            credibility_requirements=CredibilityRequirements(
                min_domain_authority=0.7,
                min_relevance_score=0.4
            )
        )
        
        # Run agent
        output = run_source_discovery(input_data)
        
        # Assertions
        self.assertIsInstance(output, SourceDiscoveryOutput)
        self.assertEqual(output.total_discovered, 2)
        self.assertGreater(output.total_validated, 0)
        
        # Check that MIT source scored higher
        if output.sources:
            top_source = output.sources[0]
            self.assertIn('mit.edu', top_source.url.lower())
            self.assertTrue(top_source.validation_status)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def test_empty_topic(self):
        """Test handling of empty topic"""
        with self.assertRaises(Exception):
            SourceDiscoveryInput(topic="")
    
    def test_zero_max_results(self):
        """Test handling of zero max results"""
        with self.assertRaises(Exception):
            SourceDiscoveryInput(topic="test", max_results=0)
    
    @patch('source_discovery_agent.google_search')
    def test_no_search_results(self, mock_search):
        """Test handling when search returns no results"""
        mock_search.return_value = []
        
        input_data = SourceDiscoveryInput(
            topic="very specific obscure topic xyz123",
            max_results=10
        )
        
        output = run_source_discovery(input_data)
        
        self.assertEqual(output.total_discovered, 0)
        self.assertEqual(output.total_validated, 0)
        self.assertEqual(len(output.sources), 0)


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCredibilityRequirements))
    suite.addTests(loader.loadTestsFromTestCase(TestSourceMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestSourceDiscoveryInput))
    suite.addTests(loader.loadTestsFromTestCase(TestRobotsTxtChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestCredibilityScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestRelevanceScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestPageFetcher))
    suite.addTests(loader.loadTestsFromTestCase(TestSourceDiscoveryAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
