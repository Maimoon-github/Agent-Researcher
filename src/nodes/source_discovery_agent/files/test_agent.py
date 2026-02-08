"""
Unit tests for Source Discovery Agent

Run with: pytest test_agent.py
"""

import pytest
import sys
import os

# Add project root to sys.path to allow absolute imports
# This file is in: src/nodes/source_discovery_agent/files/test_agent.py
# Root is at: ../../../..
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.nodes.source_discovery_agent import (
    SourceDiscoveryAgent,
    SourceDiscoveryConfig,
    QueryAnalyzer,
    SourceGenerator,
    CredibilityScorer,
    QueryValidationError,
    NoSourcesFoundError
)


class TestQueryAnalyzer:
    """Test cases for QueryAnalyzer"""
    
    def test_analyze_basic_query(self):
        """Test basic query analysis"""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("climate change impact")
        
        assert 'search_terms' in result
        assert 'query_type' in result
        assert 'intent' in result
        assert len(result['search_terms']) > 0
    
    def test_academic_query_detection(self):
        """Test detection of academic queries"""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("peer-reviewed research on quantum computing")
        
        assert result['domain_hints']['academic'] is True
        assert result['intent'] == 'literature_review'
    
    def test_news_query_detection(self):
        """Test detection of news queries"""
        analyzer = QueryAnalyzer()
        result = analyzer.analyze("latest news on renewable energy")
        
        assert result['domain_hints']['news'] is True
        assert result['intent'] == 'current_events'


class TestCredibilityScorer:
    """Test cases for CredibilityScorer"""
    
    def test_score_academic_domain(self):
        """Test scoring of academic domains"""
        scorer = CredibilityScorer()
        score = scorer.calculate_score("https://arxiv.org/abs/2301.00001")
        
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Academic domains should score high
    
    def test_score_government_domain(self):
        """Test scoring of government domains"""
        scorer = CredibilityScorer()
        score = scorer.calculate_score("https://nasa.gov/research/article")
        
        assert score > 0.8  # Government domains should score very high
    
    def test_score_breakdown(self):
        """Test credibility score breakdown"""
        scorer = CredibilityScorer()
        breakdown = scorer.get_score_breakdown("https://example.com")
        
        assert 'total_score' in breakdown
        assert 'components' in breakdown
        assert 'domain_authority' in breakdown['components']
        assert 'content_quality' in breakdown['components']
        assert 'external_validation' in breakdown['components']


class TestSourceDiscoveryAgent:
    """Test cases for SourceDiscoveryAgent"""
    
    def test_agent_initialization(self):
        """Test agent initialization with defaults"""
        agent = SourceDiscoveryAgent()
        
        assert agent.config is not None
        assert agent.query_analyzer is not None
        assert agent.source_generator is not None
    
    def test_agent_custom_config(self):
        """Test agent initialization with custom config"""
        config = SourceDiscoveryConfig(
            min_credibility_score=0.8,
            max_urls_per_domain=3
        )
        agent = SourceDiscoveryAgent(config=config)
        
        assert agent.config.min_credibility_score == 0.8
        assert agent.config.max_urls_per_domain == 3
    
    def test_discover_sources_basic(self):
        """Test basic source discovery"""
        agent = SourceDiscoveryAgent()
        
        # Note: This test might fail if network is unavailable
        # In production, use mocking for network calls
        result = agent.discover_sources(
            query="test query",
            max_sources_per_type=2
        )
        
        assert 'status' in result
        assert result['status'] in ['success', 'error']
    
    def test_query_validation_too_short(self):
        """Test that too-short queries are rejected"""
        agent = SourceDiscoveryAgent()
        result = agent.discover_sources(query="ab")
        
        assert result['status'] == 'error'
        assert result['error']['type'] == 'validation_error'
    
    def test_query_validation_too_long(self):
        """Test that too-long queries are rejected"""
        agent = SourceDiscoveryAgent()
        long_query = "a" * 1001
        result = agent.discover_sources(query=long_query)
        
        assert result['status'] == 'error'
        assert result['error']['type'] == 'validation_error'
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        agent = SourceDiscoveryAgent()
        
        # Process a query
        agent.discover_sources(query="test metrics", max_sources_per_type=2)
        
        # Get metrics
        metrics = agent.get_metrics()
        
        assert 'query_count' in metrics
        assert metrics['query_count'] > 0
    
    def test_metrics_reset(self):
        """Test metrics reset"""
        agent = SourceDiscoveryAgent()
        
        # Process a query
        agent.discover_sources(query="test reset", max_sources_per_type=2)
        
        # Reset metrics
        agent.reset_metrics()
        metrics = agent.get_metrics()
        
        assert metrics['query_count'] == 0


class TestSourceGenerator:
    """Test cases for SourceGenerator"""
    
    def test_generate_web_sources(self):
        """Test web source generation"""
        generator = SourceGenerator()
        
        query_analysis = {
            'search_terms': ['climate', 'change'],
            'intent': 'fact_finding',
            'authority_level': 'medium',
            'domain_hints': {}
        }
        
        sources = generator.generate_sources(
            query_analysis,
            ['web'],
            max_sources_per_type=5
        )
        
        assert len(sources) > 0
        assert all('url' in s for s in sources)
    
    def test_generate_academic_sources(self):
        """Test academic source generation"""
        generator = SourceGenerator()
        
        query_analysis = {
            'search_terms': ['quantum', 'computing'],
            'intent': 'literature_review',
            'authority_level': 'high',
            'domain_hints': {'academic': True}
        }
        
        sources = generator.generate_sources(
            query_analysis,
            ['academic'],
            max_sources_per_type=5
        )
        
        assert len(sources) > 0
        assert any('arxiv.org' in s['url'] or 'scholar.google.com' in s['url'] 
                   for s in sources)


class TestConfiguration:
    """Test cases for configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = SourceDiscoveryConfig()
        
        assert config.min_credibility_score == 0.7
        assert config.max_urls_per_domain == 5
        assert config.request_timeout_seconds == 10
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = SourceDiscoveryConfig(
            min_credibility_score=0.85,
            max_urls_per_domain=3,
            local_scan_directories=["/tmp"]
        )
        
        assert config.min_credibility_score == 0.85
        assert config.max_urls_per_domain == 3
        assert "/tmp" in config.local_scan_directories
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = SourceDiscoveryConfig(min_credibility_score=1.5)
        
        with pytest.raises(ValueError):
            config.validate()
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion"""
        config = SourceDiscoveryConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'min_credibility_score' in config_dict
        assert 'source_weights' in config_dict


# Integration test
class TestIntegration:
    """Integration tests for full workflow"""
    
    def test_full_workflow(self):
        """Test complete discovery workflow"""
        # Configure agent
        config = SourceDiscoveryConfig(
            min_credibility_score=0.6,  # Lower threshold for testing
            max_urls_per_domain=2
        )
        agent = SourceDiscoveryAgent(config=config)
        
        # Execute discovery
        result = agent.discover_sources(
            query="artificial intelligence",
            query_id="test_001",
            source_type_preferences=["web"],
            max_sources_per_type=3
        )
        
        # Verify result structure
        assert 'status' in result
        assert 'query_id' in result
        assert result['query_id'] == "test_001"
        
        if result['status'] == 'success':
            assert 'data' in result
            assert 'validated_urls' in result['data']
            assert 'discovery_metrics' in result['data']
            assert 'recommendations' in result['data']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
