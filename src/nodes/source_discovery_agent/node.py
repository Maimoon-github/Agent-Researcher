"""
Node 1: Source Discovery Agent Node
Orchestrates the discovery of web and local sources for research queries.
"""

from typing import Dict, List, Optional, Tuple
from loguru import logger

from .agent import SourceDiscoveryAgent
from .config import SourceDiscoveryConfig
from ..base import BaseNode
from ...core.state import AgentState, Source, SourceType


class SourceDiscoveryNode(BaseNode):
    """
    Node wrapper for SourceDiscoveryAgent.
    
    This node:
    1. Analyzes the research query
    2. Generates potential sources (web, academic, news, etc.)
    3. Scans local directories for relevant documents
    4. Validates and scores all discovered sources
    5. Updates the global state with discovered sources
    """
    
    node_name = "source_discovery"
    
    def __init__(self, config=None):
        super().__init__(config)
        # Initialize the underlying agent
        # We can pass properties from our global config if needed
        agent_config = self._map_to_agent_config()
        self.agent = SourceDiscoveryAgent(config=agent_config)
        logger.debug(f"SourceDiscoveryNode initialized with agent: {self.agent}")

    def _map_to_agent_config(self) -> SourceDiscoveryConfig:
        """Map global app config to domain-specific agent config."""
        agent_config = SourceDiscoveryConfig()
        
        if hasattr(self.config, 'quality'):
            agent_config.min_credibility_score = self.config.quality.min_source_credibility
            agent_config.credibility_threshold = self.config.quality.min_source_credibility
            
        if hasattr(self.config, 'scraping'):
            agent_config.request_timeout_seconds = self.config.scraping.timeout
            agent_config.user_agent = self.config.scraping.user_agent
            
        return agent_config

    def validate_input(self, state: AgentState) -> Tuple[bool, str]:
        """Validate that we have a query to work with."""
        query = state.get("query")
        if not query:
            return False, "No query found in state"
        if len(query) < 3:
            return False, "Query is too short (min 3 chars)"
        return True, ""

    def process(self, state: AgentState) -> AgentState:
        """
        Execute the discovery process and update state.
        """
        query = state.get("query")
        logger.info(f"Discovering sources for: {query}")
        
        # Call the underlying agent
        result = self.agent.discover_sources(
            query=query,
            query_id=state.get("session_id"),
            max_sources_per_type=self.agent.config.max_sources_per_type
        )
        
        if result["status"] == "error":
            error_msg = result.get("error", {}).get("message", "Unknown discovery error")
            logger.error(f"Discovery failed: {error_msg}")
            # If it's a critical error (no sources), we might want to stop early
            if result.get("error", {}).get("type") == "no_sources_found":
                state["should_continue"] = False
                state["errors"].append(f"Discovery failed: {error_msg}")
            return state
        
        data = result.get("data", {})
        
        # Process validated web sources
        validated_urls = data.get("validated_urls", [])
        new_sources = []
        
        for source_data in validated_urls:
            source = {
                "url": source_data.get("url"),
                "source_type": source_data.get("source_type", SourceType.WEB.value),
                "credibility_score": source_data.get("credibility_score", 0.5),
                "robots_allowed": source_data.get("robots_allowed", True),
                "metadata": source_data.get("metadata", {}),
                "discovered_at": result.get("timestamp")
            }
            new_sources.append(source)
            
        # Process local file patterns
        local_files = data.get("local_file_patterns", [])
        for file_data in local_files:
            source = {
                "path": file_data.get("path"),
                "source_type": SourceType.LOCAL_FILE.value,
                "credibility_score": 1.0,  # Local files trusted by default
                "metadata": file_data.get("metadata", {}),
                "discovered_at": result.get("timestamp")
            }
            new_sources.append(source)
            
        # Update state
        state["sources"] = state.get("sources", []) + new_sources
        
        # Update metrics
        if "metrics" in state:
            metrics = state["metrics"]
            discovery_metrics = data.get("discovery_metrics", {})
            metrics["sources_discovered"] = metrics.get("sources_discovered", 0) + discovery_metrics.get("total_sources_considered", 0)
            
        logger.info(f"Discovered {len(new_sources)} total sources")
        
        return state

    def validate_output(self, state: AgentState) -> Tuple[bool, str]:
        """Validate that we have at least some sources if should_continue is True."""
        if state.get("should_continue", True) and not state.get("sources"):
            # This might not be a failure depending on the query, 
            # but usually we expect something.
            # We'll just warn for now.
            logger.warning("No sources discovered for the query")
            
        return True, ""
