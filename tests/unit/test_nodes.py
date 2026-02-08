"""
Unit tests for Nodes
"""

import pytest
from unittest.mock import MagicMock, patch
from src.nodes.base import BaseNode
from src.nodes.data_validator import DataValidatorNode
from src.nodes.data_cleaning import DataCleaningNode
from src.core.state import create_initial_state

class TestBaseNode:
    def test_base_node_execution(self):
        """Test the execute wrapper of BaseNode."""
        class MockNode(BaseNode):
            node_name = "mock_node"
            def process(self, state):
                state["processed"] = True
                return state

        node = MockNode()
        state = create_initial_state("test")
        result = node.execute(state)
        
        assert result["processed"] is True
        assert result["current_node"] == "mock_node"
        assert len(result["node_results"]) == 1
        assert result["node_results"][0]["status"] == "success"

class TestDataValidator:
    def test_validation_logic(self):
        node = DataValidatorNode()
        state = create_initial_state("test")
        
        # Test empty data
        state["raw_data"] = []
        is_valid, _ = node.validate_input(state)
        # Based on implementation, validate_input checks: if not raw_data: return False
        assert is_valid is False
        
        # Test with data - use realistic text to pass quality checks
        realistic_text = "Software architecture refers to the fundamental structures of a software system and the discipline of creating such structures and systems. Each structure comprises software elements, relations among them, and properties of both elements and relations."
        state["raw_data"] = [{"id": "1", "source_id": "s1", "content": realistic_text}] 
        result = node.process(state)
        
        # Check if validation passed
        if not result["validated_data"]:
            pytest.fail(f"Validation failed. Warnings: {result.get('warnings', [])}")
            
        assert len(result["validated_data"]) == 1
        assert "Software architecture" in result["validated_data"][0]["content"]

class TestDataCleaning:
    def test_cleaning_logic(self):
        node = DataCleaningNode()
        state = create_initial_state("test")
        
        # Use longer text to ensure chunking happens if there's a min size
        raw_text = "Dirty   Text. This  is a sentence.\n\nStart of a new paragraph with   more   spaces. " * 10
        state["validated_data"] = [{"id": "1", "source_id": "s1", "content": raw_text}]
        
        result = node.process(state)
        cleaned_chunks = result["cleaned_chunks"]
        
        assert len(cleaned_chunks) > 0
        
        combined_content = "".join([c["content"] for c in cleaned_chunks])
        # "Dirty   Text" -> "Dirty Text"
        assert "Dirty Text" in combined_content
