"""
Integration Tests for Pipelines

Tests end-to-end execution of pipelines with mocked external dependencies.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
from src.core.orchestrator import ProcessOrchestrator
from src.core.state import create_initial_state

@pytest.fixture
def mock_llm_manager():
    with patch("src.core.llm_manager.get_llm_manager") as mock:
        manager = MagicMock()
        
        # Configure generate to return success
        response = MagicMock()
        response.success = True
        
        # Valid JSON for Source Discovery AND Analysis
        # SourceDiscovery expects: "search_terms": [], "urls": []
        # LLMAnalysis expects: "summary": "", "entities": [], "facts": []
        response.content = '{"search_terms": ["term1"], "urls": ["http://mock-source.com"], "summary": "Test Summary", "entities": ["Test Entity"], "facts": ["Fact"], "relevance_score": 0.9, "tags": ["tag"], "accuracy_score": 0.8, "completeness_score": 0.8, "clarity_score": 0.8, "issues": [], "suggestions": []}'
        
        manager.generate.return_value = response
        manager.get_embeddings.return_value = [0.1] * 768
        
        mock.return_value = manager
        yield manager

def test_data_collection_pipeline(mock_llm_manager):
    """Test the data collection pipeline end-to-end."""
    orchestrator = ProcessOrchestrator()
    state = create_initial_state("test query")
    
    # Run Source Discovery -> File Loader -> Web Scraper -> Data Validator
    # We can invoke individual nodes directly or simulate partial run
    
    # Simulate Source Discovery finding a URL
    state["sources"] = [{"url": "http://example.com", "source_type": "web"}]
    
    # Process with Web Scraper
    scraper = orchestrator.nodes["web_scraper"]
    
    # Mock httpx for scraper
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value.status_code = 200
        mock_client.return_value.__enter__.return_value.get.return_value.text = "<html><body>Test Content</body></html>"
        
        result = scraper.process(state)
        assert len(result["raw_data"]) > 0
        assert "Test Content" in result["raw_data"][0]["content"]

def test_full_pipeline_mocked(mock_llm_manager):
    """Test full pipeline execution with mocked LLM and VectorStore."""
    orchestrator = ProcessOrchestrator()
    
    # Mock WebScraper
    # Mock chromadb module using patch.dict since it's imported inside a function
    mock_chromadb_module = MagicMock()
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_chromadb_module.PersistentClient.return_value = mock_client
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {"ids": [["1"]], "documents": [["doc"]], "metadatas": [[{}]], "distances": [[0.1]]}

    with patch("src.nodes.web_scraper.WebScraperNode._scrape_url") as mock_scrape, \
         patch.dict("sys.modules", {"chromadb": mock_chromadb_module, "chromadb.config": MagicMock()}):
        
        # Configure WebScraper mock
        mock_scrape.return_value = {
            "id": "1", "source_id": "s1", "content": "Test content regarding query", 
            "content_type": "text/html", "url": "http://test.com"
        }
        
        result = orchestrator.run("Test Query")
        
        # Print errors if failed
        if not result["success"]:
            print(f"Pipeline failed with error: {result.get('error')}")
            print(f"Errors: {result.get('errors')}")
        
        assert result["success"] is True
        assert result["approved"] is True  # Assuming quality review passes with mock
        assert "metrics" in result
        assert result["metrics"]["pipeline"]["successes"] > 0
