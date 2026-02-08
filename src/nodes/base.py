"""
Base Node Interface for Agent Researcher

Abstract base class that all processing nodes must implement.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from loguru import logger

from ..core.state import AgentState, NodeResult, NodeStatus
from ..core.config import Config, get_config


class BaseNode(ABC):
    """
    Abstract base class for all processing nodes.
    
    Each node must implement:
    - process(): Main processing logic
    - validate_input(): Input validation
    - validate_output(): Output validation
    
    Provides:
    - Automatic timing and metrics
    - Error handling with retry logic
    - Logging integration
    - State update helpers
    """
    
    # Node configuration - override in subclasses
    node_name: str = "base_node"
    max_retries: int = 3
    timeout_seconds: int = 300
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.retry_count = 0
        self.last_error: Optional[str] = None
        
        logger.debug(f"Initialized node: {self.node_name}")
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """
        Main processing logic. Must be implemented by subclasses.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """
        Validate input state before processing.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default: no validation, override in subclasses
        return True, ""
    
    def validate_output(self, state: AgentState) -> tuple[bool, str]:
        """
        Validate output state after processing.
        
        Args:
            state: Updated workflow state
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default: no validation, override in subclasses
        return True, ""
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Execute the node with error handling and metrics.
        
        This is the main entry point called by the orchestrator.
        Do not override this method.
        """
        start_time = time.time()
        logger.info(f"[{self.node_name}] Starting execution")
        
        # Update state with current node
        state["current_node"] = self.node_name
        
        try:
            # Validate input
            is_valid, error_msg = self.validate_input(state)
            if not is_valid:
                return self._handle_error(state, f"Input validation failed: {error_msg}", start_time)
            
            # Execute with retries
            result_state = self._execute_with_retry(state)
            
            # Validate output
            is_valid, error_msg = self.validate_output(result_state)
            if not is_valid:
                return self._handle_error(result_state, f"Output validation failed: {error_msg}", start_time)
            
            # Record success
            duration_ms = int((time.time() - start_time) * 1000)
            node_result = NodeResult(
                node_name=self.node_name,
                status=NodeStatus.SUCCESS,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
            )
            result_state["node_results"].append(node_result.model_dump())
            
            logger.info(f"[{self.node_name}] Completed successfully in {duration_ms}ms")
            return result_state
            
        except Exception as e:
            return self._handle_error(state, str(e), start_time)
    
    def _execute_with_retry(self, state: AgentState) -> AgentState:
        """Execute with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.retry_count = attempt
                return self.process(state)
            except Exception as e:
                last_exception = e
                self.last_error = str(e)
                logger.warning(f"[{self.node_name}] Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    backoff = min(
                        self.config.error_handling.exponential_backoff_base ** attempt,
                        self.config.error_handling.max_backoff_seconds,
                    )
                    time.sleep(backoff)
        
        raise last_exception or Exception("Unknown error after retries")
    
    def _handle_error(self, state: AgentState, error_msg: str, start_time: float) -> AgentState:
        """Handle error and update state."""
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.error(f"[{self.node_name}] Error: {error_msg}")
        
        node_result = NodeResult(
            node_name=self.node_name,
            status=NodeStatus.FAILED,
            error=error_msg,
            duration_ms=duration_ms,
            retry_count=self.retry_count,
            timestamp=datetime.now(),
        )
        
        state["node_results"].append(node_result.model_dump())
        state["errors"].append(f"[{self.node_name}] {error_msg}")
        
        # Update error count in metrics
        if "metrics" in state:
            state["metrics"]["errors_count"] = state["metrics"].get("errors_count", 0) + 1
        
        return state
    
    def add_warning(self, state: AgentState, warning: str) -> None:
        """Add a warning to the state."""
        logger.warning(f"[{self.node_name}] {warning}")
        state["warnings"].append(f"[{self.node_name}] {warning}")
    
    def get_upstream_data(self, state: AgentState, key: str, default: Any = None) -> Any:
        """Safely get data from upstream nodes."""
        return state.get(key, default)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.node_name})>"
