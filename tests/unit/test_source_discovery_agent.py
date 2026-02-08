import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
# Try to add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.nodes.source_discovery_agent.agent import SourceDiscoveryAgent
    from src.nodes.source_discovery_agent.config import SourceDiscoveryConfig
    from src.nodes.source_discovery_agent.node import SourceDiscoveryNode
    from src.core.state import create_initial_state
except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback or exit
    
class TestSourceDiscoveryAgent(unittest.TestCase):
    
    def setUp(self):
        self.config = SourceDiscoveryConfig()
        self.agent = SourceDiscoveryAgent(self.config)

    def test_query_analysis(self):
        query = "What is the impact of climate change on biodiversity?"
        analysis = self.agent.query_analyzer.analyze(query)
        self.assertEqual(analysis["original_query"], query)
        # In current implementation, intent is a member of QueryIntent Enum
        self.assertTrue("climate" in analysis["search_terms"] or "impact" in analysis["search_terms"])
        # QueryIntent values are lowercased strings from the Enum
        self.assertIn(analysis["intent"], ["fact_finding", "literature_review", "current_events", "unknown"])

    def test_source_generation(self):
        analysis = {
            "original_query": "machine learning", 
            "search_terms": ["machine", "learning"],
            "intent": "literature_review",
            "authority_level": "high",
            "domain_hints": {"academic": True}
        }
        sources = self.agent.source_generator.generate_sources(analysis)
        # Expected types: 'academic', 'web', 'news', 'technical'
        found = any(s.get("source_type") == "academic" for s in sources)
        found_web = any(s.get("source_type") == "web" for s in sources)
        self.assertTrue(found or found_web)

    @patch('src.nodes.source_discovery_agent.validator.requests.head')
    def test_validation(self, mock_head):
        # Mock successful HEAD request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html', 'Content-Length': '1024'}
        mock_head.return_value = mock_response

        # In current implementation, validator, robots_parser, and scorer are separate in Agent
        self.agent.robots_parser.is_allowed = MagicMock(return_value=True)
        self.agent.credibility_scorer.calculate_score = MagicMock(return_value=0.8)
        
        # Test the internal _validate_sources method or just the components
        candidate = {"url": "https://example.com/article", "source_type": "web"}
        results = self.agent._validate_sources([candidate], 0.5)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["credibility_score"], 0.8)
        self.assertTrue(results[0]["robots_allowed"])

    def test_node_process(self):
        node = SourceDiscoveryNode()
        # Mock the internal agent discover_sources to return the actual structure
        node.agent.discover_sources = MagicMock(return_value={
            "status": "success",
            "data": {
                "validated_urls": [
                    {"url": "https://valid.com", "credibility_score": 0.9, "source_type": "web"}
                ],
                "local_file_patterns": [],
                "discovery_metrics": {"total_sources_considered": 1},
                "recommendations": {}
            },
            "timestamp": "2024-01-01T00:00:00Z"
        })
        
        state = create_initial_state("test query")
        new_state = node.process(state)
        
        self.assertEqual(len(new_state["sources"]), 1)
        self.assertEqual(new_state["sources"][0]["url"], "https://valid.com")

if __name__ == '__main__':
    unittest.main()
