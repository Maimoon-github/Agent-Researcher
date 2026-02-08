"""
Node 13: Improvement Analyzer

Analyzes feedback to identify optimization opportunities.
"""

from typing import Any, Dict, List
from datetime import datetime

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState
from ..core.llm_manager import get_llm_manager


class ImprovementAnalyzerNode(BaseNode):
    """
    Analyzes metrics and feedback for improvements.
    
    Features:
    - Pattern detection in errors
    - Performance bottleneck identification
    - Optimization recommendations
    """
    
    node_name = "improvement_analyzer"
    max_retries = 1
    
    def process(self, state: AgentState) -> AgentState:
        """Analyze metrics and generate improvement recommendations."""
        metrics = state.get("metrics", {})
        
        logger.info("Analyzing for improvements")
        
        improvements = []
        
        # Analyze pipeline performance
        pipeline = metrics.get("pipeline", {})
        if pipeline.get("success_rate", 1) < 0.9:
            improvements.append({
                "type": "reliability",
                "issue": f"Low success rate: {pipeline.get('success_rate', 0):.1%}",
                "suggestion": "Review error logs and add more robust error handling",
                "priority": "high",
            })
        
        # Analyze node timings
        node_timings = metrics.get("node_timings", {})
        for node_name, timing in node_timings.items():
            if timing.get("avg_ms", 0) > 30000:  # 30 seconds
                improvements.append({
                    "type": "performance",
                    "issue": f"Slow node: {node_name} (avg {timing['avg_ms']}ms)",
                    "suggestion": f"Optimize {node_name} or add caching",
                    "priority": "medium",
                })
        
        # Analyze quality
        quality = metrics.get("quality", {})
        if quality.get("revision_count", 0) > 1:
            improvements.append({
                "type": "quality",
                "issue": f"Multiple revisions needed: {quality.get('revision_count')}",
                "suggestion": "Improve content assembly prompts or add pre-generation validation",
                "priority": "medium",
            })
        
        if quality.get("issues_count", 0) > 3:
            improvements.append({
                "type": "quality",
                "issue": f"Many quality issues: {quality.get('issues_count')}",
                "suggestion": "Review and address common quality issues",
                "priority": "high",
            })
        
        # Analyze data pipeline
        data = metrics.get("data", {})
        if data.get("validated_items", 0) < data.get("raw_items", 1) * 0.5:
            improvements.append({
                "type": "data_quality",
                "issue": "Many items failed validation",
                "suggestion": "Improve source selection or relax validation rules",
                "priority": "medium",
            })
        
        # Analyze LLM usage
        llm = metrics.get("llm", {})
        if llm.get("model_switches", 0) > 2:
            improvements.append({
                "type": "llm",
                "issue": f"Frequent model switches: {llm.get('model_switches')}",
                "suggestion": "Consider using smaller chunks or a model with larger context",
                "priority": "low",
            })
        
        # Check for common errors
        errors = metrics.get("errors", [])
        error_patterns = self._analyze_error_patterns(errors)
        improvements.extend(error_patterns)
        
        # Store improvements
        state["improvements"] = improvements
        
        logger.info(f"Generated {len(improvements)} improvement recommendations")
        
        return state
    
    def _analyze_error_patterns(self, errors: List[str]) -> List[Dict[str, Any]]:
        """Analyze error patterns for common issues."""
        patterns = []
        
        if not errors:
            return patterns
        
        # Count error types
        timeout_errors = sum(1 for e in errors if "timeout" in e.lower())
        validation_errors = sum(1 for e in errors if "validation" in e.lower())
        llm_errors = sum(1 for e in errors if "llm" in e.lower() or "model" in e.lower())
        
        if timeout_errors > 1:
            patterns.append({
                "type": "network",
                "issue": f"Frequent timeouts ({timeout_errors})",
                "suggestion": "Increase timeout settings or improve network handling",
                "priority": "high",
            })
        
        if validation_errors > 2:
            patterns.append({
                "type": "validation",
                "issue": f"Many validation failures ({validation_errors})",
                "suggestion": "Review validation rules or improve data quality upstream",
                "priority": "medium",
            })
        
        if llm_errors > 1:
            patterns.append({
                "type": "llm",
                "issue": f"LLM errors ({llm_errors})",
                "suggestion": "Check Ollama status or adjust prompts",
                "priority": "high",
            })
        
        return patterns
