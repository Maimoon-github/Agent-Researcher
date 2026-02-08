"""
Node 12: Evaluation Metrics Collector

Gathers performance data from the pipeline.
"""

from typing import Any, Dict, List
from datetime import datetime
import statistics

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState


from ..core.llm_manager import get_llm_manager


class MetricsCollectorNode(BaseNode):
    """
    Collects and aggregates performance metrics.
    
    Features:
    - Node timing collection
    - Quality score tracking
    - Resource usage monitoring
    - Historical trend analysis
    """
    
    node_name = "metrics_collector"
    max_retries = 1
    
    def process(self, state: AgentState) -> AgentState:
        """Collect metrics from pipeline execution."""
        logger.info("Collecting pipeline metrics")
        
        node_results = state.get("node_results", [])
        quality_review = state.get("quality_review", {})
        
        # Calculate node timings
        node_timings = {}
        for result in node_results:
            node_name = result.get("node_name", "unknown")
            duration = result.get("duration_ms", 0)
            if node_name not in node_timings:
                node_timings[node_name] = []
            node_timings[node_name].append(duration)
        
        # Calculate statistics
        timing_stats = {}
        for node_name, timings in node_timings.items():
            timing_stats[node_name] = {
                "count": len(timings),
                "total_ms": sum(timings),
                "avg_ms": statistics.mean(timings) if timings else 0,
                "max_ms": max(timings) if timings else 0,
            }
        
        # Count successes and failures
        successes = sum(1 for r in node_results if r.get("status") == "success")
        failures = sum(1 for r in node_results if r.get("status") == "failed")
        
        # Calculate total pipeline time
        total_time_ms = sum(s["total_ms"] for s in timing_stats.values())
        
        # Get LLM stats
        llm_manager = get_llm_manager()
        llm_stats = llm_manager.get_stats()
        
        # Build metrics object
        metrics = {
            "session_id": state.get("session_id"),
            "collected_at": datetime.now().isoformat(),
            "pipeline": {
                "total_time_ms": total_time_ms,
                "nodes_executed": len(node_results),
                "successes": successes,
                "failures": failures,
                "success_rate": successes / max(len(node_results), 1),
            },
            "node_timings": timing_stats,
            "quality": {
                "score": quality_review.get("score", 0),
                "approved": quality_review.get("approved", False),
                "revision_count": state.get("revision_count", 0),
                "issues_count": len(quality_review.get("issues", [])),
            },
            "data": {
                "sources_discovered": len(state.get("sources", [])),
                "raw_items": len(state.get("raw_data", [])),
                "validated_items": len(state.get("validated_data", [])),
                "chunks_created": len(state.get("cleaned_chunks", [])),
                "knowledge_extracted": len(state.get("extracted_knowledge", [])),
                "indexed_count": state.get("indexed_count", 0),
            },
            "llm": {
                "current_model": llm_stats.get("current_model", ""),
                "model_switches": llm_stats.get("model_switches", 0),
                "total_calls": llm_stats.get("total_calls", 0),
                "total_tokens": llm_stats.get("total_tokens_used", 0),
                "session_tokens": llm_stats.get("session_tokens", 0),
            },
            "output": {
                "format": state.get("output_format", ""),
                "path": state.get("output_path", ""),
            },
            "errors": state.get("errors", []),
            "warnings": state.get("warnings", []),
        }
        
        # Update state metrics
        state["metrics"] = metrics
        state["model_switch_count"] = llm_stats.get("model_switches", 0) # Sync state
        state["current_model"] = llm_stats.get("current_model", "")      # Sync state
        
        logger.info(f"Metrics collected: {successes}/{len(node_results)} nodes succeeded")
        
        return state
