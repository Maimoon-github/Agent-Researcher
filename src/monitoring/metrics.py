"""
Prometheus Metrics Registry

Provides metrics collection and export for monitoring.
"""

from typing import Optional

from loguru import logger

from ..core.config import get_config


class MetricsRegistry:
    """
    Prometheus metrics registry for Agent Researcher.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = get_config()
        self._metrics = {}
        
        if self.config.monitoring.metrics_enabled:
            self._init_prometheus()
        
        self._initialized = True
    
    def _init_prometheus(self):
        """Initialize Prometheus metrics."""
        try:
            from prometheus_client import Counter, Gauge, Histogram, start_http_server
            
            # Counters
            self._metrics["documents_generated"] = Counter(
                "agent_documents_generated_total",
                "Total documents generated",
            )
            
            self._metrics["llm_calls"] = Counter(
                "agent_llm_calls_total",
                "Total LLM API calls",
                ["model"],
            )
            
            self._metrics["errors"] = Counter(
                "agent_errors_total",
                "Total errors",
                ["node"],
            )
            
            # Gauges
            self._metrics["active_sessions"] = Gauge(
                "agent_active_sessions",
                "Currently active sessions",
            )
            
            self._metrics["knowledge_items"] = Gauge(
                "agent_knowledge_items",
                "Total items in knowledge base",
            )
            
            # Histograms
            self._metrics["pipeline_duration"] = Histogram(
                "agent_pipeline_duration_seconds",
                "Pipeline execution duration",
                buckets=[1, 5, 10, 30, 60, 120, 300],
            )
            
            self._metrics["node_duration"] = Histogram(
                "agent_node_duration_seconds",
                "Node execution duration",
                ["node"],
                buckets=[0.1, 0.5, 1, 5, 10, 30],
            )
            
            self._metrics["quality_score"] = Histogram(
                "agent_quality_score",
                "Document quality scores",
                buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            )
            
            # Start HTTP server for Prometheus scraping
            port = self.config.monitoring.prometheus_port
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
            
        except ImportError:
            logger.warning("prometheus_client not installed, metrics disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus: {e}")
    
    def inc_documents_generated(self):
        """Increment documents generated counter."""
        if "documents_generated" in self._metrics:
            self._metrics["documents_generated"].inc()
    
    def inc_llm_calls(self, model: str):
        """Increment LLM calls counter."""
        if "llm_calls" in self._metrics:
            self._metrics["llm_calls"].labels(model=model).inc()
    
    def inc_errors(self, node: str):
        """Increment errors counter."""
        if "errors" in self._metrics:
            self._metrics["errors"].labels(node=node).inc()
    
    def set_active_sessions(self, count: int):
        """Set active sessions gauge."""
        if "active_sessions" in self._metrics:
            self._metrics["active_sessions"].set(count)
    
    def set_knowledge_items(self, count: int):
        """Set knowledge items gauge."""
        if "knowledge_items" in self._metrics:
            self._metrics["knowledge_items"].set(count)
    
    def observe_pipeline_duration(self, seconds: float):
        """Observe pipeline duration."""
        if "pipeline_duration" in self._metrics:
            self._metrics["pipeline_duration"].observe(seconds)
    
    def observe_node_duration(self, node: str, seconds: float):
        """Observe node duration."""
        if "node_duration" in self._metrics:
            self._metrics["node_duration"].labels(node=node).observe(seconds)
    
    def observe_quality_score(self, score: float):
        """Observe quality score."""
        if "quality_score" in self._metrics:
            self._metrics["quality_score"].observe(score)


def get_metrics() -> MetricsRegistry:
    """Get the global metrics registry."""
    return MetricsRegistry()
