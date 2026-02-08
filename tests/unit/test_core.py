"""
Unit tests for Core components
"""

import pytest
from src.core.config import Config
from src.core.state import create_initial_state

def test_config_loading():
    """Test that config loads with defaults."""
    config = Config()
    assert config.system.name == "Agent Researcher"
    assert config.llm.primary_model == "mistral:7b-instruct"

def test_initial_state_creation():
    """Test initial state generation."""
    state = create_initial_state("test query")
    assert state["query"] == "test query"
    assert state["current_node"] == "orchestrator"
    assert state["should_continue"] is True
    assert isinstance(state["metrics"], dict)
