"""
Alert Manager

Handles alerting for errors and anomalies.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from loguru import logger

from ..core.config import get_config


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """Represents an alert."""
    
    def __init__(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.title = title
        self.message = message
        self.severity = severity
        self.source = source
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.acknowledged = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
        }


class AlertManager:
    """
    Manages alerts and notifications.
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
        self.alerts: List[Alert] = []
        self.max_alerts = 1000
        
        self._initialized = True
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create and store a new alert."""
        alert = Alert(title, message, severity, source, metadata)
        
        # Store alert
        self.alerts.append(alert)
        
        # Trim old alerts if needed
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log the alert
        log_method = getattr(logger, severity.value, logger.warning)
        log_method(f"[ALERT] {title}: {message}")
        
        # Send notifications for critical alerts
        if severity == AlertSeverity.CRITICAL:
            self._send_notification(alert)
        
        return alert
    
    def _send_notification(self, alert: Alert):
        """Send notification for critical alerts."""
        # In a real implementation, this could send emails, Slack messages, etc.
        logger.critical(f"CRITICAL ALERT: {alert.title}")
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        source: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get filtered alerts."""
        filtered = self.alerts
        
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        
        if source:
            filtered = [a for a in filtered if a.source == source]
        
        if acknowledged is not None:
            filtered = [a for a in filtered if a.acknowledged == acknowledged]
        
        # Return most recent first
        return [a.to_dict() for a in reversed(filtered[-limit:])]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def clear_acknowledged(self):
        """Clear acknowledged alerts."""
        self.alerts = [a for a in self.alerts if not a.acknowledged]
    
    # Convenience methods for common alerts
    
    def alert_node_failure(self, node: str, error: str):
        """Alert for node failure."""
        self.create_alert(
            title=f"Node Failure: {node}",
            message=error,
            severity=AlertSeverity.ERROR,
            source=node,
        )
    
    def alert_model_exhausted(self, models: List[str]):
        """Alert when all models are exhausted."""
        self.create_alert(
            title="All LLM Models Exhausted",
            message=f"All fallback models failed: {models}",
            severity=AlertSeverity.CRITICAL,
            source="llm_manager",
        )
    
    def alert_low_quality(self, score: float, threshold: float):
        """Alert for low quality document."""
        self.create_alert(
            title="Low Quality Document",
            message=f"Quality score {score:.2f} below threshold {threshold:.2f}",
            severity=AlertSeverity.WARNING,
            source="quality_review",
        )
    
    def alert_high_error_rate(self, error_rate: float):
        """Alert for high error rate."""
        self.create_alert(
            title="High Error Rate",
            message=f"Error rate: {error_rate:.1%}",
            severity=AlertSeverity.WARNING,
            source="metrics_collector",
        )


def get_alert_manager() -> AlertManager:
    """Get the global alert manager."""
    return AlertManager()
