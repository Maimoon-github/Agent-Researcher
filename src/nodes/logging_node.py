"""
Node 15: Logging Node

Centralized logging for all pipeline activities.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState


class LoggingNode(BaseNode):
    """
    Centralized logging node.
    
    Features:
    - Structured logging
    - Log rotation
    - Session log export
    """
    
    node_name = "logging_node"
    max_retries = 1
    
    _configured = False
    
    @classmethod
    def configure_logging(cls, config):
        """Configure global logging settings."""
        if cls._configured:
            return
        
        # Remove default handler
        logger.remove()
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=config.system.log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        )
        
        # Add file handler
        log_path = Path(config.monitoring.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_path),
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=config.monitoring.log_rotation,
            retention="7 days",
            compression="gz",
        )
        
        cls._configured = True
        logger.info("Logging configured")
    
    def __init__(self, config=None):
        super().__init__(config)
        self.configure_logging(self.config)
    
    def process(self, state: AgentState) -> AgentState:
        """Log session summary and export logs."""
        session_id = state.get("session_id", "unknown")
        
        logger.info(f"Finalizing logs for session: {session_id}")
        
        # Create session log summary
        summary = self._create_session_summary(state)
        
        # Export session log
        self._export_session_log(session_id, summary, state)
        
        return state
    
    def _create_session_summary(self, state: AgentState) -> Dict[str, Any]:
        """Create session summary for logging."""
        metrics = state.get("metrics", {})
        
        return {
            "session_id": state.get("session_id"),
            "query": state.get("query", "")[:200],
            "started_at": state.get("started_at"),
            "completed_at": datetime.now().isoformat(),
            "outcome": {
                "approved": state.get("approved", False),
                "output_path": state.get("output_path", ""),
                "quality_score": state.get("quality_review", {}).get("score", 0),
            },
            "pipeline": metrics.get("pipeline", {}),
            "data": metrics.get("data", {}),
            "llm": metrics.get("llm", {}),
            "errors_count": len(state.get("errors", [])),
            "warnings_count": len(state.get("warnings", [])),
        }
    
    def _export_session_log(self, session_id: str, summary: Dict, state: AgentState):
        """Export detailed session log to file."""
        try:
            log_dir = Path(self.config.monitoring.log_file).parent / "sessions"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{session_id}.json"
            
            full_log = {
                "summary": summary,
                "node_results": state.get("node_results", []),
                "errors": state.get("errors", []),
                "warnings": state.get("warnings", []),
                "improvements": state.get("improvements", []),
            }
            
            log_file.write_text(json.dumps(full_log, indent=2, default=str))
            logger.info(f"Session log exported: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to export session log: {e}")
