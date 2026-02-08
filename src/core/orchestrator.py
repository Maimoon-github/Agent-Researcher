"""
Process Orchestrator - Root Node

LangGraph-based workflow orchestration for the Agent Researcher system.
"""

from typing import Any, Dict, Literal, Optional
from datetime import datetime

from loguru import logger
from langgraph.graph import StateGraph, END

from .state import AgentState, create_initial_state
from .config import Config, get_config
from .llm_manager import get_llm_manager
from ..nodes import (
    SourceDiscoveryNode,
    WebScraperNode,
    FileLoaderNode,
    DataValidatorNode,
    DataCleaningNode,
    LLMAnalysisNode,
    SemanticIndexingNode,
    ContentAssemblyNode,
    TemplateEngineNode,
    FormattingNode,
    QualityReviewNode,
    MetricsCollectorNode,
    ImprovementAnalyzerNode,
    KBUpdaterNode,
    LoggingNode,
)


class ProcessOrchestrator:
    """
    Main workflow orchestrator using LangGraph.
    
    Coordinates all 15 nodes through defined pipelines:
    1. Data Collection Pipeline
    2. Knowledge Processing Pipeline
    3. Document Generation Pipeline
    4. Feedback & Iteration Loop
    5. Monitoring Layer
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.config.ensure_directories()
        
        # Initialize nodes
        self._init_nodes()
        
        # Build workflow graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        
        logger.info("Process Orchestrator initialized")
    
    def _init_nodes(self):
        """Initialize all processing nodes."""
        self.nodes = {
            "source_discovery": SourceDiscoveryNode(self.config),
            "file_loader": FileLoaderNode(self.config),
            "web_scraper": WebScraperNode(self.config),
            "data_validator": DataValidatorNode(self.config),
            "data_cleaning": DataCleaningNode(self.config),
            "llm_analysis": LLMAnalysisNode(self.config),
            "semantic_indexing": SemanticIndexingNode(self.config),
            "content_assembly": ContentAssemblyNode(self.config),
            "template_engine": TemplateEngineNode(self.config),
            "formatting": FormattingNode(self.config),
            "quality_review": QualityReviewNode(self.config),
            "metrics_collector": MetricsCollectorNode(self.config),
            "improvement_analyzer": ImprovementAnalyzerNode(self.config),
            "kb_updater": KBUpdaterNode(self.config),
            "logging_node": LoggingNode(self.config),
        }
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create graph with state schema
        graph = StateGraph(AgentState)
        
        # Add node wrappers
        for name, node in self.nodes.items():
            graph.add_node(name, node.execute)
        
        # Set entry point
        graph.set_entry_point("source_discovery")
        
        # Data Collection Pipeline (Sequential with parallel scraping)
        graph.add_edge("source_discovery", "file_loader")
        graph.add_edge("file_loader", "web_scraper")
        graph.add_edge("web_scraper", "data_validator")
        
        # Knowledge Processing Pipeline
        graph.add_edge("data_validator", "data_cleaning")
        graph.add_edge("data_cleaning", "llm_analysis")
        graph.add_edge("llm_analysis", "semantic_indexing")
        
        # Document Generation Pipeline
        graph.add_edge("semantic_indexing", "content_assembly")
        graph.add_edge("content_assembly", "template_engine")
        graph.add_edge("template_engine", "formatting")
        graph.add_edge("formatting", "quality_review")
        
        # Quality Review - Conditional Edge
        graph.add_conditional_edges(
            "quality_review",
            self._quality_router,
            {
                "approved": "metrics_collector",
                "revision": "content_assembly",
            },
        )
        
        # Feedback Loop
        graph.add_edge("metrics_collector", "improvement_analyzer")
        graph.add_edge("improvement_analyzer", "kb_updater")
        graph.add_edge("kb_updater", "logging_node")
        
        # End
        graph.add_edge("logging_node", END)
        
        return graph
    
    def _quality_router(self, state: AgentState) -> Literal["approved", "revision"]:
        """Route based on quality review result."""
        if state.get("approved", False):
            return "approved"
        
        revision_count = state.get("revision_count", 0)
        max_revisions = self.config.quality.max_revision_attempts
        
        if revision_count >= max_revisions:
            logger.warning(f"Max revisions ({max_revisions}) reached, proceeding anyway")
            return "approved"
        
        return "revision"
    
    def run(
        self,
        query: str,
        output_format: str = "markdown",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the full research pipeline.
        
        Args:
            query: Research query to process
            output_format: Output format (markdown, pdf, docx, html)
            session_id: Optional session ID for tracking
            
        Returns:
            Final state with results
        """
        logger.info(f"Starting research pipeline for: {query[:100]}...")
        
        # Create initial state
        initial_state = create_initial_state(query, session_id)
        initial_state["output_format"] = output_format
        
        # Reset LLM manager for new session
        llm = get_llm_manager()
        llm.reset_to_primary()
        
        # Run the graph
        try:
            final_state = self.app.invoke(initial_state)
            
            logger.info(f"Pipeline completed. Output: {final_state.get('output_path', 'N/A')}")
            
            return {
                "success": True,
                "session_id": final_state.get("session_id"),
                "output_path": final_state.get("output_path"),
                "approved": final_state.get("approved", False),
                "quality_score": final_state.get("quality_review", {}).get("score", 0),
                "metrics": final_state.get("metrics", {}),
                "errors": final_state.get("errors", []),
                "improvements": final_state.get("improvements", []),
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": initial_state.get("session_id"),
            }
    
    def run_continuous(
        self,
        queries: list[str],
        output_format: str = "markdown",
        interval_seconds: int = 0,
    ):
        """
        Run pipeline continuously for multiple queries.
        
        Args:
            queries: List of research queries
            output_format: Output format
            interval_seconds: Delay between queries
        """
        import time
        
        results = []
        
        for i, query in enumerate(queries):
            logger.info(f"Processing query {i+1}/{len(queries)}")
            
            result = self.run(query, output_format)
            results.append(result)
            
            if interval_seconds > 0 and i < len(queries) - 1:
                logger.info(f"Waiting {interval_seconds}s before next query...")
                time.sleep(interval_seconds)
        
        return results
